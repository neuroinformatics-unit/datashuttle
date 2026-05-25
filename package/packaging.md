# Packaging & CI guide

This document explains how the Datashuttle desktop installers (Windows
`.exe`, macOS `.dmg`) are produced, how the GitHub Actions workflows
drive that process, and the conventions someone picking up the work
later should know about.

It complements:
- [`README.md`](README.md) — quick "how do I build locally?" recipe.
- [`apple-notarisation-notes.md`](apple-notarisation-notes.md) —
  everything specific to Apple code-signing & notarisation.
- [`TODO.txt`](TODO.txt) — outstanding tasks the maintainers have
  flagged but not yet tackled.

---

## 1. What we ship

| Platform | Artifact | Built by | Installer technology |
|---|---|---|---|
| Windows (x64) | `datashuttle_<version>.exe` | `package/package_windows.py` | [Inno Setup 6](https://jrsoftware.org/isinfo.php) |
| macOS Intel | `datashuttle-<version>-x86_64.dmg` | `package/package_macos.py` | [`create-dmg`](https://github.com/create-dmg/create-dmg) |
| macOS Apple Silicon | `datashuttle-<version>-arm64.dmg` | `package/package_macos.py` | `create-dmg` |

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
├── apple-notarisation-notes.md      # macOS signing reference (separate doc)
├── packaging.md                     # this file
├── README.md                        # short local-build recipe
├── TODO.txt                         # outstanding packaging tasks
│
├── packaging_utils.py               # shared helpers: WezTerm version + download
│
├── datashuttle_launcher.py          # entry point baked into datashuttle.spec
├── datashuttle.spec                 # PyInstaller spec — shared by Win + macOS
│
├── terminal_launcher_windows.py     # Windows launcher source
├── terminal_launcher_windows.spec   # PyInstaller spec for Windows launcher
├── terminal_launcher_macos.py       # macOS launcher source
├── terminal_launcher_macos.spec     # PyInstaller spec for macOS launcher (uses BUNDLE)
│
├── package_windows.py               # Windows orchestrator (PyInstaller + Inno Setup)
├── package_macos.py                 # macOS orchestrator (PyInstaller + create-dmg)
├── make_inno_setup_script.py        # Generates the .iss script consumed by ISCC
│
├── wezterm_config.lua               # Custom WezTerm config shipped inside the bundle
├── NeuroBlueprint_icon.ico          # Windows installer icon
│
└── (generated at build time)
    ├── _vendored/                   # WezTerm downloaded here
    ├── build/                       # PyInstaller working dir
    ├── dist/                        # PyInstaller output + staging area
    ├── Output/                      # Final installer (.exe / .dmg) lands here
    └── inno_compile_script.iss      # Windows only: generated installer script
```

`_vendored/` is **not** committed — `packaging_utils.download_wezterm`
fetches a pinned WezTerm release the first time you build (and skips
the download on subsequent builds).

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
   `--distpath` and `--workpath` to subfolders of `package/`. We pin
   these explicitly because the scripts are typically invoked from the
   repo root (`python package/package_macos.py`), and we don't want
   PyInstaller defaults to leak `build/` / `dist/` into the repo root.

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
   produces `package/Output/datashuttle_<version>.exe`.

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
   `package/Output/datashuttle-<version>-<arch>.dmg`.

The Info.plist (set in `terminal_launcher_macos.spec`) carries
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
BIN="package/dist/Datashuttle.app/Contents/Resources/datashuttle"
test -x "$BIN"
file "$BIN"
lipo -archs "$BIN" | grep -q "${TARGET_ARCH}"
/usr/libexec/PlistBuddy -c "Print :LSMinimumSystemVersion" \
  package/dist/Datashuttle.app/Contents/Info.plist
```

This fails loudly if PyInstaller produced a binary for the wrong
architecture (which is easy to do accidentally when conda env
mismatches arise).

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
python package/package_windows.py
# output: package/Output/datashuttle_<version>.exe
```

To build locally on macOS:

```bash
brew install create-dmg        # one-time
conda install -c conda-forge rclone   # or: brew install rclone
python -m pip install pyinstaller requests
python package/package_macos.py
# output: package/Output/datashuttle-<version>-<arch>.dmg
```

Local macOS builds are **unsigned**. macOS will refuse to open them
without a Gatekeeper override (right-click → Open, or
`xattr -d com.apple.quarantine path/to/Datashuttle.app`). Signing &
notarisation only happen in CI once secrets are configured — see
[`apple-notarisation-notes.md`](apple-notarisation-notes.md).

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
`package/terminal_launcher_windows.py`.

### 9.6 Don't use `codesign --deep` on macOS

When we get to code-signing, `--deep` will silently overwrite the
WezTerm signature with ours, breaking the bundle. Sign inside-out
instead. Detailed in
[`apple-notarisation-notes.md`](apple-notarisation-notes.md).

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
| Windows installer build fails | `package/package_windows.py` log + the generated `inno_compile_script.iss` (kept after the run) |
| macOS .dmg build fails | `package/package_macos.py` log; check `package/dist/Datashuttle.app/Contents/` exists before `create-dmg` |
| `.tcss` styles missing in built app | `package/datashuttle.spec` glob → raises now if empty; also check `_resolve_css_path()` in `datashuttle/tui/app.py` |
| "rclone installation not found" at runtime | quoting in `datashuttle/utils/rclone.py` `get_command()` |
| Wrong architecture binary on macOS | `TARGET_ARCH` env var + `target_arch=` in spec; `lipo -archs` verification step in CI catches this |
| Gatekeeper refuses to open the app | code-signing not yet configured; see `apple-notarisation-notes.md` |
| `setuptools_scm` produces `0.0.0` | `fetch-depth: 0` missing on the checkout step |
