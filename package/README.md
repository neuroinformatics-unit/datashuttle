# Packaging

These notes explain how the Datashuttle desktop installers (Windows
`.exe`, macOS `.dmg`) are produced, how the GitHub Actions workflows
drive that process, and the conventions someone picking up the work
later should know about.

## 1. What we ship

| Platform | Artifact | Built by | Installer technology | Signed                                          |
|---|---|---|---|-------------------------------------------------|
| Windows (x64) | `datashuttle_<version>.exe` | `package/windows/package_windows.py` | [Inno Setup 6](https://jrsoftware.org/isinfo.php) | no, as requires registered company to code sign |

Each installer is fully self-contained: it bundles a frozen Python
runtime, all of `datashuttle`'s dependencies, the `rclone` CLI, and a
vendored copy of [WezTerm](https://wezfurlong.org/wezterm/) for hosting
the TUI. End users do not need Python, conda, or anything else
pre-installed.

---

## 2. Runtime architecture (how a built install actually runs)

The TUI is a [Textual](https://textual.textualize.io/) app. Textual
does not render well on all native system terminals and so we need to
vendor a terminal emulator we know it runs well on - we chose WezTerm.
Wezterm is cross platform and does not require signing up e.g (unlike Warp).

The packaging therefore involves **two**
PyInstaller binaries.

First we create a `datashuttle.exe` that can be called from any
terminal emulator and will run datashuttle. This is done using the
standard PyInstaller workflow to package a Python software.

Next a light wrapper 'terminal_launcher.exe' is also packaged
which just opens our vendored Wezterm and calls `datashuttle.exe` in it.

```
  user double-clicks
        │
        ▼
  terminal_launcher  ◄── tiny PyInstaller bundle that calls the
        │              vendored Wezterm to run datashuttle.exe
        │
        ▼
  WezTerm (vendored)  ◄── third-party terminal emulator, ships
        │              inside our installer
        ▼
  datashuttle.exe  ◄── the main PyInstaller bundle: frozen Python +
                   datashuttle source + rclone
```

Details:
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

`package_windows.py` adds the parent `package/` directory to `sys.path`
at startup so they can `import packaging_utils` (and so the Windows
orchestrator can `import make_inno_setup_script`). The shared
`datashuttle.spec` and `datashuttle_launcher.py` live at `package/`
because both platforms build the exact same inner binary from them.

`_vendored/` is **not** committed — `packaging_utils.download_wezterm`
fetches a pinned WezTerm release the first time you build (and skips
the download on subsequent builds).

---

## 4. Build process — step by step

First, the build script downloads Wezterm if it is not already present.
Then, PyInstaller is run twice, first `datashuttle.spec` which
creates `datashuttle.exe`, then `terminal_launcher.spec` which
creates `terminal_launcher.exe`.

### `datashuttle.spec`

Produces the **inner** binary — the actual Textual app. PyInstaller
can not always find all resources required automatically, so some need
to be manually added at the top of the spec file. This includes textuals
`tcss` files, `rclone` and some other `hiddenimports`.


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


## 5. CI / GitHub Actions

Two workflows, one per OS:

- [`.github/workflows/package_windows.yml`](../.github/workflows/package_windows.yml)

The workflows run on push to main with a `v` tag. The project uses `setuptools_scm` (configured in `pyproject.toml`)
to derive the version from git tags. Local dev builds end up with
versions like `0.6.1.dev3+g1a2b3c4`.

At build time, the distribution scripts and documentation both have
access to the current tag version through `setuptools_scm`. They use
this to build the file name for this release.

The installer is uploaded as an artefact to the release page, and the documentation
links to this file from the documentation's install page.
