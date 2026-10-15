"""macOS code-signing, notarisation and stapling for Datashuttle.

This module is a no-op unless the following environment variables are set,
so local builds remain unsigned and only CI (or maintainers with the
credentials configured locally) actually signs:

Signing (required to sign the .app):
    MACOS_SIGNING_IDENTITY      e.g. "Developer ID Application: Your Name (TEAMID)"

Notarisation (required to notarise + staple the .dmg):
    APPLE_ID                    Apple ID email
    APPLE_TEAM_ID               10-character team ID
    APPLE_APP_SPECIFIC_PASSWORD App-specific password generated at appleid.apple.com

If only the signing identity is set, the .app will be signed but the .dmg
will not be notarised (useful when iterating on signing locally).

Apple's notarisation service must be able to verify every signed Mach-O
binary inside the bundle, so we walk it inside-out: deepest binaries first,
the outer .app last. We deliberately avoid ``codesign --deep`` because it
overwrites nested signatures (including WezTerm's, which we want to keep).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path
import os
import subprocess


def _identity() -> str | None:
    return os.environ.get("MACOS_SIGNING_IDENTITY")


def _notary_creds() -> tuple[str, str, str] | None:
    apple_id = os.environ.get("APPLE_ID")
    team_id = os.environ.get("APPLE_TEAM_ID")
    password = os.environ.get("APPLE_APP_SPECIFIC_PASSWORD")
    if apple_id and team_id and password:
        return apple_id, team_id, password
    return None


def _is_macho(path: Path) -> bool:
    """Return True if *path* is a Mach-O binary (executable, dylib, bundle).

    Uses ``file -b`` rather than parsing magic bytes ourselves so we get the
    same answer for fat binaries, x86_64, arm64, and dylib variants.
    """
    if not path.is_file() or path.is_symlink():
        return False
    try:
        out = subprocess.check_output(["file", "-b", str(path)], text=True)
    except subprocess.CalledProcessError:
        return False
    return "Mach-O" in out


def _codesign(target: Path, entitlements: Path, identity: str) -> None:
    """Sign *target* with the hardened runtime and a secure timestamp.

    ``--options runtime`` and ``--timestamp`` are both required for
    notarisation; forgetting either yields cryptic rejection logs from
    Apple's service.
    """
    subprocess.run(
        [
            "codesign",
            "--force",
            "--sign",
            identity,
            "--options",
            "runtime",
            "--entitlements",
            str(entitlements),
            "--timestamp",
            str(target),
        ],
        check=True,
    )


def sign_app_bundle(app_path: Path, entitlements: Path) -> None:
    """Walk *app_path* inside-out and sign every Mach-O binary plus the bundle.

    Skips ``_vendored/WezTerm-macos-*`` — WezTerm ships a valid signature
    that we want to preserve. Apple's notarisation service is happy as long
    as the enclosing bundle is signed + hardened, even if nested third-party
    bundles use a different team ID.
    """
    identity = _identity()
    if identity is None:
        print("[sign_macos] MACOS_SIGNING_IDENTITY not set; skipping signing.")
        return

    if not entitlements.is_file():
        raise FileNotFoundError(f"Entitlements file not found: {entitlements}")
    if not app_path.is_dir():
        raise FileNotFoundError(f"App bundle not found: {app_path}")

    print(f"[sign_macos] Signing {app_path} with identity {identity!r}")

    resources = app_path / "Contents" / "Resources"
    wezterm_skip = resources / "_vendored"

    # 1. Sign every inner Mach-O (rclone, .dylibs, .so, the datashuttle
    #    executable) — anything under Contents/ except WezTerm's bundle.
    inner_binaries: list[Path] = []
    for path in app_path.rglob("*"):
        # Skip everything under the vendored WezTerm tree.
        try:
            path.relative_to(wezterm_skip)
            continue
        except ValueError:
            pass
        if _is_macho(path):
            inner_binaries.append(path)

    # Deepest paths first so children are signed before parents.
    inner_binaries.sort(key=lambda p: len(p.parts), reverse=True)
    for binary in inner_binaries:
        _codesign(binary, entitlements, identity)

    # 2. Sign the outer .app bundle last.
    _codesign(app_path, entitlements, identity)

    # 3. Verify.
    subprocess.run(
        ["codesign", "--verify", "--strict", "--verbose=2", str(app_path)],
        check=True,
    )
    print(
        f"[sign_macos] Signed {len(inner_binaries)} inner binaries + outer bundle."
    )


def notarise_and_staple(dmg_path: Path) -> None:
    """Submit *dmg_path* to Apple's notary service and staple the ticket.

    Stapling embeds the notarisation ticket in the DMG so Gatekeeper can
    verify offline; without it, first launch on a machine with no network
    will fail.
    """
    creds = _notary_creds()
    if creds is None:
        print(
            "[sign_macos] Notary credentials not set "
            "(APPLE_ID / APPLE_TEAM_ID / APPLE_APP_SPECIFIC_PASSWORD); "
            "skipping notarisation."
        )
        return

    apple_id, team_id, password = creds
    if not dmg_path.is_file():
        raise FileNotFoundError(f"DMG not found: {dmg_path}")

    print(
        f"[sign_macos] Submitting {dmg_path.name} to notarytool (this may take a few minutes)..."
    )
    subprocess.run(
        [
            "xcrun",
            "notarytool",
            "submit",
            str(dmg_path),
            "--apple-id",
            apple_id,
            "--team-id",
            team_id,
            "--password",
            password,
            "--wait",
        ],
        check=True,
    )

    print(f"[sign_macos] Stapling notarisation ticket to {dmg_path.name}")
    subprocess.run(["xcrun", "stapler", "staple", str(dmg_path)], check=True)
    subprocess.run(["xcrun", "stapler", "validate", str(dmg_path)], check=True)

    # Final Gatekeeper assessment — for visibility in the build log.
    subprocess.run(
        [
            "spctl",
            "--assess",
            "--type",
            "open",
            "--context",
            "context:primary-signature",
            "--verbose=2",
            str(dmg_path),
        ],
        check=False,  # informational; non-zero just means the user-visible message differs
    )
    print(f"[sign_macos] {dmg_path.name} is signed, notarised and stapled.")
