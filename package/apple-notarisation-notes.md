# Apple code signing & notarisation — setup notes

These notes capture everything needed to ship a signed + notarised
`Datashuttle.app` (and its enclosing `.dmg`) on macOS. Until this is in
place, end users will see Gatekeeper warnings ("Datashuttle.app is
damaged" / "cannot be opened because Apple cannot check it for malicious
software"), and on recent macOS versions the app will be quarantined
outright.

Signing only happens in CI — local dev builds remain unsigned.

---

## 1. One-time setup (on the maintainer's end)

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
5. **Note your Team ID** — 10-character string visible in your Apple
   Developer account membership page.

---

## 2. GitHub repository secrets

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

---

## 3. Repo changes required (to be added once secrets exist)

### 3.1 Entitlements file — `package/entitlements.plist`

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

### 3.2 CI step to import the certificate

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

### 3.3 Sign inside-out from `package_macos.py`

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
  --entitlements package/entitlements.plist \
  --timestamp \
  /path/to/binary-or-bundle
```

`--options runtime` enables the hardened runtime (required for
notarisation). `--timestamp` is also required — notarisation rejects
ad-hoc / un-timestamped signatures.

### 3.4 Notarise the DMG

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

### 3.5 Staple the ticket

```bash
xcrun stapler staple Datashuttle.dmg
```

Stapling attaches the notarisation ticket directly to the DMG so
Gatekeeper can verify offline. Without this the first launch on a
machine with no network will fail.

### 3.6 Verify

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

---

## 4. Order of operations

1. *Maintainer:* complete steps 1-5 in §1.
2. *Maintainer:* add the six secrets from §2 to the repo.
3. *Code change:* add `package/entitlements.plist` (§3.1).
4. *Code change:* update `package/package_macos.py` to walk the bundle
   and sign inside-out (§3.3), gated on the `MACOS_SIGNING_IDENTITY`
   env var so local builds stay unsigned.
5. *Code change:* update `.github/workflows/package_macos.yml` with the
   cert-import step (§3.2), notarisation (§3.4), stapling (§3.5), and
   verification (§3.6).
6. Trigger a packaging run, watch for `accepted / Notarized Developer
   ID` in the verify step.

---

## 5. Gotchas / lessons learned

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
