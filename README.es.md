# Crash Team Racing en la Xbox — el port UWP

Cómo coger [CTRPad](https://github.com/chrissotraidis/ctrpad) —el port nativo de *Crash Team
Racing* (PlayStation, 1999, `SCUS-94426`) a 64 bits de verdad, sobre la decompilación de
[CTR-ModSDK](https://github.com/CTR-tools/CTR-ModSDK)— y hacerlo correr **en una Xbox Series X en modo
desarrollador**, como un paquete UWP que compilas y firmas tú.

*(English: [README.md](README.md))*

No es una teoría: el juego arranca, suena, pasa la presentación de Sony y la intro de Nitros Oxide,
se navega con mando y corre a **32,9 FPS** —los del juego original—, en **16:9 a pantalla completa**,
**en español** y, si lo pides, **a 60 imágenes por segundo**. Está instalado y probado en dos
consolas.

## En qué consola se probó

**En una Xbox Series X**, en modo desarrollador. Las dos consolas en las que se construyó y se probó esto
son Series X, así que es el único hardware al que se refiere cualquier cosa que se afirme aquí.

**En una Series S no se ha probado nunca, ni una vez.** Es otra máquina: menos memoria disponible para un
juego y una GPU más floja. Puede que funcione en una, puede que vaya más despacio, o puede que no
arranque; nada de aquí se ha medido en ella. Si lo ejecutas en una Series S, lo que obtengas no es lo que
dice este README, y ninguna de las cifras de aquí es una promesa sobre esa consola.

## Qué es este repositorio

**Una receta y las herramientas que la aplican.** CTRPad no tiene nada de UWP: aquí está lo que hubo
que añadirle para que una consola lo ejecute, más tres cosas que el port gana por el camino y que
van detrás de opciones de CMake. Todo se aplica **a tu propia copia** de CTRPad, en tu máquina.

| Pieza | Qué es |
|---|---|
| `patches/ctr-uwp-port.patch` | El parche del juego: 90 archivos. El port UWP, el panorámico, los 60 FPS y el idioma |
| `src/uwp/ctr_uwp_main.cpp` | La entrada WinRT: pide el mando por Windows.Gaming.Input y une el disco partido |
| `patches/sdl3-uwp-audio-wasapi.patch` | El interbloqueo del audio de SDL3 en WinRT, sin el cual el juego **no pasa de la pantalla de presentación**. Sirve para cualquier port UWP con SDL3 |
| `tools/` | El orquestador, el script que compila/empaqueta/firma y el partidor del disco |

## Qué **no** es

Aquí no hay **código del juego, ni imagen del disco, ni ejecutable compilado, ni paquete `.msix`, ni
las bibliotecas de UWP, ni arte**. Esto no produce un juego jugable por sí solo. Necesitas tu propia
copia volcada legalmente del disco y CTRPad compilando en tu PC antes de empezar. Está detallado en
[`NOTICE.es.md`](NOTICE.es.md).

Los mosaicos del paquete **tampoco**: los del paquete real se hicieron con arte del juego, que es de
sus dueños. Los tuyos los pones tú —[`docs/ASSETS.es.md`](docs/ASSETS.es.md) dice los tamaños, y el
script se detiene si la carpeta está vacía.

## Qué hace falta antes

| | |
|---|---|
| CTRPad | [chrissotraidis/ctrpad](https://github.com/chrissotraidis/ctrpad), **clonado con git** (el parche se aplica con `git apply`) y compilando en tu PC primero |
| Tu propio disco | Un volcado NTSC-U de `SCUS-94426` como `ctr-u.bin` |
| Visual Studio | 2022, con las herramientas de C++ **y el componente de UWP**: aquí empaqueta `makeappx` y firma `signtool`, los dos del Windows SDK |
| El bundle de UWP | SDL3, Mesa y `libuwp` compilados para UWP: [`worleydl/uwp-dep`](https://github.com/worleydl/uwp-dep). No se distribuyen aquí ([`docs/INSTALL.es.md`](docs/INSTALL.es.md) §2) |
| SDL3 para UWP | [`XboxEmulationHub/SDL3-uwp`](https://github.com/XboxEmulationHub/SDL3-uwp), **compilado por ti y con el parche del audio**: el `SDL3.dll` de su release no sirve (§2 de la guía) |
| PowerShell | La que Windows ya trae: **PowerShell 7 no hace falta** |
| Python 3 | Para aplicar la receta. Nada más que la biblioteca estándar |
| Una Xbox en modo desarrollador | Y un certificado con el que firmar: uno autofirmado sirve |

## Cómo va

Dos órdenes. La §0 de [`docs/INSTALL.es.md`](docs/INSTALL.es.md) explica la terminal con calma, y el
resto de esa guía es la versión larga.

> **Dónde se escribe esto:** en **PowerShell** —pulsa la tecla **Windows**, escribe `powershell` y
> pulsa **Enter**—, en una ventana **normal**: no hace falta «ejecutar como administrador», y usarlo
> además rompería la firma, porque el certificado vive en el almacén del usuario que ejecuta la
> orden. Desde la carpeta de este repositorio.

```powershell
# 1. aplicar la receta a tu copia de CTRPad (y, con --sdl3, el parche del audio)
python tools\aplicar.py C:\ctr\ctrpad --sdl3 C:\ctr\SDL3-uwp

# 2. compilar, empaquetar y firmar
powershell -ExecutionPolicy Bypass -File tools\construir-uwp.ps1 `
    -Arbol C:\ctr\ctrpad -Dep C:\ctr\uwp-dep -Version 1.0.0.0 -Certificado <tu huella> -Panoramico
```

`python tools\aplicar.py --list` dice qué hace cada paso.

Después, instalar el `.msix` por el Device Portal y subir tu disco **partido** al `LocalState` de la
aplicación. Paso a paso, con el lado de la consola:
**[`docs/INSTALL.es.md`](docs/INSTALL.es.md)**.

## Qué hubo que resolver

Cada una de estas cosas fue un fallo real en la consola. El detalle, con lo que decía el registro y
lo que se midió, está en **[`docs/HOW-IT-WORKS.es.md`](docs/HOW-IT-WORKS.es.md)**.

| | Síntoma | Arreglo |
|---|---|---|
| 1 | Se quedaba en la presentación, proceso vivo y CPU al 0 % | No era el disco: el juego espera a que suene una voz, y el audio nunca abría. `WASAPI_ActivateDevice` llamaba a `WASAPI_PrepDevice` **desde el propio hilo de gestión de WASAPI**, y la comprobación que debía detectarlo no reconocía ese hilo: la tarea se encolaba esperando al hilo que ya la estaba ejecutando |
| 2 | La activación fallaba con `0x8027025B` | Faltaba la dependencia de VCLibs en el manifiesto. Meter las DLL dentro del paquete **no** la sustituye |
| 3 | No respondía a ningún botón | En WinRT los mandos llegan por **Windows.Gaming.Input**, y su driver se desactiva solo si la aplicación no pide la pista `SDL_HINT_JOYSTICK_WGI`. Una línea en la entrada. Es la segunda vez que esta pista muerde en este catálogo |
| 4 | El disco no subía: HTTP 500 | Las subidas del portal pasan por `D:\DevelopmentFiles`, que es pequeño. Va en trozos de 150 MiB y el juego los une en el arranque siguiente |
| 5 | El juego en inglés | El castellano ya está en el disco: solo había que pedirlo. Un `1` por un `6` donde se carga el archivo de idioma |
| 6 | 4:3 con bandas | El 16:9 de *High Octane* portado a mano a CTRPad: la fila X de la matriz de vista-proyección se comprime y la interfaz se compensa primitiva a primitiva. **No cuesta FPS** |
| 7 | 30 FPS, como la PlayStation | Los 60 FPS de *High Octane*: 401 cambios sobre 60 archivos, con herramientas de trasplante. **59,8 FPS** medidos en la consola; apagado de fábrica |

## Créditos y licencia

Port y herramientas de **Recompilaciones**. Publicado bajo la [GPL-3.0-or-later](LICENSE), la misma
licencia de CTRPad y de CTR Native, de los que esto es un derivado. El panorámico y los 60 FPS están
portados de [CTR: High Octane](https://github.com/Rinnegatamante/Crash-Team-Racing-High-Octane)
(GPL-3.0) con los cambios que CTRPad necesitaba; el detalle, en
[`NOTICE.es.md`](NOTICE.es.md).

Los comentarios del código y de los scripts van en español, que es donde se escribieron. La
documentación está en los dos idiomas.

*Crash Team Racing* es © Sony Interactive Entertainment / Naughty Dog. Este proyecto no está
afiliado a ellos, ni a Microsoft, ni a los autores de la decompilación, de CTR Native, de CTRPad o
de High Octane, y no distribuye nada que les pertenezca. Quien tenga derechos sobre este material
puede escribir a **jajdpmail@gmail.com**.
