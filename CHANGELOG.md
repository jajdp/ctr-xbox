# Changelog

All notable changes to this repository. Dates are `YYYY-MM-DD`.

The versions here are **the repository's**, not the package's. The package version is whatever you
pass to `construir-uwp.ps1 -Version`, and it has to go up on every package you install, because the
console will not replace a package with one of the same version.

## [1.0.0] — 2026-10-13

First publication. The recipe for the UWP port, as it was applied to the build that runs on two real
Xbox Series consoles: 32.9 FPS, full-screen 16:9, Spanish menus, and 60 FPS available.

### Added

- **`patches/ctr-uwp-port.patch`** — 90 files against CTRPad `76ad5fe`. The UWP port itself plus
  three additions behind CMake options: `CTR_WIDESCREEN` (real 16:9), `CTR_NATIVE_60FPS` (60 frames
  per second, 401 changes across 60 files, ported from CTR: High Octane) and the language index.
- **`src/uwp/ctr_uwp_main.cpp`** — the WinRT entry point: asks for `SDL_HINT_JOYSTICK_WGI`, without
  which no controller is ever enumerated, and joins the disc from its 150 MiB parts on first boot.
- **`patches/sdl3-uwp-audio-wasapi.patch`** — SDL3's WASAPI backend deadlocked on WinRT, and the
  game waits for a voice line before leaving the presentation screen, so the whole thing hung with
  the process alive and the CPU at 0%. Three files; the fix is one of them. **Useful to any UWP port
  that uses SDL3.**
- **`tools/aplicar.py`** — applies the recipe with `git apply` (all or nothing), copies the entry
  point, and optionally patches your SDL3 checkout. Idempotent.
- **`tools/construir-uwp.ps1`** — compiles, lays out the package with the UWP libraries and your
  tiles, packages with `makeappx` and signs with `signtool`. Everything by parameter; it checks the
  certificate and the manifest's `Publisher` **before** compiling, instead of failing at the end.
- **`tools/partir_disco.py`** — the disc in 150 MiB parts, because the Device Portal answers 500 to
  the whole thing.
- **Documentation in both languages**: a build-and-install guide that says which terminal each
  command goes in, whether administrator is needed (it is not, and in one step it breaks things),
  and how the console has to be set up — including that **with no profile signed in the console will
  not launch apps**. Plus `HOW-IT-WORKS`, with every failure that had to be solved and what the log
  said.

### Verified

Applied to a clean clone of CTRPad, the recipe leaves **91 of 91 files with the same content** as
the tree the installed, tested package was built from (90 byte for byte; `main.c` differs only in
line endings, which the reference tree happens to keep as CRLF).

### Not included, on purpose

- The disc, the built executable, the `.msix`, the saves and the package tiles.
- The UWP libraries (SDL3, Mesa, `libuwp`): they are other people's binaries. The guide says where
  to get them.
