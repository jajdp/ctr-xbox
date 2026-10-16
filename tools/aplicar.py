#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Aplica el port de Xbox a un árbol de CTRPad.

Uso:
    python tools/aplicar.py <raíz del árbol de CTRPad>
    python tools/aplicar.py <raíz> --sdl3 <raíz del código de SDL3-uwp>
    python tools/aplicar.py --list

Dos cosas:

  1. **El parche del juego** (`patches/ctr-uwp-port.patch`): 90 archivos, lo que hace que CTRPad
     corra en una consola más los tres añadidos que van detrás de opciones de CMake (el panorámico,
     los 60 FPS y el idioma). Se aplica con `git apply`, que es todo o nada: si un solo trozo no
     cuadra, no escribe nada.
  2. **La entrada WinRT** (`src/uwp/ctr_uwp_main.cpp`), que se copia a `platform/uwp/` del árbol.
     No va en el parche porque es un archivo nuevo y así se puede leer sin desenredar un diff.

Y con `--sdl3`, el parche del audio de SDL3 (`patches/sdl3-uwp-audio-wasapi.patch`), que hace falta
una vez sobre el código de SDL3-uwp antes de compilarlo: sin él el juego se queda en la pantalla de
presentación con el proceso vivo y la CPU al 0 % (docs/HOW-IT-WORKS.es.md).

Es idempotente: si el parche ya está puesto, lo dice y no toca nada.

Después de esto: `tools/construir-uwp.ps1` (docs/INSTALL.es.md §6).

