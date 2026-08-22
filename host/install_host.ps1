# install_host.ps1
# Registra el native messaging host en Chrome para el usuario actual.
# Genera un archivo JSON en el directorio (no modifica el template).
#
# Uso: .\install_host.ps1 -ExtensionId "abcdefghijklmnopqrstuvwxyzabcdef"
#
# Opcional:
#   -PythonPath "C:\ruta\a\python.exe"  (si python no está en el PATH)
#
# El ExtensionId lo obtienes de chrome://extensions/ tras cargar la extensión.

param(
    [Parameter(Mandatory=$true)]
    [string]$ExtensionId,

    [string]$PythonPath = ""
)

$HostName   = "com.animeautoplay.host"
$HostDir    = $PSScriptRoot
$BatPath    = "$HostDir\animeautoplay_host.bat"

# ── Generar JSON con el ID real (NO tocamos el template) ─────────────────
$jsonContent = @"
{
    "name": "com.animeautoplay.host",
    "description": "Anime AutoPlay Native Host — simula clicks reales para fullscreen",
    "path": "$BatPath",
    "type": "stdio",
    "allowed_origins": [
        "chrome-extension://$ExtensionId/"
    ]
}
"@

$JsonOutput = "$HostDir\com.animeautoplay.host.json"
$jsonContent | Set-Content $JsonOutput -Encoding UTF8
Write-Host "JSON generado: $JsonOutput"

# ── Ajustar el .bat si se especificó PythonPath ───────────────────────────
if ($PythonPath -ne "") {
    $batContent = "@echo off`r`n`"$PythonPath`" `"%~dp0animeautoplay_host.py`""
    Set-Content -Path $BatPath -Value $batContent -Encoding ASCII
    Write-Host "Bat actualizado con ruta de Python: $PythonPath"
}

# ── Registrar en el registro de Windows ───────────────────────────────────
$RegKey = "HKCU:\SOFTWARE\Google\Chrome\NativeMessagingHosts\$HostName"
if (-not (Test-Path $RegKey)) { New-Item -Path $RegKey -Force | Out-Null }
Set-ItemProperty -Path $RegKey -Name "(default)" -Value $JsonOutput

Write-Host ""
Write-Host "Host registrado correctamente:"
Write-Host "  JSON: $JsonOutput"
Write-Host "  Clave: $RegKey"
Write-Host ""
Write-Host "Reinicia Chrome para que los cambios tengan efecto."
Write-Host ""
Write-Host "NOTA: Si mueves la carpeta de sitio, vuelve a ejecutar este script."
