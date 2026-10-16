<#
.SYNOPSIS
  Compila, empaqueta y firma el paquete UWP (Xbox Series) de Crash Team Racing a partir de CTRPad.

.DESCRIPTION
  Cuatro pasos seguidos:
    1. compila el árbol de CTRPad ya parcheado, con el perfil UWP;
    2. monta el layout del paquete: el ejecutable, tus mosaicos y las bibliotecas de UWP
       (SDL3 y Mesa) que vienen del bundle de dependencias;
    3. empaqueta con makeappx;
    4. firma con tu certificado.

  El disco del juego NO va dentro del paquete: se sube aparte al LocalState de la aplicación,
  partido en trozos (tools\partir_disco.py y docs/INSTALL.es.md §8).

  DÓNDE SE ESCRIBE: en PowerShell —tecla Windows, escribe «powershell», Enter—, en una ventana
  NORMAL: no hace falta «ejecutar como administrador», y usarlo además rompería la firma, porque el
  certificado está en el almacén del usuario que ejecuta la orden. Desde la carpeta de este
  repositorio. PowerShell 7 no hace falta: con la 5.1 que trae Windows basta, y por eso los
  ejemplos llevan -ExecutionPolicy Bypass (un Windows de fábrica no ejecuta un .ps1).

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File tools\construir-uwp.ps1 `
      -Arbol C:\ctr\ctrpad -Dep C:\ctr\uwp-dep -Version 1.0.0.0 -Certificado <huella>

.EXAMPLE
  # con el panorámico 16:9 y los 60 FPS compilados dentro
  powershell -ExecutionPolicy Bypass -File tools\construir-uwp.ps1 `
      -Arbol C:\ctr\ctrpad -Dep C:\ctr\uwp-dep -Version 1.0.1.0 -Certificado <huella> -Panoramico -SesentaFps

.NOTES
  Recompilaciones — https://github.com/jajdp/ctr-xbox
  GPL-3.0-or-later, como CTRPad.
#>
param(
  # La raíz del árbol de CTRPad ya parcheado (tools\aplicar.py).
  [Parameter(Mandatory = $true)][string]$Arbol,
  # El bundle de dependencias de UWP: SDL3, Mesa y libuwp. docs/INSTALL.es.md §2.
  [Parameter(Mandatory = $true)][string]$Dep,
  # La versión del paquete, de cuatro números. SUBE en cada paquete nuevo.
  [Parameter(Mandatory = $true)][string]$Version,
  # La huella SHA-1 de tu certificado de firma, en tu almacén personal.
  [Parameter(Mandatory = $true)][string]$Certificado,
  # Dónde dejar el .msix. Por defecto, <árbol>\paquete.
  [string]$Salida = '',
  # Los mosaicos del paquete. Por defecto, package\Assets de este repositorio, que viene VACÍA.
  [string]$Mosaicos = '',
  [switch]$SoloEmpaquetar,
  # 16:9 de verdad en vez de 4:3 con bandas (docs/HOW-IT-WORKS.es.md).
  [switch]$Panoramico,
  # El juego a 60 imágenes por segundo. Se enciende luego con una variable o un archivo.
  [switch]$SesentaFps
)
$ErrorActionPreference = 'Stop'

$Repo = Split-Path -Parent $PSScriptRoot
if (-not $Salida)   { $Salida   = Join-Path $Arbol 'paquete' }
if (-not $Mosaicos) { $Mosaicos = Join-Path $Repo 'package\Assets' }
$build  = Join-Path $Arbol 'build-uwp'
$layout = Join-Path $Arbol 'layout-uwp'

