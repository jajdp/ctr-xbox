# -*- coding: utf-8 -*-
"""Parte el disco del juego en trozos para subirlos al Device Portal.

El portal escribe un temporal en `D:\\` (el volumen del modo desarrollador, ~5 GB y casi
lleno), asi que una subida de 578 MB responde 500 aunque LocalState tenga 13 GB libres. La
solucion es la misma que en Recompilaciones: subir el disco en trozos. El port los une en la
consola la primera vez que arranca (ver NativeDiscImage_JoinParts en el parche de UWP).

    py -3.13 partir_disco.py <ctr-u.bin> <carpeta de salida> [tamano MiB] [nombre destino]

El nombre destino sirve cuando el .bin del usuario se llama de otra manera: los trozos
tienen que llamarse como el archivo que el juego busca (`ctr-u.bin`), no como el original.

Deja `ctr-u.bin.001`, `.002`, ... y un `ctr-u.bin.partes` con el numero de trozos, el tamano
total y el SHA-1 del original, que es lo que comprueba el port al unirlos.
"""
import hashlib
import os
import sys

entrada = sys.argv[1]
salida = sys.argv[2]
trozo = int(sys.argv[3]) * 1024 * 1024 if len(sys.argv) > 3 else 150 * 1024 * 1024

os.makedirs(salida, exist_ok=True)
nombre = sys.argv[4] if len(sys.argv) > 4 else os.path.basename(entrada)
total = os.path.getsize(entrada)
sha = hashlib.sha1()
n = 0
with open(entrada, "rb") as f:
    while True:
        datos = f.read(trozo)
        if not datos:
            break
        n += 1
        sha.update(datos)
        destino = os.path.join(salida, "%s.%03d" % (nombre, n))
        with open(destino, "wb") as g:
            g.write(datos)
        print("  %s  %.1f MiB" % (os.path.basename(destino), len(datos) / 1048576))

with open(os.path.join(salida, nombre + ".partes"), "w", encoding="ascii") as f:
    f.write("partes=%d\n" % n)
    f.write("bytes=%d\n" % total)
    f.write("sha1=%s\n" % sha.hexdigest())

print("%d trozos · %.1f MiB · sha1 %s" % (n, total / 1048576, sha.hexdigest()))
