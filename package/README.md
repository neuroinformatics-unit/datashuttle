# Packaging

These notes explain how the Datashuttle desktop installers (Windows
`.exe`, macOS `.dmg`) are produced, how the GitHub Actions workflows
drive that process, and the conventions someone picking up the work
later should know about.

See [`TODO.txt`](TODO.txt) for outstanding tasks the maintainers have
flagged but not yet tackled.

macOS code-signing & notarisation is documented in §11 below.

---

## 1. What we ship

| Platform | Artifact | Built by | Installer technology | Signed |
|---|---|---|---|---|
| Windows (x64) | `datashuttle_<version>.exe` | `package/windows/package_windows.py` | [Inno Setup 6](https://jrsoftware.org/isinfo.php) | no (planned) |
| macOS Intel | `datashuttle-<version>-x86_64.dmg` | `package/macos/package_macos.py` | [`create-dmg`](https://github.com/create-dmg/create-dmg) | yes — Developer ID + notarised + stapled (when CI secrets are set) |
| macOS Apple Silicon | `datashuttle-<version>-arm64.dmg` | `package/macos/package_macos.py` | `create-dmg` | yes — Developer ID + notarised + stapled (when CI secrets are set) |

Each installer is fully self-contained: it bundles a frozen Python
runtime, all of `datashuttle`'s dependencies, the `rclone` CLI, and a
vendored copy of [WezTerm](https://wezfurlong.org/wezterm/) for hosting
the TUI. End users do not need Python, conda, or anything else
pre-installed.

---

## 2. Runtime architecture (how a built install actually runs)

The TUI is a [Textual](https://textual.textualize.io/) app. Textual
needs a real terminal to render into — you can't just double-click a
Python interpreter. The packaging therefore involves **two**
PyInstaller binaries:

```
  user double-clicks
        │
        ▼
  terminal_launcher  ◄── tiny PyInstaller bundle that knows how to
        │              spawn a real terminal window
        │ (subprocess.Popen)
        ▼
  WezTerm (vendored)  ◄── third-party terminal emulator, ships
        │              inside our installer
        │ (runs as its child process)
        ▼
  datashuttle  ◄── the main PyInstaller bundle: frozen Python +
                   datashuttle source + rclone
```

1. The OS launches `terminal_launcher` (`.exe` on Windows;
   `Datashuttle.app/Contents/MacOS/terminal_launcher` on macOS).
2. `terminal_launcher` locates the vendored WezTerm next to itself,
   and `subprocess.Popen`s `wezterm-gui … start -- … datashuttle`,
   passing a custom `wezterm_config.lua` via the `WEZTERM_CONFIG_FILE`
   env var.
3. WezTerm opens a window and runs the `datashuttle` executable inside
   it. `datashuttle` is a separate PyInstaller bundle that contains
   the actual TUI app.

The launcher / WezTerm / datashuttle split is the reason the macOS
packaging script does manual `shutil.copytree` calls to merge two
PyInstaller dist outputs into one `.app` bundle (see §4.2).

---

## 3. Project layout

```
package/
├── README.md                        # this file (full packaging + CI + signing reference)
├── TODO.txt                         # outstanding packaging tasks
│
├── packaging_utils.py               # shared helpers: WezTerm version + download
├── datashuttle_launcher.py          # entry point baked into datashuttle.spec
├── datashuttle.spec                 # PyInstaller spec — shared by Win + macOS
├── wezterm_config.lua               # Custom WezTerm config shipped inside the bundle
│
├── windows/
│   ├── package_windows.py           # Windows orchestrator (PyInstaller + Inno Setup)
│   ├── terminal_launcher_windows.py # Windows launcher source
│   ├── terminal_launcher_windows.spec
│   ├── make_inno_setup_script.py    # Generates the .iss script consumed by ISCC
│   └── NeuroBlueprint_icon.ico      # Windows installer icon
│
├── macos/
│   ├── package_macos.py             # macOS orchestrator (PyInstaller + create-dmg)
│   ├── terminal_launcher_macos.py   # macOS launcher source
│   ├── terminal_launcher_macos.spec # PyInstaller spec for macOS launcher (uses BUNDLE)
│   ├── sign_macos.py                # macOS code-signing + notarisation + stapling (no-op without env vars)
│   └── entitlements.plist           # Hardened-runtime entitlements used by sign_macos.py
│
└── (generated at build time)
    ├── _vendored/                       # WezTerm downloaded here (shared between platforms)
    ├── windows/build/                   # PyInstaller working dir (Windows)
    ├── windows/dist/                    # PyInstaller output + staging area (Windows)
    ├── windows/Output/                  # Final .exe installer lands here
    ├── windows/inno_compile_script.iss  # Generated Inno Setup script
    ├── macos/build/                     # PyInstaller working dir (macOS)
    ├── macos/dist/                      # PyInstaller output + staging area (macOS)
    └── macos/Output/                    # Final .dmg installer lands here
```

The platform-specific orchestrators (`package_windows.py`,
`package_macos.py`) add the parent `package/` directory to `sys.path`
at startup so they can `import packaging_utils` (and so the Windows
orchestrator can `import make_inno_setup_script`). The shared
`datashuttle.spec` and `datashuttle_launcher.py` live at `package/`
because both platforms build the exact same inner binary from them.

`_vendored/` is **not** committed — `packaging_utils.download_wezterm`
fetches a pinned WezTerm release the first time you build (and skips
the download on subsequent builds). Anchoring it at `package/` (rather
than inside each platform folder) means you only download WezTerm once
if you happen to build both platforms on the same machine.

---

## 4. Build process — step by step

### 4.1 Common preliminaries

Both platform scripts:

1. Resolve the datashuttle version with `importlib.metadata.version` —
   datashuttle must already be installed in the environment
   (`pip install .` or `pip install -e .`). The script aborts with a
   clear error if not.
2. Wipe stale `build/`, `dist/`, and `Output/` directories so we never
   pick up artifacts from a previous run.
3. Call `packaging_utils.download_wezterm` to fetch the pinned WezTerm
   release into `package/_vendored/` if it isn't already present.
4. Run `pyinstaller` twice — once for each spec file — pinning
   `--distpath` and `--workpath` to the platform subfolder
   (`package/windows/` or `package/macos/`). We pin these explicitly
   because the scripts are typically invoked from the repo root
   (`python package/macos/package_macos.py`), and we don't want
   PyInstaller defaults to leak `build/` / `dist/` into the repo root
   or to let the two platforms clobber each other's outputs.

### 4.2 `datashuttle.spec` (shared between Windows and macOS)

Produces the **inner** binary — the actual Textual app.

Key bits:

- **`tcss_files`** — TUI stylesheets are not pure-Python modules, so
  PyInstaller doesn't pick them up automatically. The spec globs them
  out of `datashuttle/tui/css/*.tcss` and adds them as `datas`. The
  glob is anchored on `SPECPATH` (the spec file's directory) rather
  than on the caller's CWD, so the lookup is robust regardless of
  where `pyinstaller` is invoked from. If no `.tcss` files are found,
  the spec **raises `FileNotFoundError`** rather than silently
  shipping a styleless app — this caught a real bug in earlier
  iterations.
- **`binaries`** — bundles the `rclone` executable located via
  `shutil.which("rclone")`. The spec raises `FileNotFoundError`
  upfront if rclone isn't on `PATH`, surfacing the problem at the
  start of the build instead of at first user-launch.
- **`hiddenimports`** — lists modules PyInstaller's static analysis
  can't see (typically lazy / dynamic imports inside Textual and
  Rich).
- **`target_arch`** — set from the `TARGET_ARCH` env var. The macOS
  matrix uses this to build separate x86_64 and arm64 binaries on
  the corresponding runner architectures.

Note: there is **no** `BUNDLE()` block here. This spec produces a
plain onedir layout (`dist/datashuttle/` containing the `datashuttle`
exe and an `_internal/` folder of deps). The macOS orchestrator copies
that into its `Datashuttle.app` later.

### 4.3 Windows pipeline (`package_windows.py`)

1. Run `datashuttle.spec` → `dist/datashuttle/datashuttle.exe` +
   `dist/datashuttle/_internal/`.
2. Run `terminal_launcher_windows.spec` →
   `dist/terminal_launcher/terminal_launcher.exe` + its own
   `_internal/`.
3. Move the launcher's contents up one level so they sit at
   `dist/terminal_launcher.exe` (the launcher is what the user
   double-clicks; its `_internal/` ends up alongside it).
4. Copy `_vendored/WezTerm-windows-…/` into `dist/_vendored/…`.
5. Copy the top-level `LICENSE` to `dist/license.txt` — this is the
   single source of truth for the EULA we show during install.
6. Copy the Windows icon and the `wezterm_config.lua` into the
   appropriate spots.
7. Render the Inno Setup script via `make_inno_setup_script` (uses
   `r"""…"""` so backslashes survive `.format`-style substitution),
   write it to `package/inno_compile_script.iss`.
8. Invoke `iscc.exe` from the standard Inno Setup install path. This
   produces `package/windows/Output/datashuttle_<version>.exe`.

Install layout on the user's machine: `C:\Program Files
(x86)\DataShuttle\` (set by `DefaultDirName={autopf}\DataShuttle`).
The 32-bit `{autopf}` is the Inno default because we don't set
`ArchitecturesInstallIn64BitMode` — fine for our purposes since
`terminal_launcher.exe` is a 64-bit binary that just happens to live
under `Program Files (x86)`.

### 4.4 macOS pipeline (`package_macos.py`)

1. Run `datashuttle.spec` → `dist/datashuttle/`.
2. Run `terminal_launcher_macos.spec` — this one **does** end with a
   `BUNDLE()` block, so it produces `dist/Datashuttle.app/` with the
   launcher binary at `Contents/MacOS/terminal_launcher` and its deps
   in `Contents/MacOS/_internal/`.
3. Merge the inner `datashuttle` build into the `.app` bundle:
   - `dist/datashuttle/_internal/` → `Datashuttle.app/Contents/Resources/_internal/`
   - `dist/datashuttle/datashuttle` → `Datashuttle.app/Contents/Resources/datashuttle`
4. Copy vendored WezTerm into `Contents/Resources/_vendored/…` and
   drop the `wezterm_config.lua` inside it.
5. Stage the LICENSE as `dist/license.txt` for `create-dmg`.
6. Call `create-dmg` with `--eula <license_path>` so Finder shows the
   MIT licence at first-mount. Output:
   `package/macos/Output/datashuttle-<version>-<arch>.dmg`.
7. Code-sign the `.app` (between steps 4 and 5) and notarise + staple
   the `.dmg` (after step 6) via [`sign_macos.py`](macos/sign_macos.py).
   Both calls are no-ops unless the relevant env vars are set, so
   local builds remain unsigned. See §11 for the full credential /
   entitlement / inside-out signing story.

The Info.plist (set in `macos/terminal_launcher_macos.spec`) carries
`LSMinimumSystemVersion`, `CFBundleVersion`, etc. — these come from
env vars set by `package_macos.py` so they stay in sync with the build.

---

## 5. CI / GitHub Actions

Two workflows, one per OS:

- [`.github/workflows/package_windows.yml`](../.github/workflows/package_windows.yml)
- [`.github/workflows/package_macos.yml`](../.github/workflows/package_macos.yml)

### 5.1 Triggers

Both workflows run on:

- Pushes to `main` (smoke test).
- Pushes of tags matching `v*` (release builds).
- Pull requests.
- Manual `workflow_dispatch` from the Actions tab, with an optional
  `test_release_upload` boolean input that pushes the artifact to a
  throwaway draft Release (useful for end-to-end testing without
  cutting a real tag).

### 5.2 Conda for both platforms

Both workflows use `conda-incubator/setup-miniconda@v4` rather than
`actions/setup-python`. The reason is `rclone`: installing it from
`conda-forge` gives us a known-good binary that matches the
environment, instead of relying on the host package manager. This
keeps macOS x86_64 and arm64 builds consistent with the Windows build.

Pattern:
```yaml
- name: Set up Conda
  uses: conda-incubator/setup-miniconda@v4
  with:
    python-version: "3.12"
    channels: conda-forge
- name: Install pip
  run: conda install pip
- name: Install rclone
  run: conda install -c conda-forge rclone
- name: Install dependencies
  run: |
    python -m pip install --upgrade pip
    python -m pip install .[dev]
    python -m pip install pyinstaller requests
```

Every pip line uses `python -m pip install`, not bare `pip`, to make
absolutely sure we're hitting the conda env's pip rather than a
system one.

### 5.3 macOS matrix

```yaml
matrix:
  include:
    - os: macos-15-intel
      target_arch: x86_64
      macos_min_version: "10.13.0"
      macosx_deployment_target: "10.13"
    - os: macos-14
      target_arch: arm64
      macos_min_version: "11.0.0"
      macosx_deployment_target: "11.0"
```

Notes:

- `macos-13` runners were retired by GitHub in early 2026. We now
  build on `macos-15-intel` / `macos-14` and pin the
  back-compat floor via `MACOSX_DEPLOYMENT_TARGET` — the **deployment
  target**, not the build host, determines the minimum macOS version
  the binary will actually run on.
- Apple Silicon's floor is `11.0` (the first Apple Silicon macOS); we
  use `10.13` for Intel.
- `TARGET_ARCH` is read by `datashuttle.spec` and propagated to the
  PyInstaller `target_arch=` argument, so each runner produces a
  natively-architected binary.

### 5.4 Post-build verification (macOS only, for now)

After packaging, the workflow runs:

```bash
BIN="package/macos/dist/Datashuttle.app/Contents/Resources/datashuttle"
test -x "$BIN"
file "$BIN"
lipo -archs "$BIN" | grep -q "${TARGET_ARCH}"
/usr/libexec/PlistBuddy -c "Print :LSMinimumSystemVersion" \
  package/macos/dist/Datashuttle.app/Contents/Info.plist
```

This fails loudly if PyInstaller produced a binary for the wrong
architecture (which is easy to do accidentally when conda env
mismatches arise).

When the signing/notarisation env vars are configured (tag pushes and
opt-in manual dispatches only), three additional verifications are
performed by `sign_macos.py`:

```bash
# After signing the .app bundle:
codesign --verify --strict --verbose=2 path/to/Datashuttle.app

# After notarising + stapling the .dmg:
xcrun stapler validate path/to/datashuttle-<version>-<arch>.dmg
spctl --assess --type open --context context:primary-signature \
  --verbose=2 path/to/datashuttle-<version>-<arch>.dmg
# expected: "accepted / source=Notarized Developer ID"
```

### 5.5 Releases

Both workflows use `softprops/action-gh-release@v2` to publish
artifacts. The release step is gated to either:

- a real tag push (`refs/tags/v*`), in which case it creates / updates
  a draft Release named after the tag, **or**
- a manual `workflow_dispatch` with `test_release_upload=true`, in
  which case it publishes to a `test-build-<run_id>` draft Release
  that can be deleted safely.

The macOS workflow uses the same approach to attach both x86_64 and
arm64 DMGs to the same release (because `softprops/action-gh-release`
appends assets when the release already exists).

`permissions: contents: write` is set on the job so the release step
has the token scope it needs. Pull requests from forks get the
default read-only token and won't be able to push releases, which is
the correct behaviour.

---

## 6. Versioning

- The project uses `setuptools_scm` (configured in `pyproject.toml`)
  to derive the version from git tags. Local dev builds end up with
  versions like `0.6.1.dev3+g1a2b3c4`.
- CI must check out with `fetch-depth: 0` for the macOS workflow so
  `setuptools_scm` has the full tag history.
- Tagging a release: `git tag vX.Y.Z && git push --tags`. The
  workflow then builds the installer and attaches it to a draft
  Release named `vX.Y.Z` — review and publish manually.

---

## 7. EULA / licence handling

A single source of truth: the top-level `LICENSE` file. Both
packaging scripts copy it to `dist/license.txt` at build time:

- Windows: Inno Setup picks it up via `LicenseFile=` in the generated
  `.iss`. The user sees the MIT licence and must accept it before the
  install proceeds.
- macOS: `create-dmg --eula <license_path>` makes Finder display the
  licence when the DMG is mounted.

If you change the licence, update only `LICENSE`. There is no stale
copy in `package/` (an older `package/license.txt` was removed when
the single-source-of-truth approach was introduced).

---

## 8. Local development

To build locally on Windows:

```powershell
# from an activated conda/venv with datashuttle installed
choco install innosetup -y     # one-time
python -m pip install pyinstaller requests
python package/windows/package_windows.py
# output: package/windows/Output/datashuttle_<version>.exe
```

To build locally on macOS:

```bash
brew install create-dmg        # one-time
conda install -c conda-forge rclone   # or: brew install rclone
python -m pip install pyinstaller requests
python package/macos/package_macos.py
# output: package/macos/Output/datashuttle-<version>-<arch>.dmg
```

Local macOS builds are **unsigned**. macOS will refuse to open them
without a Gatekeeper override (right-click → Open, or
`xattr -d com.apple.quarantine path/to/Datashuttle.app`). Signing &
notarisation only happen in CI once secrets are configured — see §11.

---

## 9. Gotchas / lessons learned

These are real things that broke in earlier iterations. Worth
remembering when modifying the packaging code.

### 9.1 Path quoting around `_MEIPASS`

PyInstaller extracts data files under `sys._MEIPASS`, which on Windows
is typically `C:\Program Files (x86)\DataShuttle\_internal\` — a path
containing spaces. When constructing rclone invocations via
`shell=True`, the full path **must** be wrapped in double quotes,
otherwise `cmd.exe` splits at the space and produces "rclone
installation not found" errors. See
[`datashuttle/utils/rclone.py`](../datashuttle/utils/rclone.py)
`get_command()`.

### 9.2 SSH script shebang ordering

The "call rclone through a script for the central connection" code path
generates a shell script on the remote host. The shebang line must be
prepended **after** `get_command()` builds the command line — if you
prepend first and then call `get_command()`, the resulting script
contains `rclone ... \n#!/bin/bash` and produces "Exec format error".
The current code in
[`datashuttle/utils/rclone.py`](../datashuttle/utils/rclone.py) has the
correct order; do not "tidy" it.

### 9.3 PyInstaller `__file__` is synthetic

For modules bundled inside the PYZ archive (i.e. all pure-Python
modules with the default `noarchive=False`), `__file__` is a synthetic
path — it points at where the module would live in `_MEIPASS` even
though there's no actual `.py` file on disk. This is fine for most
purposes but it means **do not use `__file__` at class-body /
import-time to look up data files** without going through
`sys._MEIPASS` first. The `CSS_PATH` setup in
[`datashuttle/tui/app.py`](../datashuttle/tui/app.py)
(`_resolve_css_path()`) handles this; the previous direct-glob
approach silently produced an empty list on macOS, yielding an
unstyled TUI with no error.

### 9.4 Spec files do not have `__file__`

PyInstaller exec's the spec file with a namespace that includes
`SPECPATH`, `workpath`, `distpath`, etc. — but **not** `__file__`.
Trying to use `__file__` in a spec file raises `NameError` at build
time. Always use `SPECPATH` to anchor relative paths in spec files.

### 9.5 `locals()` snapshots

If you iterate `locals().items()` in a function that also assigns to
new locals inside the loop (e.g. for debug-printing), Python raises
`RuntimeError: dictionary changed size during iteration`. The fix is
trivial: `for var, val in list(locals().items()):`. This bit us in
`package/windows/terminal_launcher_windows.py`.

### 9.6 Don't use `codesign --deep` on macOS

[`sign_macos.py`](macos/sign_macos.py) signs the bundle inside-out (deepest
Mach-O first, outer `.app` last) and deliberately skips the vendored
`_vendored/WezTerm-macos-*/` tree so WezTerm's own valid signature is
preserved. Never "simplify" this by switching to `codesign --deep` —
it silently overwrites nested signatures (including WezTerm's),
breaking the bundle in a way that only manifests at notarisation
time. Full reasoning in §11.

### 9.7 `shutil.which("rclone")` returns uppercase `.EXE` on Windows

Cosmetic only — Windows is case-insensitive — but if you regex-match
the path expecting lowercase `.exe`, you'll be surprised. The
extension comes from the `PATHEXT` env var, which is uppercase by
default.

### 9.8 Ruff D301 and raw docstrings

Any docstring containing `\` (e.g. Windows path examples) must use
`r"""..."""` to avoid D301. Easy to forget when adding examples
in docstrings.

---

## 10. Where to look when something breaks

| Symptom | First place to look |
|---|---|
| Windows installer build fails | `package/windows/package_windows.py` log + the generated `package/windows/inno_compile_script.iss` (kept after the run) |
| macOS .dmg build fails | `package/macos/package_macos.py` log; check `package/macos/dist/Datashuttle.app/Contents/` exists before `create-dmg` |
| `.tcss` styles missing in built app | `package/datashuttle.spec` glob → raises now if empty; also check `_resolve_css_path()` in `datashuttle/tui/app.py` |
| "rclone installation not found" at runtime | quoting in `datashuttle/utils/rclone.py` `get_command()` |
| Wrong architecture binary on macOS | `TARGET_ARCH` env var + `target_arch=` in spec; `lipo -archs` verification step in CI catches this |
| Gatekeeper refuses to open the app | check the build log for `[sign_macos]` lines — if it says `MACOS_SIGNING_IDENTITY not set; skipping`, the secrets aren't configured (see §11); otherwise check `codesign --verify` and `spctl --assess` output |
| Notarisation rejected | `xcrun notarytool log <submission-id> --apple-id … --team-id … --password …` — most common cause is a missed binary that lacks `--options runtime` or `--timestamp` |
| `setuptools_scm` produces `0.0.0` | `fetch-depth: 0` missing on the checkout step |

---

## 11. Apple code signing & notarisation

Everything needed to ship a signed + notarised `Datashuttle.app` (and
its enclosing `.dmg`) on macOS. Until the maintainer setup in §11.3 is
complete, end users will see Gatekeeper warnings ("Datashuttle.app is
damaged" / "cannot be opened because Apple cannot check it for
malicious software"), and on recent macOS versions the app will be
quarantined outright.

Signing only happens in CI — local dev builds remain unsigned.

### 11.1 Status

The **code** for signing, notarisation and stapling is implemented:

- [`package/macos/entitlements.plist`](macos/entitlements.plist) — hardened-runtime entitlements
- [`package/macos/sign_macos.py`](macos/sign_macos.py) — sign-inside-out + notarise + staple, gated on env vars
- [`package/macos/package_macos.py`](macos/package_macos.py) — calls `sign_macos` at the right points
- [`.github/workflows/package_macos.yml`](../.github/workflows/package_macos.yml) — imports cert + injects secrets

**What's still needed:** a maintainer must complete the one-time Apple
setup (§11.3) and add the six repo secrets (§11.4). Until then, the
workflow runs the signing code as a no-op and produces unsigned
builds.

### 11.2 Cost

**A single Apple Developer Program membership ($99/year, individual or
organisation) covers everything we need.** No additional fees:

- Developer ID Application certificate (sign `.app` for distribution outside the App Store)
- `notarytool` submissions — free, unlimited
- App-specific passwords — free, generated at <https://appleid.apple.com>
- GitHub Actions `macos-14` (arm64) and `macos-15-intel` runners — free for public repos

The Developer ID certificate itself is valid for **5 years**; the
membership must be renewed annually for that cert to keep working.

### 11.3 One-time setup (on the maintainer's end)

1. **Enroll in the Apple Developer Program** — $99/year. Individual or
   organisation account both work. Sign up at
   <https://developer.apple.com/programs/>.
2. **Create a "Developer ID Application" certificate** in your Apple
   Developer account. Two ways:
   - Xcode → Settings → Accounts → Manage Certificates → `+` →
     *Developer ID Application*, **or**
   - <https://developer.apple.com> → Certificates, IDs & Profiles → `+`
     → *Developer ID Application*.
3. **Export the cert as a `.p12`** from Keychain Access:
   right-click the cert → *Export* → set a strong password. The `.p12`
   must contain **both** the public certificate **and** the private
   key (Keychain Access will include both if you export from the "My
   Certificates" category, not "Certificates").
4. **Create an app-specific password** at <https://appleid.apple.com>
   (Sign-in & Security → App-Specific Passwords). This is what
   `notarytool` uses to authenticate.
   - *Alternative (cleaner long-term):* create an App Store Connect
     API key (`.p8`) with the *Developer* role. Slightly more setup
     but doesn't expire with your Apple ID password.
5. **Note your Team ID** —  10-character string visible in your Apple
   Developer account membership page.

### 11.4 GitHub repository secrets

Add the following under *Settings → Secrets and variables → Actions →
New repository secret*.

| Secret name | Value |
|---|---|
| `MACOS_CERTIFICATE` | base64 of the `.p12` — generate with `base64 -i cert.p12 \| pbcopy` |
| `MACOS_CERTIFICATE_PWD` | the password you set when exporting the `.p12` |
| `MACOS_SIGNING_IDENTITY` | e.g. `Developer ID Application: Your Name (TEAMID)` (run `security find-identity -v -p codesigning` locally to get the exact string) |
| `APPLE_ID` | your Apple ID email address |
| `APPLE_TEAM_ID` | your 10-character team ID |
| `APPLE_APP_SPECIFIC_PASSWORD` | the app-specific password from step 4 above |

Treat all of these as sensitive; never echo them in workflow logs.

### 11.5 Implementation reference

The subsections below document *what* the code does and *why*, so
future maintainers can understand and debug the pipeline. The actual
logic lives in [`macos/sign_macos.py`](macos/sign_macos.py); the snippets here are
the essential commands it issues.

#### 11.5.1 Entitlements — [`macos/entitlements.plist`](macos/entitlements.plist)

A Python-based app under hardened runtime needs two exceptions:

- `com.apple.security.cs.allow-unsigned-executable-memory` — Python uses
  JIT-like memory regions (ctypes / cffi / generated trampolines) that
  trip the default hardened-runtime memory protection.
- `com.apple.security.cs.disable-library-validation` — we load
  third-party dylibs (from the conda environment, WezTerm internals,
  `rclone`) that are not signed by our team ID.

Minimal content:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>com.apple.security.cs.allow-unsigned-executable-memory</key>
    <true/>
    <key>com.apple.security.cs.disable-library-validation</key>
    <true/>
</dict>
</plist>
```

#### 11.5.2 CI step to import the certificate

Use `apple-actions/import-codesign-certs@v3` (or equivalent) at the top
of the macOS packaging job — it creates a temporary keychain, imports
the `.p12`, and tears it down at the end of the job.

```yaml
- name: Import code-signing certificate
  uses: apple-actions/import-codesign-certs@v3
  with:
    p12-file-base64: ${{ secrets.MACOS_CERTIFICATE }}
    p12-password: ${{ secrets.MACOS_CERTIFICATE_PWD }}
```

#### 11.5.3 Sign inside-out from `package_macos.py`

Code-signing must walk the bundle **inside-out**: deepest binaries
first, outer `.app` last. Never use `codesign --deep` — it overwrites
nested signatures (including WezTerm's, which we want to preserve).

Order:

1. Sign the bundled `rclone` binary under
   `Datashuttle.app/Contents/Resources/_internal/rclone`.
2. Sign every `.dylib` / `.so` / Mach-O under
   `Datashuttle.app/Contents/Resources/_internal/` (use `find` +
   `file -b` filter, or rely on PyInstaller's own
   `codesign_identity=` argument on the `EXE()` calls in the specs).
3. Sign the inner `datashuttle` executable
   (`Contents/Resources/datashuttle`).
4. **Skip** `_vendored/WezTerm-macos-*/WezTerm.app` — its signature
   from the WezTerm project is already valid and will keep working as
   long as it's enclosed in a notarised outer bundle with a hardened
   runtime flag set on the enclosing app.
5. Sign the outer `Datashuttle.app` last.

Every `codesign` invocation needs:

```bash
codesign \
  --force \
  --sign "$MACOS_SIGNING_IDENTITY" \
  --options runtime \
  --entitlements package/macos/entitlements.plist \
  --timestamp \
  /path/to/binary-or-bundle
```

`--options runtime` enables the hardened runtime (required for
notarisation). `--timestamp` is also required — notarisation rejects
ad-hoc / un-timestamped signatures.

#### 11.5.4 Notarise the DMG

After `create-dmg` produces `Datashuttle.dmg`:

```bash
xcrun notarytool submit Datashuttle.dmg \
  --apple-id "$APPLE_ID" \
  --team-id "$APPLE_TEAM_ID" \
  --password "$APPLE_APP_SPECIFIC_PASSWORD" \
  --wait
```

`--wait` blocks until Apple's servers return a verdict (usually 1-5
minutes). If it fails, fetch the log with:

```bash
xcrun notarytool log <submission-id> \
  --apple-id "$APPLE_ID" \
  --team-id "$APPLE_TEAM_ID" \
  --password "$APPLE_APP_SPECIFIC_PASSWORD"
```

#### 11.5.5 Staple the ticket

```bash
xcrun stapler staple Datashuttle.dmg
```

Stapling attaches the notarisation ticket directly to the DMG so
Gatekeeper can verify offline. Without this the first launch on a
machine with no network will fail.

#### 11.5.6 Verify

Sanity checks to run in CI after stapling:

```bash
# Verify the DMG is correctly stapled
xcrun stapler validate Datashuttle.dmg

# Verify the app bundle's signature
codesign --verify --strict --verbose=2 \
  /path/to/Datashuttle.app

# Verify hardened runtime is enabled
codesign -dvvv /path/to/Datashuttle.app 2>&1 | grep flags
# Should show: flags=0x10000(runtime)

# Verify Gatekeeper acceptance
spctl --assess --type execute --verbose=2 \
  /path/to/Datashuttle.app
# Should print: accepted
# source=Notarized Developer ID
```

### 11.6 Order of operations

1. *Maintainer:* complete steps 1–5 in §11.3.
2. *Maintainer:* add the six secrets from §11.4 to the repo.
3. *Test:* trigger `package_macos.yml` with `workflow_dispatch` +
   `test_release_upload=true`. Watch the build log for
   `[sign_macos] Signed N inner binaries + outer bundle.` followed by
   `accepted / Notarized Developer ID` from `spctl --assess`.
4. *Ship:* push a `v*` tag. The workflow will sign + notarise + staple
   automatically and attach the DMG to the draft release.

Local builds (`python package/macos/package_macos.py` with no env vars set)
remain unsigned and skip notarisation — useful for iterating on the
packaging script itself.

### 11.7 Notarisation gotchas

- **Do not use `codesign --deep`.** It re-signs nested bundles with the
  outer identity, clobbering WezTerm's existing valid signature and
  silently producing a broken result.
- **Sign inside-out, always.** Any binary modified after the enclosing
  bundle is signed invalidates the outer signature.
- **`--options runtime` + `--timestamp` are non-negotiable** for
  notarisation. Forgetting either yields cryptic rejection logs.
- **Entitlements must be passed at sign time**, not after. You cannot
  add entitlements to an already-signed binary without re-signing.
- **WezTerm's hardened-runtime flag must already be set** for our
  bundle to notarise. As of WezTerm 20240203 it is — verify with
  `codesign -dvvv .../wezterm-gui 2>&1 | grep flags`; expect
  `flags=0x10000(runtime)`.
- **Notarisation only checks signed Mach-O binaries**; the bundled
  Python `.pyc` and `.tcss` files are ignored. Don't bother signing
  them individually.
- **First-time notarisation can take longer** (10-30 min) while Apple
  fingerprints the team; subsequent submissions are usually under 5
  minutes.
- **Renewal:** the Developer ID certificate is valid for 5 years; the
  `.p12` and team ID stay the same across renewals, but the
  app-specific password must be regenerated if the Apple ID password
  changes.
