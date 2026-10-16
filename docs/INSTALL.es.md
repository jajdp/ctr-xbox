# Construir el port y meterlo en la consola

*(English: [INSTALL.md](INSTALL.md))*

Diez pasos. Del 1 al 5 se hacen una sola vez; a partir del 6, rehacer el paquete son dos órdenes.

## 0. Antes de empezar: dónde se escriben las órdenes

Esta guía está llena de bloques como este. **Todos son órdenes que tecleas tú** en una ventana de
terminal, y cada uno dice arriba desde dónde. Si nunca has usado una, aquí está todo lo que hace
falta saber; si ya sabes, sáltate esta sección.

### La terminal: PowerShell

Todo lo de esta guía va en **PowerShell**, la terminal normal de Windows:

1. Pulsa la tecla **Windows**.
2. Escribe `powershell`.
3. Pulsa **Enter** sobre *Windows PowerShell*.

Se abre una ventana con una línea que acaba en `>`. Ahí escribes la orden y pulsas **Enter**.

**Moverte a una carpeta.** Casi todas las órdenes se escriben *desde una carpeta concreta*,
normalmente la de este repositorio. Para ir a ella se usa `cd` y la ruta, entre comillas si tiene
espacios:

```powershell
cd "C:\Users\tu-usuario\Downloads\ctr-xbox"
```

**Un atajo que ahorra errores:** abre la carpeta en el Explorador de archivos, haz clic en la barra
de direcciones, escribe `powershell` encima de lo que ponga y pulsa **Enter**. Se abre PowerShell ya
situado ahí.

