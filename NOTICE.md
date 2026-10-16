# Notice

*(Español: [NOTICE.es.md](NOTICE.es.md))*

## Not affiliated

This is an unofficial, noncommercial fan project. It is **not affiliated with, endorsed by or
connected to Sony Interactive Entertainment, Naughty Dog, Activision or Microsoft**, or any of their
subsidiaries, nor to the authors of the [CTR-ModSDK](https://github.com/CTR-tools/CTR-ModSDK)
decompilation, of [CTR Native](https://github.com/CTR-tools/ctr-native), of
[CTRPad](https://github.com/chrissotraidis/ctrpad) or of
[CTR: High Octane](https://github.com/Rinnegatamante/Crash-Team-Racing-High-Octane). *Crash Team
Racing*, *Xbox* and all related names and marks are the property of their respective owners, and are
used here only to say what this works with.

Nothing here is for sale, and nothing here is monetized.

## What this repository does not distribute

No disc image. No game assets. No built executable. No `.msix` package. No save data. No artwork,
audio, music or fonts from the game — not even the package tiles, which is why `package/Assets/` is
empty and [`docs/ASSETS.md`](docs/ASSETS.md) asks you to supply your own.

**And none of the UWP libraries.** `SDL3.dll`, Mesa's `opengl32.dll` and the rest of the bundle are
other people's binaries: the guide says where to get them and how to build them, and they are not
copied here.

Nothing here produces a playable game on its own. You need your own legally dumped copy of the disc
and a working build of CTRPad, neither of which this repository provides or can provide.

## What it does contain of other people's work

**A patch against CTRPad.** `patches/ctr-uwp-port.patch` is a `git diff` against commit `76ad5fe` of
[chrissotraidis/ctrpad](https://github.com/chrissotraidis/ctrpad), and like any diff it quotes the
context lines around each change. CTRPad is **GPL-3.0**, as are CTR Native and the ModSDK
decompilation it comes from, and the GPL is written precisely so that a derivative like this one can
exist and be shared: this repository is released under [that same license](LICENSE).

**Widescreen and 60 FPS come from CTR: High Octane** (also GPL-3.0), ported by hand onto CTRPad
rather than merged, because High Octane is a 32-bit tree and a console needs 64-bit. What that
means in practice: the pure coordinate arithmetic transfers as it is, and anything that touches the
game's data had to be translated to CTRPad's accessors — High Octane's `UI_Map.c` block does not
even compile here, because it dereferences what CTRPad models as a guest reference. 401 of those
changes are the 60 FPS work, across 60 files.

**The SDL3 patch.** `patches/sdl3-uwp-audio-wasapi.patch` changes three files of
[SDL3-uwp](https://github.com/XboxEmulationHub/SDL3-uwp)'s WASAPI backend. SDL3 is **zlib**-licensed,
which allows modified versions; the patch is a diff against its own source, applied to your copy and
never distributed as a binary.

**There are no screenshots here at all.** A screenshot of this running would be mostly someone
else's artwork.

## Takedown and contact

If you hold rights in this material and want something here removed or changed, write to
**jajdpmail@gmail.com**, saying what you object to and in what capacity you are writing.

Requests from rights holders are honoured: the disputed part is removed, or the repository is taken
down, without argument, and you will get a reply confirming it. No notice or legal process beyond
that email is needed to reach the person who maintains this.
