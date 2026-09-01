param(
    [string]$PythonExe = ""
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

if (-not $PythonExe) {
    $KnownPython = Join-Path $env:LOCALAPPDATA "Python\pythoncore-3.14-64\python.exe"
    $PythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if ($PythonCommand) {
        $PythonExe = $PythonCommand.Source
    } elseif (Test-Path -LiteralPath $KnownPython) {
        $PythonExe = $KnownPython
    } else {
        throw "Python 3.10+ 실행 파일을 찾지 못했습니다. -PythonExe 인수로 경로를 지정하십시오."
    }
}

if (-not (Test-Path -LiteralPath $VenvPython)) {
    & $PythonExe -m venv (Join-Path $ProjectRoot ".venv")
}

& $VenvPython -m pip install --upgrade pip
& $VenvPython -m pip install -r (Join-Path $ProjectRoot "requirements.txt")
Push-Location $ProjectRoot
try {
    & $VenvPython -m alembic upgrade head
} finally {
    Pop-Location
}
& $VenvPython -m pytest (Join-Path $ProjectRoot "tests") -q

Push-Location (Join-Path $ProjectRoot "apps\frontend")
try {
    npm ci
    npm test -- --reporter=dot
    npm run build
} finally {
    Pop-Location
}

Write-Host "DAMGA-OPS prototype bootstrap and verification completed."