# ---------------------------------------------------------------- comprobaciones, antes de nada
foreach ($exigido in @((Join-Path $Arbol 'CMakeLists.txt'), (Join-Path $Arbol 'game'),
                       (Join-Path $Arbol 'platform\uwp\ctr_uwp_main.cpp'))) {
  if (-not (Test-Path -LiteralPath $exigido)) {
    throw "-Arbol no es un árbol de CTRPad parcheado (falta $exigido). Pasa primero tools\aplicar.py; docs/INSTALL.es.md §3."
  }
}
if (-not (Test-Path -LiteralPath (Join-Path $Dep 'bin\opengl32.dll'))) {
  throw "-Dep no parece el bundle de UWP (falta bin\opengl32.dll en $Dep). docs/INSTALL.es.md §2."
}
if ($Version -notmatch '^\d+\.\d+\.\d+\.\d+$') { throw "-Version tiene que ser de cuatro números, como 1.0.0.0 (es: $Version)" }
$Certificado = $Certificado.Trim() -replace '[\s:]', ''
if ($Certificado -notmatch '^[0-9A-Fa-f]{40}$') {
  throw ("-Certificado tiene que ser la huella SHA-1 de tu certificado, 40 dígitos hexadecimales (es: $Certificado). " +
         "La ves con: Get-ChildItem Cert:\CurrentUser\My | Format-List Subject, Thumbprint — docs/INSTALL.es.md §5.")
}
$cert = Get-ChildItem -LiteralPath "Cert:\CurrentUser\My\$Certificado" -ErrorAction Ignore
if (-not $cert -or -not $cert.HasPrivateKey) {
  throw "no hay ningún certificado CON CLAVE PRIVADA con la huella $Certificado en tu almacén personal. docs/INSTALL.es.md §5."
}

# El SDK de Windows y cmake se buscan: fijarlos a una versión concreta es la forma más rápida de que
# esto deje de funcionar en la máquina de al lado.
$kits = 'C:\Program Files (x86)\Windows Kits\10\bin'
$SDK = Get-ChildItem -LiteralPath $kits -Directory -ErrorAction Ignore |
       Where-Object { Test-Path -LiteralPath (Join-Path $_.FullName 'x64\makeappx.exe') } |
       Sort-Object Name -Descending | Select-Object -First 1
if (-not $SDK) { throw "no encuentro makeappx.exe en ninguna versión del Windows SDK bajo $kits" }
$SDK = Join-Path $SDK.FullName 'x64'
$vs = & "${env:ProgramFiles(x86)}\Microsoft Visual Studio\Installer\vswhere.exe" -latest -property installationPath
if (-not $vs) { throw 'no encuentro Visual Studio (vswhere no devolvió nada): docs/INSTALL.es.md §1' }
$CMAKE = Join-Path $vs 'Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe'
if (-not (Test-Path -LiteralPath $CMAKE)) { $CMAKE = (Get-Command cmake).Source }
Write-Host "  SDK: $SDK"
Write-Host "  cmake: $CMAKE"
Write-Host "  certificado: $($cert.Subject)"

New-Item -ItemType Directory -Force -Path $Salida, $layout | Out-Null

# ---------------------------------------------------------------- 1. compilar
if (-not $SoloEmpaquetar) {
  Write-Host "  compilando CTRPad para UWP..." -ForegroundColor Cyan
  $cfg = @('-S', $Arbol, '-B', $build, '-G', 'Visual Studio 17 2022', '-A', 'x64',
           '-DCMAKE_SYSTEM_NAME=WindowsStore', '-DCMAKE_SYSTEM_VERSION=10.0',
           '-DCTR_NATIVE_UWP=ON', "-DCTR_NATIVE_UWP_DEP=$($Dep -replace '\\','/')",
           '-DBUILD_TESTING=OFF',
           "-DCTR_WIDESCREEN=$(if ($Panoramico) { 'ON' } else { 'OFF' })",
           "-DCTR_NATIVE_60FPS=$(if ($SesentaFps) { 'ON' } else { 'OFF' })")
  if ($Panoramico) { Write-Host "  (panorámico 16:9)" -ForegroundColor Cyan }
  if ($SesentaFps) { Write-Host "  (60 FPS compilados; se encienden con CTR_60FPS=1 o 60fps.txt)" -ForegroundColor Cyan }
  & $CMAKE @cfg | Out-Null
  if ($LASTEXITCODE -ne 0) { throw "falló la configuración de CMake" }
  & $CMAKE --build $build --config Release | Out-Null
  if ($LASTEXITCODE -ne 0) { throw "falló la compilación" }
}
$exe = Join-Path $build 'Release\ctr_native.exe'
if (-not (Test-Path -LiteralPath $exe)) { throw "no está $exe" }

