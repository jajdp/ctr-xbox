# Los mosaicos del paquete

*(English: [ASSETS.md](ASSETS.md))*

Un paquete UWP necesita trece imágenes. **Este repositorio no trae ninguna**: las del paquete real
se hicieron con el propio material artístico del juego, que es de sus dueños, y eso es exactamente
lo que [`NOTICE.es.md`](../NOTICE.es.md) promete no distribuir. Las pones tú.

`tools/construir-uwp.ps1` se detiene antes de empaquetar si `package/Assets/` no tiene ningún PNG, y
lo dice.

## Qué poner en `package/Assets/`

| Archivo | Medida |
|---|---|
| `SplashScreen.png` | 620 × 300 |
| `SplashScreen.scale-200.png` | 1240 × 600 |
| `Square150x150Logo.png` | 150 × 150 |
| `Square150x150Logo.scale-200.png` | 300 × 300 |
| `Square310x310Logo.png` | 310 × 310 |
| `Square310x310Logo.scale-200.png` | 620 × 620 |
| `Square44x44Logo.png` | 44 × 44 |
| `Square44x44Logo.scale-200.png` | 88 × 88 |
| `Square44x44Logo.targetsize-24_altform-unplated.png` | 24 × 24 |
| `StoreLogo.png` | 50 × 50 |
| `StoreLogo.scale-200.png` | 100 × 100 |
| `Wide310x150Logo.png` | 310 × 150 |
| `Wide310x150Logo.scale-200.png` | 620 × 300 |

PNG de 32 bits con alfa. Las medidas no son una recomendación: un mosaico del tamaño equivocado hace
que la consola rechace el índice de recursos.

## La forma más rápida de tener algo que funcione

Sirven imágenes con esas medidas exactas: a la consola solo le hace falta que existan y que tengan la
forma correcta. Con ImageMagick, si lo tienes, salen todas de una vez.

> **Dónde se escribe esto:** en **PowerShell** —pulsa la tecla **Windows**, escribe `powershell` y
> pulsa **Enter**—, en una ventana **normal**: no hace falta «ejecutar como administrador». Desde la
> carpeta de este repositorio.

```powershell
$tiles = @{
  'SplashScreen.png'                                   = '620x300'
  'SplashScreen.scale-200.png'                         = '1240x600'
  'Square150x150Logo.png'                              = '150x150'
  'Square150x150Logo.scale-200.png'                    = '300x300'
  'Square310x310Logo.png'                              = '310x310'
  'Square310x310Logo.scale-200.png'                    = '620x620'
  'Square44x44Logo.png'                                = '44x44'
  'Square44x44Logo.scale-200.png'                      = '88x88'
  'Square44x44Logo.targetsize-24_altform-unplated.png' = '24x24'
  'StoreLogo.png'                                      = '50x50'
  'StoreLogo.scale-200.png'                            = '100x100'
  'Wide310x150Logo.png'                                = '310x150'
  'Wide310x150Logo.scale-200.png'                      = '620x300'
}
foreach ($t in $tiles.GetEnumerator()) {
  magick -size $t.Value xc:"#1b1b1f" (Join-Path 'package\Assets' $t.Key)
}
```

Cámbialos por arte de verdad cuando quieras. Acuérdate de subir el `-Version` al recompilar, o la
consola seguirá mostrando los mosaicos del paquete que ya tiene.

## Si haces arte

Que sea tuyo. Las capturas, los logotipos, los dibujos de los personajes y las tipografías del juego
son de sus dueños, y un paquete que los lleve es un paquete que no puedes compartir.
