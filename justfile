set shell := ["powershell.exe", "-NoLogo", "-Command"]

run:
    python -m uvicorn app.main:app --reload

activate-venv:
    .\venv\Scripts\Activate.ps1


