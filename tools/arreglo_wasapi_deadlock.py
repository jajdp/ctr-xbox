# SDL3-uwp: la proteccion anti-interbloqueo de WASAPI_ProxyToManagementThread
# compara contra SDL_GetThreadID(ManagementThread). El propio hilo de gestion
# registra aqui su id al arrancar, que es lo que la comparacion necesita de
# verdad: WASAPI_ActivateDevice llama a WASAPI_PrepDevice desde dentro del hilo
# de gestion, y si no se detecta, la tarea se encola y espera al hilo que ya
# esta ocupado ejecutandola. Eso colgaba la apertura del audio en Xbox UWP.
#
# El mismo cambio que patches/sdl3-uwp-audio-wasapi.patch, pero comprobando el texto en vez de
# aplicando un diff: sirve cuando tu copia de SDL3 no es un repositorio git. Lo llama solo
# tools/aplicar.py --sdl3, y se le puede dar la ruta a mano:
#
#     python tools/arreglo_wasapi_deadlock.py <raiz del codigo de SDL3-uwp>
#
# Recompilaciones - https://github.com/jajdp/ctr-xbox  (GPL-3.0-or-later, como CTRPad)
import io, os, sys

libres = [a for a in sys.argv[1:] if not a.startswith("-")]
if not libres:
    sys.exit("uso: arreglo_wasapi_deadlock.py <raiz del codigo de SDL3-uwp>")
raiz = os.path.abspath(libres[0])
p = os.path.join(raiz, "src", "audio", "wasapi", "SDL_wasapi.c")
if not os.path.isfile(p):
    sys.exit("no es la raiz de SDL3 (falta %s)" % p)
s = io.open(p, encoding="utf-8").read()
fallos = []


def sub(viejo, nuevo, veces=1):
    global s
    n = s.count(viejo)
    if n != veces:
        fallos.append("esperaba %d, hay %d: %r" % (veces, n, viejo[:60]))
        return
    s = s.replace(viejo, nuevo)


sub(
    "static SDL_Thread *ManagementThread = NULL;",
    "static SDL_Thread *ManagementThread = NULL;\n"
    "// the management thread stamps its own id here; see WASAPI_ProxyToManagementThread\n"
    "static SDL_ThreadID ManagementThreadID = 0;",
)

sub(
    "static int ManagementThreadEntry(void *userdata)\n"
    "{\n"
    "    ManagementThreadEntryData *data = (ManagementThreadEntryData *)userdata;\n",
    "static int ManagementThreadEntry(void *userdata)\n"
    "{\n"
    "    ManagementThreadEntryData *data = (ManagementThreadEntryData *)userdata;\n"
    "\n"
    "    ManagementThreadID = SDL_GetCurrentThreadID();\n",
)

sub(
    "    if ((wait_on_result) && (SDL_GetCurrentThreadID() == SDL_GetThreadID(ManagementThread))) {",
    "    if ((wait_on_result) && (SDL_GetCurrentThreadID() == ManagementThreadID)) {",
)

# traza para comprobar que la deteccion funciona
sub(
    "        *wait_on_result = task(userdata);\n        return true;  // completed!",
    '        fprintf(stderr, "[SDL WASAPI] proxy: tarea %p en linea (ya estamos en el hilo de gestion)\\n", (void *)task);\n'
    "        fflush(stderr);\n"
    "        *wait_on_result = task(userdata);\n"
    "        return true;  // completed!",
)

if fallos:
    sys.stderr.write("NO SE ESCRIBIO NADA:\n  " + "\n  ".join(fallos) + "\n")
    sys.exit(1)

tmp = p + ".nuevo"
io.open(tmp, "w", encoding="utf-8", newline="").write(s)
os.replace(tmp, p)
print("arreglo aplicado a SDL_wasapi.c")
