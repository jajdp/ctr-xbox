# How it works, and why each piece is there

*(Español: [HOW-IT-WORKS.es.md](HOW-IT-WORKS.es.md))*

Every piece of this repository came out of a specific failure on a real console. This is what it
was, how it was found, and what fixed it. If you only want to build the thing,
[`INSTALL.md`](INSTALL.md) is enough.

## Where it starts from

There are three links in the chain before this one, and each solves what the previous could not:

| | |
|---|---|
| [CTR-ModSDK](https://github.com/CTR-tools/CTR-ModSDK) | The decompilation, around 73% |
| [CTR Native](https://github.com/CTR-tools/ctr-native) | The native PC port, with SDL3 and OpenGL 3.3. It is **32-bit**, because the game's code keeps PlayStation pointers in 32 bits |
| [CTRPad](https://github.com/chrissotraidis/ctrpad) | Takes CTR Native to **real 64-bit**, with a checked memory model and guest references instead of raw pointers. That is what makes a console possible, where 32-bit is not an option |

What this repository adds is the fourth link: making that run inside an Xbox App Container, with its
window, its audio, its controller and its disc.

On the console the game draws with **OpenGL on Mesa built for UWP**, which translates to Direct3D
12, presented by SDL3 in a 1920×1080 window; audio goes out through WASAPI at 44 100 Hz stereo; and
the disc lives in the app's `LocalState`.

## Building and packaging: nine stumbles

None is interesting by itself, but together they are half the work of a UWP port, and every one of
them shows up again in the next:

| | Symptom | Cause and fix |
|---|---|---|
| 1 | `MSB8024: Using static version of the C++ runtime library is not supported` | UWP does not allow the static CRT, and CTRPad's CMake pins it for MSVC. In UWP it becomes `MultiThreadedDLL` |
| 2 | 102 errors inside the SDK's `combaseapi.h` | `native_win32.h` defines `NOUSER` to avoid clashing with the game's names, and without `winuser.h` the SDK's COM will not compile. Not defined in UWP |
| 3 | `missing ';' before identifier 'far'` in `objidl.h` | The same file does `#undef far` / `#undef near`, and the COM headers SDL pulls in afterwards use `FAR`/`NEAR`. In UWP they are redefined empty after the `#undef` |
| 4 | `WRL requires C++ compilation (use a .cpp suffix)` | `SDL_main.h` generates the WinRT startup and **is C++**, while the game is a single translation unit in C. The entry point moves to `platform/uwp/ctr_uwp_main.cpp`, the port's only C++ file |
| 5 | `The C++ file that includes SDL_main.h must be compiled with /ZW` | With `/ZW` (C++/CX) the link blows up: `vccorlib` wants a `Platform::Array` `main` and clashes with the CRT (`LNK2038`, `LNK2005`). SDL covers this case: define `SDL_WINRT_METADATA_FILE_AVAILABLE` and compile **without** `/ZW` |
| 6 | `unresolved external symbol main` | The app has to be a windowed one, not a console one, so the CRT enters through the `WinMain` SDL provides |
| 7 | The game's warnings turned into errors (`C4996`, `C4146`, `C4308`) | Windows Store projects carry `/sdl`. Turned off with `/sdl-` |
| 8 | It installs but **will not start**: `0x8027025B` | `<PackageDependency Name="Microsoft.VCLibs.140.00" …>` is missing from the manifest. Putting the DLLs inside the package does not replace it |
| 9 | `-2147009293: package depends on a framework that could not be found` | VCLibs' `MinVersion` cannot be higher than the one installed on the console. It is kept low on purpose |

Two more, about method: a WinRT app's main thread stack is **1 MB** (8 on desktop), so this game asks
for `/STACK:33554432`; and **there is no console in UWP**, so `stdout` and `stderr` are lost — and
that is where the game's errors go: they are redirected to files in `LocalState`, unbuffered. Without
that, none of what follows could have been seen.

## Getting the data in and drawing: seven more

| | Symptom | Cause and fix |
|---|---|---|
| 10 | It starts and dies leaving no log | `SDL_CreateDirectory` **does not create parent folders**, so it could not create its own data folder. They are created one by one |
| 11 | The Device Portal answers **500** for the 578 MB disc, but accepts a 150 MiB file | The portal writes a temporary file on `D:\`, the Developer Mode volume, which is short on space — even with 13 GB free in `LocalState`. The disc is split into four and **the game joins them at startup** |
| 12 | `Could not initialize OpenGL / GLES library`, and `SDL_LoadObject` says "That operation is not supported" | The `SDL3.dll` from SDL3-uwp's release is built with the generic configuration: no dynamic loading, and its EGL looks for `libEGL.so.1`, a Linux name. It has to be built from its WinRT project |
| 13 | EGL/ANGLE or WGL? | That SDL carries both paths, but its configuration leaves GLES/EGL commented out and WGL active: on a console the right path is **desktop OpenGL with Mesa**, not ANGLE |
| 14 | The process dies on the first draw call, **no dump and no message** | It was **Mesa's version**: with a freshly released one the process vanishes inside `BeginScene`; with the one that already worked on that same console, it draws. Third time Mesa has decided things in this catalogue, and the rule is always the same: **try the Mesa that already works first** |
| 15 | `Failed to initialise SDL input subsystem: SDL not built with haptic support` | That SDL has no haptics, and the game asked for every subsystem at once. In UWP it asks only for `SDL_INIT_GAMEPAD` |
| 16 | Near geometry came out broken in the 64-bit trial | That was the earlier trial on CTR Native, not CTRPad: CTRPad already solves the 64-bit memory model, which is why it is the base |

## The presentation-screen wall: it was the audio

The first installed build stopped on the presentation screen with **the process alive and the CPU at
0%**. It was not the CD layer. That screen is a loop waiting for the "Start your engines…" voice
line to finish:

```c
CDSYS_XAPlay(CDSYS_XA_TYPE_EXTRA, 0x50);
while (sdata->XA_State != 0) { VSync(0); CDSYS_XAPauseAtEnd(); }
```

With no audio, that loop never ends. And audio never opened because `SDL_OpenAudioDeviceStream` hung
**inside SDL3**.

**The cause**, following WASAPI's task queue: `WASAPI_ActivateDevice` calls `WASAPI_PrepDevice`
**from WASAPI's own management thread**, and the check meant to catch that —
`SDL_GetCurrentThreadID() == SDL_GetThreadID(ManagementThread)`, in
`WASAPI_ProxyToManagementThread` — does not recognise the thread. So the task is queued... waiting
for the thread that is already running it.

**The patch** (`patches/sdl3-uwp-audio-wasapi.patch`) touches three files of the backend:

| File | Change |
|---|---|
| `SDL_wasapi.c` | The management thread **records its own id** on startup, and the check uses that. **This is the fix**; the rest is protection |
| `SDL_wasapi.c` | Waiting for a task's result gets a 6 s cap, and says so |
| `SDL_wasapi_winrt.cpp` | Caps for the `DeviceWatcher` (3 s) and for `ActivateAudioInterfaceAsync` (4 s), whose wait SDL itself documents as "*this can block indefinitely*" |

**It is useful to any UWP port that uses SDL3 with audio**, not just this one.

Two safeguards stay in the game, and neither fires once audio works: the SPU init no longer retries
opening the device on every operation — it did so thousands of times, and with audio down that alone
keeps startup from finishing — and the XA loop moves on without sound if it has not advanced in 600
frames.

> Opening audio from a worker thread was also tried, in case the problem was that the game runs on
> the app view's thread. **It was not needed**: after the patch, audio opens fine from the main
> thread, and the detour was removed.

## The second wall: no controller input

With audio fixed, the game reached the menu and **no button did anything**. On the console only the
Xbox button worked, and that one the system handles — it never reaches the app.

On WinRT controllers arrive through **Windows.Gaming.Input** and nowhere else: this SDL's
configuration enables `SDL_JOYSTICK_WGI` and leaves XInput inside the `#else`, so that path is not
even compiled. And the WGI driver **switches itself off** if the app does not ask for it:

```c
/* src/joystick/windows/SDL_windows_gaming_input.c */
static bool WGI_JoystickInit(void)
{
    if (!SDL_GetHintBoolean(SDL_HINT_JOYSTICK_WGI, false)) {
        return true;                 /* leaves without enumerating anything */
    }
```

The default is "0" — SDL3's own `SDL_hints.h` documents it — and neither CTRPad nor this port set
it. It is not an SDL3-uwp defect: it is a step that belongs to the application. **One line**, in the
WinRT entry point, running before the game initialises the gamepad subsystem:

```cpp
SDL_SetHintWithPriority(SDL_HINT_JOYSTICK_WGI, "1", SDL_HINT_OVERRIDE);
```

And, for next time, the diagnosis is in the log from its first page:

| What it says | What it means |
|---|---|
| `mandos detectados al arrancar: 2 (WGI=1)` | Correct: the driver enumerated and the game opened the pads |
| `mandos detectados al arrancar: 0 (WGI=1)` | The hint is set, but no controller is on and paired |
| `mandos detectados al arrancar: 0 (WGI=sin poner)` | This fix is missing |

⚠ **This is the second time this hint has bitten in this catalogue** — the first was another game
with the exact same symptom — so it counts as a fixed step for every UWP port with SDL3: set it, and
check the controller through the log **before** calling the port done.

## Spanish: a 1 for a 6

Spanish **is already on the disc**: the game has six languages and loads one by index. CTRPad has no
language menu — that is *High Octane*'s, which is a 32-bit tree and cannot reach a console — so the
index is fixed where startup loads the file:

```c
// English=1
LOAD_LangFile(sdata->ptrBigfile1, 6); // 6 = espanol
```

That is the whole change. The entire package differs from the English one by **three bytes**.

It was tested on the PC first, with the same tree and the same code the package uses, because every
round trip to the console costs far more than a desktop build.

## Widescreen: 16:9 without stretching

Widescreen is **not inherited** from *High Octane*, for the same reason: 32-bit tree. It was ported
by hand behind the CMake option `CTR_WIDESCREEN`, **off by default**, so without it the package comes
out exactly as before.

How it works: the game still draws into its PlayStation canvas, but **the X row of the
view-projection matrix is squeezed** (`34/45`, which is 4:3 divided by the presentation aspect); when
that canvas is presented in 16:9, the scene gets its shape back and **more world fits in at the
sides**. The UI, which must not distort, is squeezed too — **each primitive about its own centre**.

The pieces, which is where the real work shows:

| Where | What |
|---|---|
| The primitive pusher | The matrix's X row, the frustum and the corner rays |
| Level drawing | The horizontal clip window: without widening it, the game discards exactly what is now visible |
| HUD and font | Two functions that squeeze each quad about its centre; and the text cursor advances unsqueezed and is squeezed when drawing, or the letters bunch up |
| Map, icons, gauges, scoreboard and the track preview frame | One by one |
| The presenter | The aspect, fixed at 16:9 |

⚠ **The trap that measures what transplanting from another tree really costs:** *High Octane*'s map
block **does not compile** in CTRPad, because it dereferences what is a **guest reference** here. It
has to be translated to CTRPad's accessors. The rule that came out of it: **pure coordinate
arithmetic transfers as it is; anything that touches the game's data has to be translated.**

**Performance: it costs nothing.** 2 000 frames at **29.91 FPS**, the same as 4:3, with the window
still at 1920×1080.

## 60 FPS

The game is from 1999 and its logic is tied to 30 frames a second. Taking it to 60 is **401 changes
across 60 files**, ported from *High Octane* with transplant tooling, behind the `CTR_NATIVE_60FPS`
option and **off at run time** unless asked for (`CTR_60FPS=1` or a `60fps.txt` in the data folder).

The pattern is nearly always the same: what was measured in frames goes through `FPS_DOUBLE`, and
what must happen once per 30 Hz frame skips every other frame (`timer & 1`). The interesting part is
the exceptions, and one of them was found because the user reported that **the trophy on the title
screen was missing**: animations at 60 FPS have twice the frames, so the index arrives doubled, and
whoever reads them has to treat the high half as the frame and the low bit as the blend with the
next. That other half of the change was missing, in the draw-queue executor; without it the read
went out of range and the model never appeared.

Measured on the console: **59.8 FPS**.

## The disc, in parts

Device Portal uploads pass through `D:\DevelopmentFiles`, and 578 MB will not fit in one go: HTTP
500. `tools/partir_disco.py` splits it into 150 MiB parts with an index beside them, and the game's
entry point (`CtrUwp_JoinDiscParts`) joins them on the next launch, recording it in the log. The
parts stay behind: they take space, but they are the backup.

## What is missing

So as not to promise what is not there:

- **Developer Mode suspension** is not solved here: coming back from Home, the game starts over. In
  another port in this catalogue that was solved by saving the machine as it goes to the background,
  but that needs a state serialiser CTRPad does not have.
- **Widescreen has fine UI work pending** on a few screens (the garage's stats panel overflows
  slightly).
- **The controller** works (the user confirmed it by playing), but rumble has not been looked at.
