# Building the port and getting it onto the console

*(Español: [INSTALL.es.md](INSTALL.es.md))*

Ten steps. Steps 1 to 5 are done once; from step 6 on, rebuilding the package is two commands.

## 0. Before you start: where the commands go

This guide is full of blocks like the ones below. **They are all commands you type yourself** in a
terminal, and each one says where from. If you have never used one, this section is everything you
need; if you have, skip it.

### The terminal: PowerShell

Everything here goes in **PowerShell**, the ordinary Windows terminal:

1. Press the **Windows** key.
2. Type `powershell`.
3. Press **Enter** on *Windows PowerShell*.

A window opens with a line ending in `>`. That is where you type the command and press **Enter**.

**Moving to a folder.** Almost every command is typed *from a particular folder*, usually this
repository's. Use `cd` and the path, in quotes if it has spaces:

```powershell
cd "C:\Users\you\Downloads\ctr-xbox"
```

**A shortcut that saves mistakes:** open the folder in File Explorer, click the address bar, type
`powershell` over whatever is there and press **Enter**.

⚠ Some commands are long and split across lines with a **backtick** (`` ` ``) at the end of each.
Copy them whole, backticks included.

### Administrator is not needed — and is better avoided

Nothing here needs "run as administrator". All of it was built and tested from an ordinary account.

> ⚠ And in one step, being administrator **breaks** it: the certificate in §5 is created in the
> store of whoever runs the command. Create it elevated and `signtool`, running as you, will not
> find it.
>
> The only thing that asks for administrator is the Visual Studio **installer**.

### Why the PowerShell commands carry `-ExecutionPolicy Bypass`

A freshly installed Windows **will not run `.ps1` files**: its policy is `Restricted`. The
`-ExecutionPolicy Bypass` lifts that **for that one command**, changing nothing on your system.
**PowerShell 7 (`pwsh`) is not needed** anywhere here.

### How to tell whether a command worked

The ones here end by saying what they did. To confirm, this answers `True` when the previous one
ended well:

```powershell
$?
```

---

## 1. What you need first

| | What for |
|---|---|
| **Visual Studio 2022** with the C++ tools **and the UWP component** | Building for `WindowsStore`. `makeappx` and `signtool`, which package and sign, come with the **Windows SDK** that its installer brings |
| **Python 3** | Applying the recipe. Standard library only |
| **Git** | The patch is applied with `git apply`, so CTRPad has to be **cloned**, not downloaded as a zip |
| **Your own disc** | An NTSC-U dump of `SCUS-94426`. The port wants it named `ctr-u.bin` |
| **An Xbox Series X in Developer Mode** | Installing the package |

---

## 2. The three things you have to fetch separately

None of the three is distributed in this repository, and all three are needed.

### 2.1 CTRPad

```powershell
git clone https://github.com/chrissotraidis/ctrpad.git C:\ctr\ctrpad
```

⚠ **Build it and run it on your PC first**, using the project's own instructions. If it does not run
on the PC it will not run on the console, and you would be debugging two things at once.

This recipe was made against commit **`76ad5fe`**. The patch checks what it expects before writing,
so if CTRPad moves underneath, it will tell you instead of corrupting the tree.

### 2.2 The UWP dependency bundle

The libraries a UWP app needs to have a window, input and OpenGL:
**[`worleydl/uwp-dep`](https://github.com/worleydl/uwp-dep)** (there are also branches in
`SternXD/uwp-dep`). That is where `opengl32.dll`, `libgallium_wgl.dll`, `libglapi.dll`, `dxil.dll`,
`z-1.dll` and `libuwp.dll` come from — that is **Mesa built for UWP**: a console has no OpenGL, so
the package brings it and Mesa translates to Direct3D 12.

What you pass to `-Dep` is the folder that has `bin\` inside it.

### 2.3 SDL3 for UWP, built by you

**[`XboxEmulationHub/SDL3-uwp`](https://github.com/XboxEmulationHub/SDL3-uwp)**, branch
`uwp-3.4.16`, built from `VisualC-WinRT\SDL-UWP.vcxproj` with `/p:PlatformToolset=v143`.

⚠ **The `SDL3.dll` from its release will not do**: it is built with the generic configuration, has
no dynamic loading, and its EGL looks for Linux library names.

⚠ **And it needs this repository's audio patch** (§4). Without it the game stops on the
presentation screen with the process alive and the CPU at 0%.

---

## 3. Applying the recipe

> **Where to type this:** in **PowerShell**, in an **ordinary** window (no administrator), from this
> repository's folder.

```powershell
python tools\aplicar.py C:\ctr\ctrpad --sdl3 C:\ctr\SDL3-uwp
```

It does three things and reports each one: applies the game patch (90 files, with `git apply`, which
is all or nothing), copies the WinRT entry point into `platform\uwp\`, and — with `--sdl3` — patches
the audio in your SDL3 checkout.

It is **idempotent**: running it twice changes nothing and says so. To see the steps without
touching anything:

```powershell
python tools\aplicar.py --list
```

---

## 4. The SDL3 audio patch

If you did not pass `--sdl3` in step 3, do it now: it has to be in place **before** you build SDL3.

```powershell
python tools\aplicar.py C:\ctr\ctrpad --sdl3 C:\ctr\SDL3-uwp
```

If your SDL3 copy is not a git repository, the script falls back to
`tools\arreglo_wasapi_deadlock.py`, which makes the same change checking the text before writing.

Then **rebuild SDL3** and copy its `SDL3.dll` into the bundle's `bin\` (§2.2), which is where
packaging takes it from.

---

## 5. A certificate, and your identity in the manifest

Developer Mode accepts self-signed packages. Make one and **note its subject and thumbprint**.

⚠ This is where not opening the window "as administrator" really matters (§0).

> **Where to type this:** in **PowerShell**, in an **ordinary** window, from any folder.

```powershell
$c = New-SelfSignedCertificate -Type Custom -Subject "CN=YourName" `
       -KeyUsage DigitalSignature -FriendlyName "UWP signing" `
       -CertStoreLocation "Cert:\CurrentUser\My" `
       -TextExtension @("2.5.29.37={text}1.3.6.1.5.5.7.3.3", "2.5.29.19={text}")
$c.Thumbprint     # this is what goes in -Certificado
```

And in `package\AppxManifest.xml`, change the three `CHANGE-ME`s:

```xml
<Identity Name="YOUR-PACKAGE-NAME" Publisher="CN=YourName" Version="1.0.0.0" ProcessorArchitecture="x64" />
...
<PublisherDisplayName>YourName</PublisherDisplayName>
```

- **`Publisher` has to be the exact subject of your certificate.** `construir-uwp.ps1` compares them
  **before** compiling and stops if they differ, which beats finding out at signing time.
- A fresh GUID for `PhoneProductId`: `[guid]::NewGuid()`.

---

## 6. Tiles, and building

`package\Assets\` ships **empty on purpose**: the real package's tiles are the game's artwork.
[`ASSETS.md`](ASSETS.md) lists the thirteen names and sizes, and has a command that generates plain
ones in a moment.

> **Where to type this:** in **PowerShell**, in an **ordinary** window, from this repository's
> folder.

```powershell
powershell -ExecutionPolicy Bypass -File tools\construir-uwp.ps1 `
    -Arbol C:\ctr\ctrpad -Dep C:\ctr\uwp-dep -Version 1.0.0.0 -Certificado <your thumbprint> `
    -Panoramico -SesentaFps
```

It compiles, lays the package out with the libraries and your tiles, packages with `makeappx` and
signs with `signtool`. Out comes `CrashTeamRacing-<version>.msix` in `<tree>\paquete\`.

| Option | What it does |
|---|---|
| `-Panoramico` | Real 16:9 instead of 4:3 with bars. **It costs no frames** |
| `-SesentaFps` | Compiles the 60-frames-per-second mode. It ships **off**: you turn it on on the console (§9) |
| `-SoloEmpaquetar` | Skips the build and repackages what is already there |

⚠ **Bump the version for every new package.** The console will not replace a package whose version
matches the installed one, nor change its tiles.

---

## 7. Installing it on the console

### Before touching anything: how the console has to be

- **In Developer Mode**, with Dev Home installed. If it is not, that is a separate errand with
  Microsoft and this guide does not cover it. - **On, and with your profile signed in.** ⚠ With
  no user signed in the console **will not launch apps**: the package installs, shows up in the
  list, and launching it does nothing. This is one of the most expensive things to work out on
  your own. - **On the same network as your PC.** - **Its address**, which **Dev Home** shows
  on the console. The Device Portal listens on port **11443** over HTTPS. - **The portal's
  username and password**: the ones you set in **Dev Home → Remote Access Settings** when you
  turned remote access on.

### 7.1 Uploading it

Open `https://<console-ip>:11443` in your PC's browser.

⚠ The browser will warn that **the site's certificate is not trusted**. That is normal: the
certificate belongs to the console, which issues it itself. Go in anyway — in Edge and Chrome,
**Advanced** → **Continue to … (unsafe)**; in Firefox, **Advanced** → **Accept the Risk and
Continue**. Then it asks for the portal's username and password (the ones you set in Dev Home).

Once in, under **My games & apps → Add**:

1. **App package** → your `.msix`.
2. **Certificate** → not needed: the package is signed and Developer Mode accepts it.
3. **Next → Install**, and wait for *Package successfully registered*.

> **The console will not ask you for the certificate you signed with.** In Developer Mode it
> installs any signed package: the **Add** screen has no field for it. The certificate was needed on
> your PC, to sign (§5). Just in case, `construir-uwp.ps1` leaves a `firma.cer` beside the package.

### 7.2 The VCLibs dependency

The manifest declares `Microsoft.VCLibs.140.00`, and **without that line activation fails with
`0x8027025B`** with no further explanation. Putting the DLLs inside the package does **not** fix it:
it has to be the framework package.

It is usually already on the console, installed by any other development package. If it says it is
missing, add it once on the **Add** screen → **Optional packages / Dependency**, with the Windows
SDK's `Microsoft.VCLibs.x64.14.00.appx`:

```text
C:\Program Files (x86)\Microsoft SDKs\Windows Kits\10\ExtensionSDKs\Microsoft.VCLibs\14.0\Appx\Retail\x64\Microsoft.VCLibs.x64.14.00.appx
```

⚠ The `…Desktop.appx` is not it (that is the desktop bridge one), and neither is the one in `Debug`.

### 7.3 If it says `There is not enough space on the disk`

The console is not full. **The first install of a package family goes to `D:\DevelopmentFiles`**, a
partition of about 5 GB; *updates* go elsewhere, and uninstalling does not empty it. The way out is
to install a *seed* first — same identity, lower version, minimal executable — and then the real
one, which goes in as an update.

---

## 8. The disc

The disc does **not** go inside the package: it is uploaded once into the app's data folder. The
first launch creates that folder; upload before it and the portal says it cannot find the path.

```text
…\LocalState\chrissotraidis\CTRPad\CTRPad\assets\
```

The portal answers **500** when you upload 578 MB in one go (its uploads pass through
`D:\DevelopmentFiles`), so the disc goes up split and the game joins it on the next launch:

> **Where to type this:** in **PowerShell**, in an **ordinary** window, from this repository's
> folder.

```powershell
python tools\partir_disco.py "C:\path\to\your\disc.bin" C:\ctr\parts 150 ctr-u.bin
```

Out come `ctr-u.bin.001`, `.002`, … and a `ctr-u.bin.partes` with the count. **Upload all of them**,
the `.partes` included, with the Device Portal's **File explorer**, into that `assets` folder. On the
next launch the game joins them and leaves the whole `ctr-u.bin`.

⚠ The name has to be exactly `ctr-u.bin`: with any other, the port will not find it.

---

## 9. 60 FPS and the language

**60 FPS ships off** even if you built with `-SesentaFps`. There are two ways to turn it on, and on a
console it is the second:

| How | Where |
|---|---|
| The `CTR_60FPS=1` variable | On a PC, before launching |
| An empty file named `60fps.txt` | In the game's data folder, next to `assets\`. Upload it with the portal's **File explorer** |

**The language** is compiled in: Spanish is already on the disc, and the patch loads index 6 instead
of 1. To go back to English you change that number and build another package — it is in the patch,
and [`HOW-IT-WORKS.md`](HOW-IT-WORKS.md) says where.

Read `Crash Team Racing.log` in the data folder. On a console it is all you have, and it is where the
frame rate, the detected controllers and the disc joining show up.

---

## 10. Removing it from the console

⚠ **Your saves and your disc go with it.** Both live in the package's `LocalState`. To keep them,
download them first with the Device Portal's **File explorer**.

To uninstall: **My games & apps**, find the game in the list, and **Remove**. Nothing on your PC is
touched.

If what you want is to **update** without losing anything, do not uninstall: install a package with a
**higher version** and the same identity on top. That way you do not have to upload the disc again.

---

## If something goes wrong

| Symptom | Cause |
|---|---|
| The package installs and launching does nothing | Is a **profile signed in** on the console? With no user signed in it will not launch apps |
| Activation fails with `0x8027025B` | The VCLibs dependency is missing (§7.2) |
| Install aborts with `-2147009293` | The `TargetDeviceFamily` `MinVersion` is higher than the console's. The manifest keeps it low on purpose |
| Stuck on the presentation screen, process alive, CPU at 0% | The SDL3 audio patch is missing (§4). The game waits for a voice line, and with no audio that loop never ends |
| No button does anything | The Windows.Gaming.Input hint is missing, which the WinRT entry point sets. The log says it: `mandos detectados al arrancar: 0 (WGI=sin poner)` |
| `There is not enough space on the disk` | It is not full: it is `D:\DevelopmentFiles` (§7.3) |
| HTTP 500 uploading the disc | It has to be split (§8) |
| It boots but finds no disc | The name has to be `ctr-u.bin`, and the parts `ctr-u.bin.001`… with their `.partes` (§8) |
| Widescreen shows bars | The package was not built with `-Panoramico` (§6) |
| It runs at 30 FPS | That is normal: 60 is compiled with `-SesentaFps` and turned on with `60fps.txt` (§9) |
| Signing fails | The manifest's `Publisher` is not the exact subject of your certificate (§5), or the certificate was created in an administrator window (§0) |