# ---------------------------------------------------------------- 2. el layout
Write-Host "  montando el layout..." -ForegroundColor Cyan
Copy-Item -LiteralPath $exe -Destination (Join-Path $layout 'ctr_native.exe') -Force
foreach ($d in @('SDL3.dll','opengl32.dll','libgallium_wgl.dll','libglapi.dll','z-1.dll','dxil.dll','libuwp.dll')) {
  $o = Join-Path $Dep "bin\$d"
  if (-not (Test-Path -LiteralPath $o)) { throw "falta $d en $Dep\bin: el paquete no arrancaría. docs/INSTALL.es.md §2." }
  Copy-Item -LiteralPath $o -Destination (Join-Path $layout $d) -Force
}
# spirv_to_dxil.dll solo está en algunas versiones del bundle; si está, va.
$extra = Join-Path $Dep 'bin\spirv_to_dxil.dll'
if (Test-Path -LiteralPath $extra) { Copy-Item -LiteralPath $extra -Destination $layout -Force }

$png = @()
if (Test-Path -LiteralPath $Mosaicos) { $png = @(Get-ChildItem -LiteralPath $Mosaicos -Filter *.png -File) }
if (-not $png.Count) {
  throw ("no hay ningún PNG en $Mosaicos. Los mosaicos del paquete los pones tú: docs/ASSETS.es.md dice " +
         "qué tamaños y con qué nombres. Sin ellos la consola no muestra el juego como es debido.")
}
New-Item -ItemType Directory -Force (Join-Path $layout 'Assets') | Out-Null
$png | Copy-Item -Destination (Join-Path $layout 'Assets') -Force
Write-Host ("  mosaicos: {0} PNG" -f $png.Count)

# el manifiesto: la versión de este paquete, y que el Publisher sea el del certificado
$manifiesto = Join-Path $layout 'AppxManifest.xml'
Copy-Item -LiteralPath (Join-Path $Repo 'package\AppxManifest.xml') -Destination $manifiesto -Force
$xml = [IO.File]::ReadAllText($manifiesto)
$publisher = ([regex]::Match($xml, '<Identity\b[^>]*?\bPublisher="([^"]*)"', 'Singleline')).Groups[1].Value
if ($publisher -match 'CHANGE-ME') {
  throw ("package\AppxManifest.xml todavía tiene el Publisher de ejemplo ($publisher). Ponle el sujeto de tu " +
         "certificado, que es «$($cert.Subject)» — docs/INSTALL.es.md §5.")
}
if ($publisher -ne $cert.Subject) {
  throw ("el Publisher del manifiesto («$publisher») no es el sujeto del certificado («$($cert.Subject)»). " +
         "Tienen que ser idénticos letra por letra, o signtool falla — docs/INSTALL.es.md §5.")
}
$xml = [regex]::Replace($xml, '(<Identity[^>]*Version=")[0-9.]+(")', "`${1}$Version`${2}")
[IO.File]::WriteAllText($manifiesto, $xml, (New-Object Text.UTF8Encoding $false))

# ---------------------------------------------------------------- 3 y 4. empaquetar y firmar
$msix = Join-Path $Salida "CrashTeamRacing-$Version.msix"
Write-Host "  makeappx -> $(Split-Path -Leaf $msix)" -ForegroundColor Cyan
& (Join-Path $SDK 'makeappx.exe') pack /d $layout /p $msix /o | Out-String | Write-Host
if ($LASTEXITCODE -ne 0) { throw "makeappx falló" }
& (Join-Path $SDK 'signtool.exe') sign /fd SHA256 /sha1 $cert.Thumbprint $msix | Out-String | Write-Host
if ($LASTEXITCODE -ne 0) { throw "signtool falló" }

# el .cer, para el caso en que alguna vez haga falta registrarlo (normalmente no: §8.2 de la guía)
$cer = Join-Path $Salida 'firma.cer'
if (-not (Test-Path -LiteralPath $cer)) { Export-Certificate -Cert $cert -FilePath $cer -Type CERT | Out-Null }

"{0}  ({1:N1} MB)" -f $msix, ((Get-Item -LiteralPath $msix).Length / 1MB)
Write-Host "Ahora: instálalo por el Device Portal y sube tu disco al LocalState (docs/INSTALL.es.md §8 y §9)."
