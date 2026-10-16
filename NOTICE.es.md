# Aviso

*(English: [NOTICE.md](NOTICE.md))*

## Sin afiliación

Esto es un proyecto de aficionado, no oficial y sin ánimo de lucro. **No está afiliado a Sony
Interactive Entertainment, Naughty Dog, Activision ni Microsoft**, ni a sus filiales, ni cuenta con
su respaldo o aprobación, ni lo está con los autores de la decompilación
[CTR-ModSDK](https://github.com/CTR-tools/CTR-ModSDK), de
[CTR Native](https://github.com/CTR-tools/ctr-native), de
[CTRPad](https://github.com/chrissotraidis/ctrpad) ni de
[CTR: High Octane](https://github.com/Rinnegatamante/Crash-Team-Racing-High-Octane). *Crash Team
Racing*, *Xbox* y todos los nombres y marcas relacionados son de sus respectivos propietarios, y
aquí se usan solo para decir con qué funciona esto.

Aquí no se vende nada, y nada de esto está monetizado.

## Qué no distribuye este repositorio

Ni imagen del disco. Ni datos del juego. Ni ejecutable compilado. Ni paquete `.msix`. Ni partidas.
Ni arte, sonido, música o tipografías del juego: tampoco los mosaicos del paquete, y por eso
`package/Assets/` está vacía y [`docs/ASSETS.es.md`](docs/ASSETS.es.md) te pide los tuyos.

**Ni ninguna de las bibliotecas de UWP.** `SDL3.dll`, el `opengl32.dll` de Mesa y el resto del
bundle son binarios de otros: la guía dice de dónde se sacan y cómo se compilan, y aquí no se copia
ninguno.

Nada de esto produce un juego jugable por sí solo. Necesitas tu propia copia volcada legalmente del
disco y CTRPad compilando, y este repositorio no te da ninguna de las dos ni puede dártelas.

## Qué contiene de trabajo de otros

**Un parche contra CTRPad.** `patches/ctr-uwp-port.patch` es un `git diff` contra el commit `76ad5fe`
de [chrissotraidis/ctrpad](https://github.com/chrissotraidis/ctrpad) y, como cualquier diff, cita las
líneas de contexto alrededor de cada cambio. CTRPad es **GPL-3.0**, igual que CTR Native y la
decompilación de ModSDK de la que vienen, y la GPL está escrita precisamente para que un derivado
como este pueda existir y compartirse: este repositorio se publica bajo
[esa misma licencia](LICENSE).

**El panorámico y los 60 FPS vienen de CTR: High Octane** (también GPL-3.0), portados a mano sobre
CTRPad en vez de fusionados, porque High Octane es un árbol de 32 bits y una consola necesita 64. Lo
que eso significa en la práctica: la aritmética de coordenadas entra tal cual, y todo lo que toca
datos del juego hubo que traducirlo a los accesores de CTRPad —el bloque de `UI_Map.c` de High
Octane no llega ni a compilar aquí, porque desreferencia lo que CTRPad modela como una referencia de
invitado—. 401 de esos cambios son los del 60 FPS, repartidos en 60 archivos.

**El parche de SDL3.** `patches/sdl3-uwp-audio-wasapi.patch` cambia tres archivos del backend de
WASAPI de [SDL3-uwp](https://github.com/XboxEmulationHub/SDL3-uwp). SDL3 lleva licencia **zlib**, que
permite versiones modificadas; el parche es un diff contra su propio código, se aplica a tu copia y
no se distribuye ningún binario.

**Aquí no hay ninguna captura de pantalla.** Una captura de esto funcionando sería casi toda arte de
otros.

## Retirada y contacto

Si tienes derechos sobre este material y quieres que algo de aquí se quite o se cambie, escribe a
**jajdpmail@gmail.com** diciendo a qué te opones y en calidad de qué escribes.

Las peticiones de quien tiene los derechos se atienden: se quita la parte en disputa, o se retira el
repositorio, sin discutir, y recibirás una respuesta confirmándolo. No hace falta ningún aviso ni
proceso legal más allá de ese correo para llegar a la persona que mantiene esto.
