@'
# Security Notes

This project handles sensitive senior-care data, including:

- Senior names
- Phone numbers
- Locations
- Support contacts
- Call SIDs
- Check-in transcripts
- Conversation insights
- Risk summaries
- Operator actions
- Caregiver alert data

Do not treat this app as production-ready until the items in this document are addressed.

## Current Development Protection

The backend uses dashboard Basic Auth for operational routes when:

    DASHBOARD_AUTH_ENABLED=true

Protected route prefixes include:

    /ui
    /dashboard
    /ui-api
    /seniors
    /calls
    /operator-actions
    /check-ins
    /schedules
    /scheduler
    /operational-status
    /ai-call-sessions
    /support-contacts
    /heat-settings
    /debug

Public route prefixes include:

    /
    /health
    /docs
    /redoc
    /openapi.json
    /twilio

## Twilio Routes

Twilio routes must remain reachable by Twilio:

    /twilio/*

These are not protected by dashboard Basic Auth. They are protected by Twilio signature validation when:

    TWILIO_SIGNATURE_VALIDATION_ENABLED=true

Do not put Basic Auth in front of Twilio webhook routes unless Twilio is explicitly configured to send those credentials.

## Frontend Proxy

The Next.js frontend calls the backend through:

    /api/backend/*

The proxy injects backend credentials server-side. These credentials must never be exposed with `NEXT_PUBLIC_*` environment variable names.

Correct:

    API_BASIC_AUTH_USERNAME=admin
    API_BASIC_AUTH_PASSWORD=change-me-local-dev

Incorrect:

    NEXT_PUBLIC_API_BASIC_AUTH_USERNAME=admin
    NEXT_PUBLIC_API_BASIC_AUTH_PASSWORD=change-me-local-dev

Anything prefixed with `NEXT_PUBLIC_` can be exposed to the browser.

## Frontend Proxy Production Guard

The Next.js backend proxy is available at:

    /api/backend/*

In local development, this proxy lets the frontend call protected FastAPI routes without exposing backend credentials to the browser.

In production, the proxy is disabled by default unless:

    ENABLE_BACKEND_PROXY_IN_PRODUCTION=true

Do not set this to true until real frontend user authentication is implemented.

Without user authentication, a deployed proxy could become a public tunnel into protected FastAPI routes.

The proxy also restricts which backend route prefixes may be forwarded using:

    BACKEND_PROXY_ALLOWED_PREFIXES=/ui-api,/seniors,/calls,/operator-actions,/check-ins,/schedules,/scheduler,/operational-status,/ai-call-sessions,/support-contacts,/heat-settings

Twilio webhook routes must not be proxied through Next.js. They should remain protected by Twilio signature validation on the FastAPI backend.

## Local Secrets

Never commit:

    .env
    .env.local
    .env.*.local
    frontend/.env.local
    frontend/.env.*.local
    data/*.db
    data/*.sqlite
    data/*.sqlite3

Use `.env.example` files for placeholders only.

## Production Recommendation

Basic Auth is acceptable for local development and early hardening, but it is not the final production auth model.

Production should eventually use:

    Browser user session
      -> Next.js validates logged-in caregiver/operator
      -> Next.js calls FastAPI with internal service token
      -> FastAPI validates internal token or user JWT

Recommended future options:

- Auth.js / NextAuth
- Clerk
- Supabase Auth
- Firebase Auth
- Custom session cookies
- Backend Bearer token
- Internal API key
- Private backend network

## Scheduler Routes

Scheduler routes are sensitive:

    /scheduler/run-due-checks
    /scheduler/run-heat-risk-checks

These can trigger outbound calls. They must not be public in production. They should require authentication, an internal token, or private network access.

## Mock/Fallback Data

Mock fallback must be explicit.

Default:

    NEXT_PUBLIC_ALLOW_MOCK_FALLBACK=false

Demo-only:

    NEXT_PUBLIC_ALLOW_MOCK_FALLBACK=true

Production must not silently show fake senior data when backend calls fail.

## Safe Logging

Safe logging controls are configured with:

    LOG_PII=false
    LOG_TRANSCRIPTS=false
    LOG_RAW_ANALYSIS=false

These should remain false by default, especially in production.

## OpenAI and Twilio Secrets

Never commit:

    OPENAI_API_KEY=
    TWILIO_ACCOUNT_SID=
    TWILIO_AUTH_TOKEN=
    TWILIO_PHONE_NUMBER=
    ADMIN_PASSWORD=
    API_BASIC_AUTH_PASSWORD=

Local development should use `.env` and `frontend/.env.local`.

Production should use the deployment platform secret manager.


## AI Media Stream WebSocket Tokens

The Twilio/OpenAI media-stream websocket endpoint is:

    /twilio/media/ai-check-in

This endpoint is public-facing because Twilio needs to connect to it.

To prevent arbitrary clients from connecting, the TwiML generation route adds a short-lived signed token to the websocket URL:

    stream_token=<signed-token>

The websocket validates this token before accepting the connection.

Configuration:

    AI_STREAM_TOKEN_SECRET=
    AI_STREAM_TOKEN_TTL_SECONDS=300

If `AI_STREAM_TOKEN_SECRET` is not set, local development falls back to `TWILIO_AUTH_TOKEN` as the signing secret.

Production should set a dedicated `AI_STREAM_TOKEN_SECRET`.


## CORS

CORS controls which browser origins may call the FastAPI backend directly.

Configuration:

    CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

Production should use explicit frontend origins, for example:

    CORS_ALLOWED_ORIGINS=https://your-frontend-domain.com

Do not use wildcard `*` with credentials.

CORS is not authentication. It only controls browser-enforced cross-origin access. Operational API routes still require backend authentication.

## Current Production Gaps

Before production, address:

- Replace Basic Auth with real user auth.
- Require logged-in user session before proxying `/api/backend/*`.
- Replace backend Basic Auth with an internal API key, service token, or JWT.
- Add database migrations.
- Move from SQLite to a managed database if deploying multi-user.
- Audit every route that returns transcripts, phone numbers, call SIDs, or support contacts.
- Ensure scheduler endpoints are private or token-protected.
- Keep Twilio signature validation enabled.
- Keep safe logging defaults disabled for PII/transcripts/raw analysis.
'@ | Set-Content -Encoding utf8 docs/security.md