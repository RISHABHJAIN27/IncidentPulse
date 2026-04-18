set shell := ["powershell.exe", "-NoLogo", "-Command"]

run:
    python -m uvicorn app.main:app --reload

activate-venv:
    .\venv\Scripts\activate

run-dynamodb:
    docker run -d --name dynamodb-local -p 8001:8000 amazon/dynamodb-local
