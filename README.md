# Payment API

FastAPI service for user signup/login, order creation, and wallet operations.

## Features
- User signup and login with JWT auth
- Order creation with optional idempotency key
- Wallet balance, credit, and debit for the authenticated user
- PostgreSQL persistence via SQLAlchemy ORM

## Prerequisites
- Python 3.11+
- PostgreSQL 16+

## Setup
1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Configure `.env`:

```env
DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/appdb
SECRET_KEY=replace-with-a-long-random-secret
APP_ENV=production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
ENABLE_GRACEFUL_DEGRADATION=false
CREATE_TABLES_ON_STARTUP=false
LOG_LEVEL=INFO
LOG_FORMAT=plain
LOGIN_ATTEMPT_LIMIT=5
LOGIN_ATTEMPT_WINDOW_SECONDS=300
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=1800
```

4. Apply schema (optional if relying on ORM startup `create_all`):

```bash
psql -U postgres -d appdb -f sql/schema.sql
```

5. Start the API:

```bash
uvicorn app.main:app --reload --port 8000
```

## API Overview

### Auth
- `POST /users/signup`
- `POST /users/login`
- `GET /users/me` (Bearer token required)

### Orders (Bearer token required)
- `POST /orders`
- `GET /orders`

### Wallet (Bearer token required)
- `GET /wallet/me`
- `POST /wallet/me/credit`
- `POST /wallet/me/debit`

## Example Flow

1. Signup:

```bash
curl -X POST http://localhost:8000/users/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email":"user@example.com",
    "full_name":"Demo User",
    "phone":"+1-555-0101",
    "password":"secret123"
  }'
```

2. Login:

```bash
curl -X POST http://localhost:8000/users/login \
  -H "Content-Type: application/json" \
  -d '{
    "email":"user@example.com",
    "password":"secret123"
  }'
```

3. Use token:

```bash
curl -X GET http://localhost:8000/wallet/me \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

Swagger UI: `http://localhost:8000/docs`
