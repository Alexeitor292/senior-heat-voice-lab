@'
# Architecture

Senior Heat Voice Lab is a full-stack prototype for senior heat-safety monitoring, voice check-ins, support-network coordination, and operator review workflows.

## Main Components

    app/        FastAPI backend
    frontend/  Next.js frontend
    data/       Local SQLite development database
    tests/      Backend tests
    scripts/    Manual development scripts

## Backend

The backend lives in `app/` and uses FastAPI.

It handles:

- Senior profiles
- Demographics
- Support networks
- Escalation plans
- HeatRisk settings
- Scheduled check-ins
- Heat-triggered calls
- Twilio voice webhooks
- Twilio Media Streams
- OpenAI Realtime AI check-ins
- Conversation analysis
- Check-in reviews
- Operator actions
- Caregiver alerts
- Safe logging

## Frontend

The frontend lives in `frontend/` and uses Next.js.

The frontend calls the backend through a Next.js API proxy:

    Browser
      -> Next.js frontend
      -> /api/backend/*
      -> FastAPI backend

This keeps backend credentials server-side and avoids exposing backend Basic Auth credentials to the browser.

## Legacy Static UI

`app/static/` is legacy.

It may still be mounted at `/ui` if present, but the active frontend direction is the Next.js app in `frontend/`.

## API Boundary

The main frontend-facing backend routes are:

    /ui-api/map
    /ui-api/seniors
    /ui-api/seniors/{id}
    /ui-api/dashboard
    /ui-api/alerts

Operational routes include:

    /seniors/*
    /calls/*
    /operator-actions*
    /check-ins/*
    /schedules*
    /scheduler/*
    /operational-status*
    /ai-call-sessions*

Twilio routes are separate:

    /twilio/*

Twilio routes must remain reachable by Twilio and are protected with Twilio signature validation instead of dashboard Basic Auth.

## Data Mode

The frontend has mock/demo data for development. Mock fallback is explicit opt-in with:

    NEXT_PUBLIC_ALLOW_MOCK_FALLBACK=true

Default development and production behavior should be:

    NEXT_PUBLIC_ALLOW_MOCK_FALLBACK=false

When fallback is disabled, backend/API/proxy failures should fail loudly instead of silently showing fake data.

## Current Persistence

The development database is SQLite by default.

The project currently initializes SQLAlchemy tables at app startup. This is acceptable for local prototyping, but schema changes should move to Alembic migrations before production deployment.

## Current Auth Shape

Current development auth is:

    Browser
      -> Next.js
      -> Next.js proxy injects backend Basic Auth
      -> FastAPI protected operational routes

This is a development hardening step, not the final production auth model.

Future production auth should use a real user session for caregivers/operators and an internal service token or JWT between Next.js and FastAPI.
'@ | Set-Content -Encoding utf8 docs/architecture.md