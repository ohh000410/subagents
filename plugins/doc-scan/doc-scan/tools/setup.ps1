# doc-scan 도구 환경. 새 PC 에서 한 번 실행한다.
$ErrorActionPreference = 'Stop'
$venv = Join-Path $PSScriptRoot '.venv'
if (-not (Test-Path -LiteralPath $venv)) { python -m venv $venv }
$py = Join-Path $venv 'Scripts\python.exe'
& $py -m pip install -q --disable-pip-version-check -r (Join-Path $PSScriptRoot 'requirements.txt')
& $py -c "import cv2, numpy, PIL, pillow_heif; print('doc-scan ok', cv2.__version__)"
