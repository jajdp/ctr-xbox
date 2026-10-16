# Crash Team Racing on Xbox — the UWP port

How to take [CTRPad](https://github.com/chrissotraidis/ctrpad) — the native port of *Crash Team
Racing* (PlayStation, 1999, `SCUS-94426`) to real 64-bit, on top of the
[CTR-ModSDK](https://github.com/CTR-tools/CTR-ModSDK) decompilation — and run it **on an Xbox Series
in Developer Mode**, as a UWP package you build and sign yourself.

*(Español: [README.es.md](README.es.md))*

It is not a theory: the game boots, has sound, plays the Sony presentation and the Nitros Oxide
intro, takes controller input and runs at **32.9 FPS** — the original game's rate — in **full-screen
16:9**, **in Spanish**, and at **60 frames per second** if you ask for it. It is installed and
tested on two consoles.

## What this repository is

**A recipe and the tools that apply it.** CTRPad has no UWP support at all: this is what had to be
added for a console to run it, plus three things the port gains along the way, each behind a CMake
option. Everything is applied **to your own checkout** of CTRPad, on your machine.

| Piece | What it is |
|---|---|
| `patches/ctr-uwp-port.patch` | The game patch: 90 files. The UWP port, widescreen, 60 FPS and the language |
| `src/uwp/ctr_uwp_main.cpp` | The WinRT entry point: asks for the controller through Windows.Gaming.Input and joins the split disc |
| `patches/sdl3-uwp-audio-wasapi.patch` | SDL3's audio deadlock on WinRT, without which the game **never gets past the presentation screen**. Useful for any UWP port that uses SDL3 |
| `tools/` | The orchestrator, the build/package/sign script, and the disc splitter |

## What this repository is **not**

It contains **no game code, no disc image, no built executable, no `.msix` package, no UWP libraries
and no artwork**. It cannot produce a playable game on its own. You need your own legally dumped
copy of the disc and CTRPad building on your PC first. See [`NOTICE.md`](NOTICE.md).

The package tiles are **not** here either: the real package's were made from the game's art, which
belongs to its owners. You supply your own — [`docs/ASSETS.md`](docs/ASSETS.md) lists the sizes, and
the script stops if the folder is empty.

## What you need first

| | |
|---|---|
| CTRPad | [chrissotraidis/ctrpad](https://github.com/chrissotraidis/ctrpad), **cloned with git** (the patch is applied with `git apply`) and building on your PC first |
| Your own disc | An NTSC-U dump of `SCUS-94426`, as `ctr-u.bin` |
| Visual Studio | 2022, with the C++ tools **and the UWP component**; packaging is `makeappx` and signing is `signtool`, both from the Windows SDK |
| The UWP bundle | SDL3, Mesa and `libuwp` built for UWP: [`worleydl/uwp-dep`](https://github.com/worleydl/uwp-dep). Not distributed here ([`docs/INSTALL.md`](docs/INSTALL.md) §2) |
| SDL3 for UWP | [`XboxEmulationHub/SDL3-uwp`](https://github.com/XboxEmulationHub/SDL3-uwp), **built by you and with the audio patch**: the `SDL3.dll` from its release will not do (§2 of the guide) |
| PowerShell | The one Windows already ships: **PowerShell 7 is not needed** |
| Python 3 | To apply the recipe. Standard library only |
| An Xbox in Developer Mode | And a certificate to sign with — a self-signed one is fine |

## How it goes

Two commands. [`docs/INSTALL.md`](docs/INSTALL.md) §0 covers the terminal at more length, and the
rest of that guide is the long version.

> **Where to type this:** in **PowerShell** — press the **Windows** key, type `powershell` and
> press **Enter** — in an **ordinary** window: you do not need "run as administrator", and using it
> would break signing, because the certificate lives in the store of whoever runs the command. From
> this repository's folder.

```powershell
# 1. apply the recipe to your CTRPad checkout (and, with --sdl3, the audio patch)
python tools\aplicar.py C:\ctr\ctrpad --sdl3 C:\ctr\SDL3-uwp

# 2. build, package and sign
powershell -ExecutionPolicy Bypass -File tools\construir-uwp.ps1 `
    -Arbol C:\ctr\ctrpad -Dep C:\ctr\uwp-dep -Version 1.0.0.0 -Certificado <your thumbprint> -Panoramico
```

`python tools\aplicar.py --list` says what each step does.

Then install the `.msix` through the Device Portal and upload your disc, **split**, to the app's
`LocalState`. Step by step, including the console side:
**[`docs/INSTALL.md`](docs/INSTALL.md)**.

## What it had to solve

Every one of these was a real failure on the console. The detail, with what the log said and what
was measured, is in **[`docs/HOW-IT-WORKS.md`](docs/HOW-IT-WORKS.md)**.

| | Symptom | Fix |
|---|---|---|
| 1 | Stuck on the presentation screen, process alive, CPU at 0% | Not the disc: the game waits for a voice line to finish, and audio never opened. `WASAPI_ActivateDevice` called `WASAPI_PrepDevice` **from WASAPI's own management thread**, and the check meant to catch that did not recognise the thread: the task was queued waiting for the thread already running it |
| 2 | Activation failed with `0x8027025B` | The VCLibs dependency was missing from the manifest. Putting the DLLs inside the package does **not** replace it |
| 3 | No button did anything | On WinRT, controllers arrive through **Windows.Gaming.Input**, and its driver switches itself off unless the app asks for `SDL_HINT_JOYSTICK_WGI`. One line in the entry point. This is the second time this hint has bitten in this catalogue |
| 4 | The disc would not upload: HTTP 500 | Portal uploads pass through `D:\DevelopmentFiles`, which is small. It goes in 150 MiB parts and the game joins them on the next launch |
| 5 | The game was in English | Spanish is already on the disc: it only had to be asked for. A `1` for a `6` where the language file is loaded |
| 6 | 4:3 with bars | *High Octane*'s widescreen ported by hand to CTRPad: the view-projection matrix's X row is squeezed and the UI is compensated primitive by primitive. **It costs no frames** |
| 7 | 30 FPS, like the PlayStation | *High Octane*'s 60 FPS: 401 changes across 60 files, with transplant tooling. **59.8 FPS** measured on the console; off by default |

## Credits and license

Port and tooling by **Recompilaciones**. Released under the [GPL-3.0-or-later](LICENSE), the same
license as CTRPad and CTR Native, which this derives from. Widescreen and 60 FPS are ported from
[CTR: High Octane](https://github.com/Rinnegatamante/Crash-Team-Racing-High-Octane) (GPL-3.0) with
the changes CTRPad needed; the detail is in [`NOTICE.md`](NOTICE.md).

The code and script comments are in Spanish, which is where they were written. The documentation is
in both languages.

*Crash Team Racing* is © Sony Interactive Entertainment / Naughty Dog. This project is not
affiliated with them, with Microsoft, or with the authors of the decompilation, CTR Native, CTRPad
or High Octane, and it distributes nothing that belongs to them. Rights holders can write to
**jajdpmail@gmail.com**.
