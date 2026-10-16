/*
 * Punto de entrada del port a Xbox Series (UWP).
 *
 * En UWP la aplicación no empieza en un main() de consola: arranca una CoreApplication de
 * WinRT. SDL ya trae ese arranque, pero su implementación (SDL_main_impl.h) usa WRL y solo
 * compila como C++, mientras que el juego es una única unidad de traducción en C. Por eso el
 * entry point vive aquí, en el único archivo C++ del port, y se limita a llamar al main de
 * siempre, que en esta configuración se llama ctr_native_main.
 */

#include <SDL3/SDL.h>
#include <SDL3/SDL_main.h>

extern "C" int ctr_native_main(int argc, char *argv[]);

int main(int argc, char *argv[])
{
	/*
	 * En la consola los mandos SOLO llegan por Windows.Gaming.Input, y el driver WGI de SDL3
	 * se apaga a sí mismo si la aplicación no pide la pista: su WGI_JoystickInit consulta
	 * SDL_GetHintBoolean(SDL_HINT_JOYSTICK_WGI, false), con el valor por defecto en «0».
	 * Sin esto el juego arranca, suena y se ve, pero no responde a ningún botón.
	 * Hay que ponerla antes de SDL_InitSubSystem(SDL_INIT_GAMEPAD), que corre dentro de
	 * Platform_InputInit.
	 */
	SDL_SetHintWithPriority(SDL_HINT_JOYSTICK_WGI, "1", SDL_HINT_OVERRIDE);

	return ctr_native_main(argc, argv);
}
