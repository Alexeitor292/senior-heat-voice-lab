$ErrorActionPreference = "Stop"

Set-Location "C:\Users\juana\senior-heat-voice-lab"

.\venv\Scripts\Activate.ps1

python -m app.workers.scheduler_worker --interval 60