Recompilaciones — https://github.com/jajdp/ctr-xbox
GPL-3.0-or-later, como CTRPad.
"""
import os
import shutil
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARCHE = os.path.join(REPO, 'patches', 'ctr-uwp-port.patch')
PARCHE_SDL = os.path.join(REPO, 'patches', 'sdl3-uwp-audio-wasapi.patch')
ENTRADA = os.path.join(REPO, 'src', 'uwp', 'ctr_uwp_main.cpp')

# El commit de CTRPad contra el que se hizo el parche. No es una exigencia: `git apply` dirá si
# cuadra o no con el árbol que tengas. Está aquí para que, si no cuadra, sepas desde dónde mirar.
BASE = '76ad5fe6ca87de190c79d90b23603b4630813f22'
PROYECTO = 'chrissotraidis/ctrpad'

for _f in (sys.stdout, sys.stderr):
    if hasattr(_f, 'reconfigure'):
        _f.reconfigure(encoding='utf-8', errors='replace')


def git(raiz, *args, **kw):
    return subprocess.run(['git', '-C', raiz] + list(args), capture_output=True, text=True,
                          encoding='utf-8', errors='replace', **kw)


def aplicar_parche(raiz, parche, que):
    """Aplica un parche con git apply. Devuelve 'puesto', 'ya estaba' o muere diciendo por qué."""
    nombre = os.path.basename(parche)
    if not os.path.isfile(parche):
        sys.exit('falta en el repositorio: %s' % parche)
    # ¿ya está? Si se puede revertir limpiamente, es que está aplicado.
    if git(raiz, 'apply', '--reverse', '--check', parche).returncode == 0:
        print('   %-34s ya estaba' % nombre)
        return 'ya estaba'
    r = git(raiz, 'apply', '--check', '--whitespace=nowarn', parche)
    if r.returncode != 0:
        print((r.stderr or r.stdout).strip()[:1500])
        sys.exit('\n%s no entra en %s.\n'
                 'Comprueba que es %s y, si lo has actualizado, que sigue pareciéndose al commit\n'
                 '%s, que es contra el que se hizo este parche. git apply no ha escrito nada.'
                 % (nombre, raiz, PROYECTO, BASE[:7]))
    r = git(raiz, 'apply', '--whitespace=nowarn', parche)
    if r.returncode != 0:
        print((r.stderr or r.stdout).strip()[:1500])
        sys.exit('%s falló al aplicarse (y la comprobación había pasado)' % nombre)
    print('   %-34s puesto: %s' % (nombre, que))
    return 'puesto'


def main():
    if '--list' in sys.argv[1:]:
        print('El port, en orden:\n')
        print('  1. patches/ctr-uwp-port.patch       90 archivos: el port UWP, el panorámico,')
        print('                                      los 60 FPS y el idioma (por opciones de CMake)')
        print('  2. src/uwp/ctr_uwp_main.cpp         -> <arbol>/platform/uwp/')
        print('  3. patches/sdl3-uwp-audio-wasapi.patch   solo con --sdl3 <ruta de SDL3-uwp>:')
        print('                                      el interbloqueo del audio de WinRT')
        print('\nY despues: tools/construir-uwp.ps1 (docs/INSTALL.es.md §6).')
        return 0

    libres = [a for a in sys.argv[1:] if not a.startswith('-')]
    sdl3 = None
    if '--sdl3' in sys.argv:
        i = sys.argv.index('--sdl3')
        if i + 1 >= len(sys.argv):
            sys.exit('--sdl3 necesita la ruta del codigo de SDL3-uwp')
        sdl3 = os.path.abspath(sys.argv[i + 1])
        libres = [a for a in libres if a != sys.argv[i + 1]]
    if len(libres) != 1:
        sys.exit('uso: %s <ruta de la raiz del arbol de CTRPad> [--sdl3 <ruta de SDL3-uwp>]'
                 % os.path.basename(sys.argv[0]))
    raiz = os.path.abspath(libres[0])

    for exigido in ('CMakeLists.txt', 'game', os.path.join('platform', 'native_renderer.c')):
        if not os.path.exists(os.path.join(raiz, exigido)):
            sys.exit('no es la raiz de un arbol de CTRPad (falta %s): %s' % (exigido, raiz))
    if git(raiz, 'rev-parse', '--git-dir').returncode != 0:
        sys.exit('%s no es un repositorio git, y el parche se aplica con git apply.\n'
                 'Clonalo con git (docs/INSTALL.es.md §2) en vez de descargar un zip.' % raiz)

    cabeza = git(raiz, 'rev-parse', 'HEAD').stdout.strip()
    print('arbol: %s' % raiz)
    print('  HEAD %s%s' % (cabeza[:7], '  (el mismo del parche)' if cabeza == BASE else
                           '  (el parche se hizo contra %s; git apply dira si cuadra)' % BASE[:7]))

    hechos = []
    if aplicar_parche(raiz, PARCHE, 'el port y sus tres opciones') == 'puesto':
        hechos.append('el parche del juego')

    # La entrada WinRT, como archivo.
    if not os.path.isfile(ENTRADA):
        sys.exit('falta en el repositorio: %s' % ENTRADA)
    destino = os.path.join(raiz, 'platform', 'uwp', 'ctr_uwp_main.cpp')
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    with open(ENTRADA, 'rb') as f:
        fuente = f.read()
    actual = None
    if os.path.isfile(destino):
        with open(destino, 'rb') as f:
            actual = f.read()
    if actual != fuente:
        shutil.copy(ENTRADA, destino)
        print('   %-34s puesto: la entrada WinRT' % 'platform/uwp/ctr_uwp_main.cpp')
        hechos.append('la entrada WinRT')
    else:
        print('   %-34s ya estaba' % 'platform/uwp/ctr_uwp_main.cpp')

    if sdl3:
        for exigido in ('CMakeLists.txt', os.path.join('src', 'audio', 'wasapi')):
            if not os.path.exists(os.path.join(sdl3, exigido)):
                sys.exit('--sdl3 no apunta al codigo de SDL3 (falta %s): %s' % (exigido, sdl3))
        if git(sdl3, 'rev-parse', '--git-dir').returncode != 0:
            print('   (el arbol de SDL3 no es un repositorio git: se usa tools/arreglo_wasapi_deadlock.py)')
            r = subprocess.run([sys.executable, os.path.join(REPO, 'tools',
                                                             'arreglo_wasapi_deadlock.py'), sdl3],
                               capture_output=True, text=True, encoding='utf-8', errors='replace')
            print('\n'.join('   ' + l for l in (r.stdout or '').strip().split('\n')))
            if r.returncode != 0:
                sys.exit((r.stderr or '').strip() or 'el arreglo del audio fallo')
        elif aplicar_parche(sdl3, PARCHE_SDL, 'el interbloqueo del audio de WinRT') == 'puesto':
            hechos.append('el audio de SDL3')
    else:
        print('   (sin --sdl3: acuerdate del parche del audio antes de compilar SDL3-uwp, '
              'docs/INSTALL.es.md §4)')

    print('\nListo: %s.' % (', '.join(hechos) if hechos else 'ya estaba todo puesto'))
    print('Ahora: tools/construir-uwp.ps1 para compilar, empaquetar y firmar '
          '(docs/INSTALL.es.md §6).')
    return 0


if __name__ == '__main__':
    sys.exit(main())
