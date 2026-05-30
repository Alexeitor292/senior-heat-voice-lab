@'
# Development Setup

## Backend

Create and activate a virtual environment:

    python -m venv venv
    .\venv\Scripts\Activate.ps1

Install dependencies:

    python -m pip install -r requirements.txt

Apply database migrations:

    python -m alembic upgrade head

The app no longer auto-creates tables by default. For throwaway local development only, you may set:

    AUTO_CREATE_DB_TABLES=true

Production should keep:

    AUTO_CREATE_DB_TABLES=false

Create a local `.env` from `.env.example` and fill in development values.

Run tests:

    pytest -q

Run the backend:

    .\venv\Scripts\python.exe -m uvicorn app.main:app --reload

If Windows Application Control blocks `uvicorn.exe`, use module execution:

    .\venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000

Health check:

    curl.exe -i http://localhost:8000/health

Protected API check:

    curl.exe -i http://localhost:8000/ui-api/map

Expected without auth:

    401 Unauthorized

With auth:

    curl.exe -i -u admin:change-me-local-dev http://localhost:8000/ui-api/map

Expected:

    200 OK

## Frontend

Go to the frontend folder:

    cd frontend

Install dependencies:

    npm install

Create `frontend/.env.local` using `frontend/.env.example`.

Example:

    NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
    INTERNAL_API_BASE_URL=http://localhost:8000

    API_BASIC_AUTH_USERNAME=admin
    API_BASIC_AUTH_PASSWORD=change-me-local-dev

    NEXT_PUBLIC_ALLOW_MOCK_FALLBACK=false

Run typecheck and build:

    npm run typecheck
    npm run build

Run the frontend:

    npm run dev

Open:

    http://localhost:3000/map

## Frontend Proxy Check

With backend and frontend running:

    curl.exe -i http://localhost:3000/api/backend/ui-api/map

Expected:

    200 OK

The browser should call the Next.js proxy, not the FastAPI backend directly.

## Mock Fallback Mode

Default:

    NEXT_PUBLIC_ALLOW_MOCK_FALLBACK=false

This makes backend/proxy failures visible.

For demos only:

    NEXT_PUBLIC_ALLOW_MOCK_FALLBACK=true

This allows the frontend to use mock/fallback data if backend calls fail.

## Common Windows Issue

If this fails:

    uvicorn app.main:app --reload

with an Application Control policy error, use:

    .\venv\Scripts\python.exe -m uvicorn app.main:app --reload

or:

    .\venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000

## Manual WebSocket Script

`scripts/test_ai_media_stream_ws.py` is a manual development script, not a pytest test.

Run it manually only when the backend is running and you intentionally want to test the Twilio/OpenAI media stream websocket path.

    python scripts/test_ai_media_stream_ws.py

Pytest should only collect tests from `tests/`.
'@ | Set-Content -Encoding utf8 docs/dev-setup.md