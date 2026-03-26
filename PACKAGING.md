# Packaging Boneglaive as Distributable Binaries

Goal: produce standalone binaries for Windows, Linux, and FreeBSD using PyInstaller.
End users need no Python, no Cairo, no pygame — just the binary.

---

## What needs doing

### 1. Fix asset path loading for PyInstaller
PyInstaller unpacks files to a temp dir (`sys._MEIPASS`) at runtime, so relative paths like
`"graphics/units/glaiveman.svg"` break. Every asset load site needs a base-path helper:

```python
def asset_path(relative):
    base = getattr(sys, '_MEIPASS', Path(__file__).parent.parent.parent)
    return str(Path(base) / relative)
```

Then replace bare relative path strings with `asset_path("graphics/...")` throughout the
graphical code. The main offenders are `renderer.py`, `animations/core.py`, `animations/main.py`,
and the UI files in `graphical/ui/`.

### 2. Write a PyInstaller `.spec` file
Tells PyInstaller to bundle the asset directories. Rough shape:

```python
# boneglaive.spec
a = Analysis(
    ['run_graphical.py'],
    datas=[
        ('graphics/', 'graphics/'),
        ('sounds/', 'sounds/'),
        ('maps/', 'maps/'),
        ('config.json', '.'),
    ],
    hiddenimports=['cairosvg', 'cairocffi'],
)
```

### 3. Write a GitHub Actions workflow
Builds all three binaries in parallel on push/release. Runners needed:
- `ubuntu-latest` → Linux binary
- `windows-latest` → Windows binary (also installs Cairo via GTK/MSYS2 so cairosvg works at build time)
- FreeBSD via `cross-platform-actions/action` → FreeBSD binary

Artifacts attached to the release so they're downloadable.

### 4. Handle `platform_compat.py` on Windows
This file does `import curses` at the top level (line 10). `curses` doesn't ship with Python on
Windows. Nothing in the graphical path imports it currently, but it should be guarded:

```python
import platform
if platform.system() != 'Windows':
    import curses
```

Fix this before attempting a Windows build or it will fail at PyInstaller analysis time.

---

## Order of work

1. **Claude**: add `asset_path()` helper, update load sites, guard `platform_compat.py`
2. **Claude**: write `boneglaive.spec`
3. **Claude**: write `.github/workflows/build.yml`
4. **You**: push to GitHub, verify the three Actions builds succeed and artifacts download/run

---

## Notes

- The Windows runner needs Cairo available at *build* time so PyInstaller can capture the DLLs.
  The standard approach is `choco install msys2` + `pacman -S mingw-w64-x86_64-cairo` in the workflow.
- FreeBSD is not a GitHub-hosted runner — the workflow will use `cross-platform-actions/action`
  which spins up a FreeBSD VM. Slightly slower but works.
- `cairosvg` and `cairocffi` are pure Python + CFFI — PyInstaller bundles them fine as long as
  the Cairo native library is present on the build machine.
- `config.json` is bundled as a default config. On first run it will be read-only inside
  `_MEIPASS`; the game should write user config to a writable location (it currently uses the
  script directory, which won't be writable in a packaged binary). May need a small fix to write
  to `~/.config/boneglaive/` or `%APPDATA%\boneglaive\` on Windows.
