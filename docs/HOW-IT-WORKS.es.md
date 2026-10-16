# Cómo funciona, y por qué cada cosa está ahí

*(English: [HOW-IT-WORKS.md](HOW-IT-WORKS.md))*

Cada pieza de este repositorio salió de un fallo concreto en una consola de verdad. Esto cuenta cuál
fue, cómo se encontró y qué lo arregló. Si solo quieres construirlo,
[`INSTALL.es.md`](INSTALL.es.md) basta.

## De dónde sale

El camino hasta aquí tiene tres eslabones, y cada uno resuelve lo que el anterior no podía:

| | |
|---|---|
| [CTR-ModSDK](https://github.com/CTR-tools/CTR-ModSDK) | La decompilación del juego, alrededor del 73 % |
| [CTR Native](https://github.com/CTR-tools/ctr-native) | El port nativo a PC, con SDL3 y OpenGL 3.3. Es de **32 bits**, porque el código del juego guarda punteros de la PlayStation en 32 bits |
| [CTRPad](https://github.com/chrissotraidis/ctrpad) | Lleva CTR Native a **64 bits de verdad**, con un modelo de memoria comprobado y referencias de invitado en vez de punteros crudos. Y eso es lo que hace posible una consola, donde 32 bits no es una opción |

Lo que añade este repositorio es el cuarto eslabón: que eso corra dentro de un App Container de
Xbox, con su ventana, su audio, su mando y su disco.

En la consola el juego dibuja con **OpenGL sobre Mesa compilado para UWP**, que lo traduce a
Direct3D 12, presentado por SDL3 en una ventana de 1920×1080; el audio sale por WASAPI a 44 100 Hz
estéreo; y el disco vive en el `LocalState` de la aplicación.

## Compilar y empaquetar: nueve tropiezos

Ninguno es interesante por sí mismo, pero juntos son la mitad del trabajo de un port UWP, y todos
vuelven a salir en el siguiente:

| | Síntoma | Causa y arreglo |
|---|---|---|
| 1 | `MSB8024: Using static version of the C++ runtime library is not supported` | UWP no admite el CRT estático, y el CMake de CTRPad lo fija para MSVC. En UWP pasa a `MultiThreadedDLL` |
| 2 | 102 errores dentro de `combaseapi.h` del SDK | `native_win32.h` define `NOUSER` para no pisar nombres del juego, y sin `winuser.h` el COM del SDK no compila. En UWP no se define |
| 3 | `missing ';' before identifier 'far'` en `objidl.h` | El mismo archivo hace `#undef far` / `#undef near`, y el COM que SDL incluye después usa `FAR`/`NEAR`. En UWP se redefinen vacías tras el `#undef` |
| 4 | `WRL requires C++ compilation (use a .cpp suffix)` | `SDL_main.h` genera el arranque de WinRT y **es C++**, mientras el juego es una sola unidad de traducción en C. El punto de entrada se aparta a `platform/uwp/ctr_uwp_main.cpp`, el único archivo C++ del port |
| 5 | `The C++ file that includes SDL_main.h must be compiled with /ZW` | Con `/ZW` (C++/CX) el enlace revienta: `vccorlib` exige un `main` de `Platform::Array` y choca con el CRT (`LNK2038`, `LNK2005`). SDL contempla el caso: se define `SDL_WINRT_METADATA_FILE_AVAILABLE` y se compila **sin** `/ZW` |
| 6 | `unresolved external symbol main` | La aplicación tiene que ser de ventana y no de consola, para que el CRT entre por el `WinMain` que pone SDL |
| 7 | Avisos del juego convertidos en errores (`C4996`, `C4146`, `C4308`) | Los proyectos de Windows Store llevan `/sdl`. Se apaga con `/sdl-` |
| 8 | Se instala pero **no arranca**: `0x8027025B` | Falta `<PackageDependency Name="Microsoft.VCLibs.140.00" …>` en el manifiesto. Meter las DLL dentro del paquete no lo sustituye |
| 9 | `-2147009293: package depends on a framework that could not be found` | La `MinVersion` de VCLibs no puede ser mayor que la instalada en la consola. Se deja baja a propósito |

Dos cosas más, de método: la pila del hilo principal de una app WinRT es de **1 MB** (en escritorio
son 8), así que este juego pide `/STACK:33554432`; y **en UWP no hay consola**, así que `stdout` y
`stderr` se pierden —y ahí van los errores del juego—: se redirigen a archivos en `LocalState`, sin
búfer. Sin eso, nada de lo que viene abajo se habría podido ver.

## Llevar los datos y dibujar: siete más

| | Síntoma | Causa y arreglo |
|---|---|---|
| 10 | Arranca y muere sin dejar registro | `SDL_CreateDirectory` **no crea las carpetas padre**, así que no podía crear su propia carpeta de datos. Se crean una a una |
| 11 | El Device Portal responde **500** al subir el disco de 578 MB, pero sí acepta uno de 150 MiB | El portal escribe un temporal en `D:\`, el volumen del modo desarrollador, que va justo de espacio —aunque `LocalState` tenga 13 GB libres—. El disco se parte en cuatro y **el juego los une al arrancar** |
| 12 | `Could not initialize OpenGL / GLES library`, y `SDL_LoadObject` dice «That operation is not supported» | El `SDL3.dll` que publica el release de SDL3-uwp está compilado con la configuración genérica: sin carga dinámica, y su EGL busca `libEGL.so.1`, un nombre de Linux. Hay que compilarlo desde su proyecto de WinRT |
| 13 | ¿EGL/ANGLE o WGL? | Ese SDL trae los dos caminos, pero su configuración deja GLES/EGL comentado y WGL activo: en la consola el camino bueno es **OpenGL de escritorio con Mesa**, no ANGLE |
| 14 | El proceso muere en la primera operación de dibujado, **sin volcado y sin mensaje** | Era **la versión de Mesa**: con una recién publicada el proceso desaparece dentro de `BeginScene`; con la que ya funcionaba en esa misma consola, dibuja. Es la tercera vez que Mesa manda en este catálogo, y la regla es siempre la misma: **probar primero el Mesa que ya funciona** |
| 15 | `Failed to initialise SDL input subsystem: SDL not built with haptic support` | Ese SDL no trae háptica, y el juego pedía todos los subsistemas de golpe. En UWP se pide solo `SDL_INIT_GAMEPAD` |
| 16 | La geometría cercana salía rota en la prueba de 64 bits | Eso era de la prueba previa sobre CTR Native, no de CTRPad: CTRPad ya trae resuelto el modelo de memoria de 64 bits, y por eso es la base |

## El muro de la pantalla de presentación: era el audio

La primera versión instalada se quedaba en la presentación con **el proceso vivo y la CPU al 0 %**.
No era la capa de CD. Esa pantalla es un bucle que espera a que termine de sonar la voz de «Start
your engines…»:

```c
CDSYS_XAPlay(CDSYS_XA_TYPE_EXTRA, 0x50);
while (sdata->XA_State != 0) { VSync(0); CDSYS_XAPauseAtEnd(); }
```

Sin audio, ese bucle no acaba nunca. Y el audio no abría porque `SDL_OpenAudioDeviceStream` se
quedaba colgado **dentro de SDL3**.

**La causa**, siguiendo la cola de tareas de WASAPI: `WASAPI_ActivateDevice` llama a
`WASAPI_PrepDevice` **desde el propio hilo de gestión de WASAPI**, y la comprobación que debería
detectarlo —`SDL_GetCurrentThreadID() == SDL_GetThreadID(ManagementThread)`, en
`WASAPI_ProxyToManagementThread`— no lo reconoce. Así que la tarea se encola... esperando al hilo
que ya está ejecutándola.

**El parche** (`patches/sdl3-uwp-audio-wasapi.patch`) toca tres archivos del backend:

| Archivo | Cambio |
|---|---|
| `SDL_wasapi.c` | El hilo de gestión **registra su propio identificador** al arrancar, y la comprobación usa ese. **Este es el arreglo**; lo demás es protección |
| `SDL_wasapi.c` | La espera del resultado de una tarea lleva tope (6 s) y avisa |
| `SDL_wasapi_winrt.cpp` | Topes para el `DeviceWatcher` (3 s) y para `ActivateAudioInterfaceAsync` (4 s), cuya espera el propio SDL documenta como «*this can block indefinitely*» |

**Sirve para cualquier port UWP que use SDL3 con audio**, no solo para este.

En el juego quedan dos salvaguardas, que con el audio funcionando no se disparan nunca: la
inicialización del SPU ya no reintenta abrir el dispositivo en cada operación —lo hacía miles de
veces, y con el audio caído eso basta para que el arranque no termine— y el bucle del XA sigue
adelante sin sonido si en 600 cuadros no avanza.

> Se probó también a abrir el audio desde un hilo de trabajo, por si el problema fuera que el juego
> corre en el hilo de la vista de la app. **No hacía falta**: comprobado tras el parche, el audio
> abre igual desde el hilo principal, y el rodeo se quitó.

## El segundo muro: el mando no respondía

Con el audio resuelto, el juego llegaba al menú y **no respondía a ningún botón**. En la consola solo
funcionaba el botón Xbox, que atiende el sistema y nunca llega a la aplicación.

En WinRT los mandos llegan por **Windows.Gaming.Input** y por ningún otro sitio: la configuración de
este SDL activa `SDL_JOYSTICK_WGI` y deja XInput dentro del `#else`, así que ese camino ni se
compila. Y el driver de WGI **se desactiva a sí mismo** si la aplicación no lo pide:

```c
/* src/joystick/windows/SDL_windows_gaming_input.c */
static bool WGI_JoystickInit(void)
{
    if (!SDL_GetHintBoolean(SDL_HINT_JOYSTICK_WGI, false)) {
        return true;                 /* se va sin enumerar ningún mando */
    }
```

El valor por defecto es «0» —lo documenta el propio `SDL_hints.h`—, y ni CTRPad ni este port la
ponían. No es un defecto de SDL3-uwp: es un paso que le toca a la aplicación. **Una línea**, en la
entrada WinRT, que corre antes de que el juego inicialice el subsistema de mandos:

```cpp
SDL_SetHintWithPriority(SDL_HINT_JOYSTICK_WGI, "1", SDL_HINT_OVERRIDE);
```

Y, para la próxima, el diagnóstico queda en el registro desde la primera página:

| Lo que dice | Qué significa |
|---|---|
| `mandos detectados al arrancar: 2 (WGI=1)` | Correcto: el driver enumeró y el juego abrió los mandos |
| `mandos detectados al arrancar: 0 (WGI=1)` | La pista está puesta, pero no hay ningún mando encendido y emparejado |
| `mandos detectados al arrancar: 0 (WGI=sin poner)` | Falta este arreglo |

⚠ **Es la segunda vez que esta pista muerde en este catálogo** —la primera fue otro juego con el
mismo síntoma exacto—, así que vale como paso fijo de todo port UWP con SDL3: encenderla y
comprobar el mando por el registro **antes** de dar el port por terminado.

## El español: un 1 por un 6

El castellano **ya está en el disco**: el juego tiene seis idiomas y carga uno por índice. CTRPad no
tiene menú de idiomas —eso es de *High Octane*, que es de 32 bits y no llega a una consola—, así que
el índice va fijo donde el arranque carga el archivo:

```c
// English=1
LOAD_LangFile(sdata->ptrBigfile1, 6); // 6 = espanol
```

Eso es todo el cambio. El paquete entero cambia **tres bytes** respecto al inglés.

Se probó primero en el PC, con el mismo árbol y el mismo código que usa el paquete, porque cada
vuelta en la consola cuesta mucho más que una compilación de escritorio.

## El panorámico: 16:9 sin estirar

El 16:9 **no se hereda** de *High Octane* por las mismas razones: es un árbol de 32 bits. Se portó a
mano detrás de la opción de CMake `CTR_WIDESCREEN`, **apagada por omisión**, así que sin ella el
paquete sale igual que antes.

Cómo funciona: el juego sigue dibujando en su lienzo de PlayStation, pero **la fila X de la matriz de
vista-proyección se comprime** (`34/45`, que es 4:3 partido por el aspecto de presentación); al
presentar ese lienzo en 16:9, la escena recupera su forma y **entra más mundo por los lados**. La
interfaz, que no debe deformarse, se comprime igual, **cada primitiva sobre su propio centro**.

Las piezas, que es donde se ve el trabajo de verdad:

| Dónde | Qué |
|---|---|
| El empujador de primitivas | La fila X de la matriz, el frustum y los rayos de esquina |
| El dibujado del nivel | La ventana de recorte horizontal: sin ampliarla, el juego descarta justo lo que ahora se ve |
| El HUD y la fuente | Dos funciones que comprimen cada cuadrilátero sobre su centro; y el cursor del texto avanza sin comprimir y se comprime al dibujar, o las letras se amontonan |
| Mapa, iconos, medidores, marcador y la vista previa de pista | Uno por uno |
| El presentador | El aspecto fijo en 16:9 |

⚠ **La trampa que mide el coste real de traerse cosas de otro árbol:** el bloque del mapa de *High
Octane* **no compila** en CTRPad, porque desreferencia lo que aquí es una **referencia de invitado**.
Hay que traducirlo a los accesores de CTRPad. La regla que salió de ahí: **lo que es pura coordenada
entra tal cual; lo que toca datos del juego hay que traducirlo.**

**Rendimiento: no cuesta nada.** 2 000 cuadros a **29,91 FPS**, los mismos que en 4:3, con la ventana
en 1920×1080.

## Los 60 FPS

El juego es de 1999 y su lógica va atada a 30 imágenes por segundo. Pasarlo a 60 son **401 cambios
en 60 archivos**, portados de *High Octane* con herramientas de trasplante, detrás de la opción
`CTR_NATIVE_60FPS` y **apagados en tiempo de ejecución** salvo que se pidan (`CTR_60FPS=1` o un
`60fps.txt` en la carpeta de datos).

El patrón es casi siempre el mismo: lo que se medía en cuadros pasa por `FPS_DOUBLE`, y lo que debe
ocurrir una vez por cuadro de 30 se salta un cuadro de cada dos (`timer & 1`). Lo interesante son las
excepciones, y una de ellas se encontró porque el usuario avisó de que **el trofeo del título no
salía**: las animaciones a 60 FPS tienen el doble de fotogramas, así que el índice llega al doble, y
quien las lee tiene que tratar la mitad alta como fotograma y el bit bajo como mezcla con el
siguiente. Faltaba esa otra mitad del cambio, en el ejecutor de la cola de dibujado; sin ella se leía
fuera de rango y el modelo no salía.

Medido en la consola: **59,8 FPS**.

## El disco, en trozos

Las subidas del Device Portal pasan por `D:\DevelopmentFiles`, y ahí no caben 578 MB de una vez:
HTTP 500. `tools/partir_disco.py` lo parte en trozos de 150 MiB con un índice al lado, y la entrada
del juego (`CtrUwp_JoinDiscParts`) los une en el arranque siguiente, dejando constancia en el
registro. Los trozos se quedan: ocupan, pero son el respaldo.

## Lo que falta

Para no prometer lo que no hay:

- **La suspensión del modo desarrollador** no está resuelta aquí: al volver de Home, el juego
  empieza de nuevo. En otro port de este catálogo se resolvió guardando la máquina al pasar a
  segundo plano, pero eso exige un serializador de estado que CTRPad no tiene.
- **El panorámico tiene ajustes finos pendientes** en pantallas sueltas (el panel de estadísticas del
  garaje se sale un poco).
- **El mando** funciona (lo confirmó el usuario jugando), pero la vibración no se ha mirado.