⚠ Algunas órdenes son largas y se parten en varias líneas con una **comilla invertida** (`` ` ``) al
final de cada una. Cópialas enteras, con esas comillas: son las que dicen «sigue en la línea de
abajo».

### No hace falta administrador — y es mejor no usarlo

Nada de esta guía necesita «ejecutar como administrador». Todo se construyó y se probó con una
cuenta normal.

> ⚠ Y en un paso concreto, ser administrador lo **estropea**: el certificado del §5 se crea en el
> almacén del usuario que ejecuta la orden. Si lo creas en una ventana elevada, acaba en el almacén
> del administrador, y al firmar —que harás como tú— `signtool` no lo encuentra.
>
> Lo único que pide administrador es el **instalador** de Visual Studio, que lo pide él solo.

### Por qué las órdenes de PowerShell llevan `-ExecutionPolicy Bypass`

Un Windows recién instalado **no ejecuta archivos `.ps1`**: su política está en `Restricted`. El
`-ExecutionPolicy Bypass` de los ejemplos levanta esa restricción **solo para esa orden**, sin
cambiar nada en tu sistema. **PowerShell 7 (`pwsh`) no hace falta** para nada de aquí.

### Cómo saber si una orden funcionó

Las de esta guía terminan diciendo qué hicieron, y si algo va mal lo dicen también. Para confirmar,
esto responde `True` cuando la anterior terminó bien:

```powershell
$?
```

---

## 1. Lo que hace falta antes

| | Para qué |
|---|---|
| **Visual Studio 2022** con las herramientas de C++ **y el componente de UWP** | Compilar para `WindowsStore`. El `makeappx` y el `signtool` que empaquetan y firman vienen con el **Windows SDK**, que el instalador trae |
| **Python 3** | Aplicar la receta. Nada más que la biblioteca estándar |
| **Git** | El parche se aplica con `git apply`, así que CTRPad tiene que estar **clonado**, no descargado como zip |
| **Tu propio disco** | Un volcado NTSC-U de `SCUS-94426`. El port lo quiere con el nombre `ctr-u.bin` |
| **Una Xbox Series en modo desarrollador** | Instalar el paquete |

---

## 2. Las tres cosas que hay que traer aparte

Ninguna de las tres se distribuye en este repositorio, y las tres hacen falta.

### 2.1 CTRPad

```powershell
git clone https://github.com/chrissotraidis/ctrpad.git C:\ctr\ctrpad
```

⚠ **Compílalo y pruébalo en tu PC primero**, con las instrucciones del propio proyecto. Si no corre
en el PC, no va a correr en la consola, y tendrías dos problemas a la vez en vez de uno.

Esta receta se hizo contra el commit **`76ad5fe`**. El parche comprueba lo que espera encontrar
antes de escribir, así que si CTRPad cambia por debajo, te lo dirá en vez de estropear el árbol.

### 2.2 El bundle de dependencias de UWP

Las bibliotecas que una aplicación UWP necesita para tener ventana, entrada y OpenGL:
**[`worleydl/uwp-dep`](https://github.com/worleydl/uwp-dep)** (también hay ramas en
`SternXD/uwp-dep`). De ahí salen `opengl32.dll`, `libgallium_wgl.dll`, `libglapi.dll`, `dxil.dll`,
`z-1.dll` y `libuwp.dll`, que es **Mesa compilado para UWP**: la consola no tiene OpenGL, así que lo
trae el paquete y Mesa lo traduce a Direct3D 12.

Lo que le pasas luego a `-Dep` es la carpeta que tiene `bin\` dentro.

### 2.3 SDL3 para UWP, compilado por ti

**[`XboxEmulationHub/SDL3-uwp`](https://github.com/XboxEmulationHub/SDL3-uwp)**, rama
`uwp-3.4.16`, compilado desde `VisualC-WinRT\SDL-UWP.vcxproj` con `/p:PlatformToolset=v143`.

⚠ **El `SDL3.dll` que publica su release no sirve**: está compilado con la configuración genérica,
no trae carga dinámica y su EGL busca nombres de Linux.

⚠ **Y necesita el parche del audio** de este repositorio (§4). Sin él, el juego se queda en la
pantalla de presentación con el proceso vivo y la CPU al 0 %.

---

## 3. Aplicar la receta

> **Dónde se escribe:** en **PowerShell**, en una ventana **normal** (no hace falta
> administrador), desde la carpeta de este repositorio.

```powershell
python tools\aplicar.py C:\ctr\ctrpad --sdl3 C:\ctr\SDL3-uwp
```

Hace tres cosas y dice qué hizo cada una: aplica el parche del juego (90 archivos, con `git apply`,
que es todo o nada), copia la entrada WinRT a `platform\uwp\`, y —con `--sdl3`— parchea el audio de
tu copia de SDL3.

Es **idempotente**: pasarlo dos veces no cambia nada y lo dice. Para ver los pasos sin tocar nada:

```powershell
python tools\aplicar.py --list
```

---

## 4. El parche del audio de SDL3

Si en el paso 3 no pasaste `--sdl3`, hazlo ahora: tiene que estar **antes** de compilar SDL3.

```powershell
python tools\aplicar.py C:\ctr\ctrpad --sdl3 C:\ctr\SDL3-uwp
```

Si tu copia de SDL3 no es un repositorio git, el script usa `tools\arreglo_wasapi_deadlock.py`, que
hace el mismo cambio comprobando el texto antes de escribir.

Después, **vuelve a compilar SDL3** y copia su `SDL3.dll` al `bin\` del bundle (§2.2), que es de
donde lo toma el empaquetado.

---

## 5. Un certificado, y tu identidad en el manifiesto

El modo desarrollador acepta paquetes autofirmados. Crea uno y **apunta su sujeto y su huella**.

⚠ Aquí importa de verdad lo de **no** abrir la ventana «como administrador» (§0).

> **Dónde se escribe:** en **PowerShell**, en una ventana **normal**, desde cualquier carpeta.

```powershell
$c = New-SelfSignedCertificate -Type Custom -Subject "CN=TuNombre" `
       -KeyUsage DigitalSignature -FriendlyName "Firma UWP" `
       -CertStoreLocation "Cert:\CurrentUser\My" `
       -TextExtension @("2.5.29.37={text}1.3.6.1.5.5.7.3.3", "2.5.29.19={text}")
$c.Thumbprint     # esto es lo que se pasa en -Certificado
```

Y en `package\AppxManifest.xml`, cambia los tres `CHANGE-ME`:

```xml
<Identity Name="TU-NOMBRE-DE-PAQUETE" Publisher="CN=TuNombre" Version="1.0.0.0" ProcessorArchitecture="x64" />
...
<PublisherDisplayName>TuNombre</PublisherDisplayName>
```

- **`Publisher` tiene que ser el sujeto exacto de tu certificado.** `construir-uwp.ps1` lo compara
  **antes** de compilar y se detiene si no coinciden, que es mejor que enterarse al firmar.
- Un GUID nuevo para `PhoneProductId`: `[guid]::NewGuid()`.

---

## 6. Los mosaicos, y compilar

`package\Assets\` viene **vacía a propósito**: los mosaicos del paquete real son arte del juego.
[`ASSETS.es.md`](ASSETS.es.md) dice los trece nombres y medidas, y trae una orden que los genera
lisos en un momento.

> **Dónde se escribe:** en **PowerShell**, en una ventana **normal**, desde la carpeta de este
> repositorio.

```powershell
powershell -ExecutionPolicy Bypass -File tools\construir-uwp.ps1 `
    -Arbol C:\ctr\ctrpad -Dep C:\ctr\uwp-dep -Version 1.0.0.0 -Certificado <tu huella> `
    -Panoramico -SesentaFps
```

Compila, monta el layout con las bibliotecas y tus mosaicos, empaqueta con `makeappx` y firma con
`signtool`. Sale `CrashTeamRacing-<versión>.msix` en `<árbol>\paquete\`.

| Opción | Qué hace |
|---|---|
| `-Panoramico` | 16:9 de verdad en vez de 4:3 con bandas. **No cuesta FPS** |
| `-SesentaFps` | Compila el modo de 60 imágenes por segundo. Viene **apagado**: se enciende en la consola (§9) |
| `-SoloEmpaquetar` | Salta la compilación y vuelve a empaquetar lo que ya hay |

⚠ **La versión sube en cada paquete nuevo.** La consola no reemplaza un paquete por otro de la
misma versión, ni cambia sus mosaicos.

---

## 7. Instalarlo en la consola

### Antes de tocar nada: cómo tiene que estar la consola

- **En modo desarrollador**, con Dev Home instalado. Si no lo está, eso es un trámite aparte
  con Microsoft y no lo cubre esta guía. - **Encendida y con tu perfil iniciado.** ⚠ Sin un
  usuario conectado, la consola **no abre aplicaciones**: el paquete se instala, aparece en la
  lista y al lanzarlo no pasa nada. Es de las cosas que más tiempo cuestan averiguar. - **En la
  misma red que tu PC.** - **Su dirección**, que te la dice **Dev Home** en la propia consola.
  El Device Portal escucha en el puerto **11443** por HTTPS. - **Usuario y contraseña del
  portal**: los que definiste en **Dev Home → Remote Access Settings** al activar el acceso
  remoto.

### 7.1 Subirlo

Abre `https://<ip-de-la-consola>:11443` en el navegador de tu PC.

⚠ El navegador avisará de que **el certificado del sitio no es de confianza**. Es normal y no
es un problema: ese certificado es de la propia consola, que se lo hace ella. Entra de todas
formas — en Edge y en Chrome, **Avanzado** → **Continuar a … (no seguro)**; en Firefox,
**Avanzado** → **Aceptar el riesgo y continuar**. Después te pedirá el usuario y la contraseña
del portal (los que definiste en Dev Home).

Ya dentro, en **My games & apps → Add**:

1. **App package** → tu `.msix`.
2. **Certificate** → no hace falta: el paquete va firmado y el modo desarrollador lo acepta.
3. **Next → Install**, y esperar al *Package successfully registered*.

> **La consola no te va a pedir el certificado con el que firmaste.** En modo desarrollador instala
> cualquier paquete que venga firmado: la pantalla **Add** ni siquiera tiene casilla para él. El
> certificado hizo falta en tu PC, para firmar (§5), y ahí se acaba su papel. Por si acaso,
> `construir-uwp.ps1` deja un `firma.cer` junto al paquete.

### 7.2 La dependencia de VCLibs

El manifiesto declara `Microsoft.VCLibs.140.00`, y **sin esa línea la activación falla con
`0x8027025B`** sin más explicación. Metiendo las DLL dentro del paquete **no** se arregla: tiene que
ser el paquete de marco.

Normalmente ya está en la consola, porque lo instala cualquier otro paquete de desarrollo. Si dice
que falta, se añade una vez en la pantalla **Add** → **Optional packages / Dependency**, con el
`Microsoft.VCLibs.x64.14.00.appx` del Windows SDK:

```text
C:\Program Files (x86)\Microsoft SDKs\Windows Kits\10\ExtensionSDKs\Microsoft.VCLibs\14.0\Appx\Retail\x64\Microsoft.VCLibs.x64.14.00.appx
```

⚠ No vale el `…Desktop.appx` (ese es el del puente de escritorio) ni el de la carpeta `Debug`.

### 7.3 Si sale `There is not enough space on the disk`

No es que la consola esté llena. **La primera instalación de una familia de paquetes va a
`D:\DevelopmentFiles`**, una partición de unos 5 GB; las *actualizaciones* van a otro
almacenamiento, y desinstalar no la vacía. La salida es instalar primero una *semilla* —un paquete
con la misma identidad, versión más baja y un ejecutable mínimo— y después el de verdad, que entra
como actualización.

---

## 8. El disco

El disco **no va dentro del paquete**: se sube una sola vez a la carpeta de datos de la aplicación.
El primer arranque la crea; si subes antes, el portal dice que no encuentra la ruta.

```text
…\LocalState\chrissotraidis\CTRPad\CTRPad\assets\
```

El portal responde **500** al subir los 578 MB de una vez (sus subidas pasan por
`D:\DevelopmentFiles`), así que el disco va partido y el juego lo une él solo en el arranque
siguiente:

> **Dónde se escribe:** en **PowerShell**, en una ventana **normal**, desde la carpeta de este
> repositorio.

```powershell
python tools\partir_disco.py "C:\ruta\a\tu\disco.bin" C:\ctr\partes 150 ctr-u.bin
```

Salen `ctr-u.bin.001`, `.002`, … y un `ctr-u.bin.partes` con la cuenta. **Súbelos todos**, incluido
el `.partes`, con el **File explorer** del Device Portal, a esa carpeta `assets`. En el arranque
siguiente el juego los une (`Uniendo N trozos del disco…` en el registro) y deja el `ctr-u.bin`
entero.

⚠ El nombre tiene que ser exactamente `ctr-u.bin`: con otro, el port no lo encuentra.

---

## 9. Los 60 FPS y el idioma

**Los 60 FPS vienen apagados** aunque hayas compilado con `-SesentaFps`. Se encienden de dos
maneras, y la que sirve en una consola es la segunda:

| Cómo | Dónde |
|---|---|
| La variable `CTR_60FPS=1` | En un PC, antes de arrancar el juego |
| Un archivo vacío llamado `60fps.txt` | En la carpeta de datos del juego, junto a `assets\`. Se sube con el **File explorer** del portal |

**El idioma** va compilado dentro: el castellano ya está en el disco y el parche carga el índice 6
en vez del 1. Para volver al inglés hay que cambiar ese número y compilar otro paquete — está en el
parche, y [`HOW-IT-WORKS.es.md`](HOW-IT-WORKS.es.md) dice dónde.

Lee `Crash Team Racing.log` en la carpeta de datos: en una consola es lo único que tienes, y es
donde salen los FPS, los mandos detectados y la unión del disco.

---

## 10. Quitarlo de la consola

⚠ **Se van tus partidas y tu disco.** Los dos viven en el `LocalState` del paquete. Si quieres
conservarlos, bájalos antes con el **File explorer** del Device Portal.

Para desinstalar: **My games & apps**, busca el juego en la lista, y **Remove**. Nada de tu PC se
toca.

Si lo que quieres es **actualizar** sin perder nada, no desinstales: instala encima un paquete con
una **versión mayor** y la misma identidad. Así no hay que volver a subir el disco.

---

## Si algo no sale bien

| Síntoma | Causa |
|---|---|
| El paquete instala y al abrirlo no pasa nada | ¿Hay un **perfil iniciado** en la consola? Sin usuario conectado no abre aplicaciones |
| La activación falla con `0x8027025B` | Falta la dependencia de VCLibs (§7.2) |
| La instalación aborta con `-2147009293` | El `MinVersion` del `TargetDeviceFamily` es mayor que la versión de la consola. El manifiesto lo deja bajo a propósito |
| Se queda en la pantalla de presentación, el proceso vivo y la CPU al 0 % | Falta el parche del audio de SDL3 (§4). El juego espera a que termine una voz, y sin audio ese bucle no acaba nunca |
| No responde a ningún botón | Falta la pista de Windows.Gaming.Input, que pone la entrada WinRT. El registro lo dice: `mandos detectados al arrancar: 0 (WGI=sin poner)` |
| `There is not enough space on the disk` | No está llena: es `D:\DevelopmentFiles` (§7.3) |
| HTTP 500 al subir el disco | Hay que partirlo (§8) |
| Arranca pero no encuentra el disco | El nombre tiene que ser `ctr-u.bin`, y las partes `ctr-u.bin.001`… con su `.partes` (§8) |
| El 16:9 sale con bandas | El paquete no se compiló con `-Panoramico` (§6) |
| Va a 30 FPS | Lo normal: los 60 se compilan con `-SesentaFps` y se encienden con `60fps.txt` (§9) |
| Falla al firmar | El `Publisher` del manifiesto no es el sujeto exacto de tu certificado (§5), o el certificado se creó en una ventana de administrador (§0) |
