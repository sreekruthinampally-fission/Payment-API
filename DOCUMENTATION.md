# Payment API Documentation

## Architecture

### Layers
- `routes_*`: HTTP layer (validation, auth dependency, error mapping)
- `services.py`: business logic + DB transaction handling
- `models.py`: SQLAlchemy entities and relationships
- `schemas.py`: Pydantic request/response contracts
- `auth.py`: password hashing + JWT token handling

### Auth Model
- Passwords are stored as PBKDF2 hashes.
- JWT `sub` contains user id as UUID string.
- Protected routes resolve authenticated user id via `get_current_user`.

## Data Model

### `users`
- `id` (UUID, PK)
- `email` (unique)
- `full_name`
- `phone`
- `hashed_password`
- `created_at`
- `is_active` (bool)

### `orders`
- `id` (UUID, PK)
- `customer_id` (FK -> `users.id`)
- `amount` (must be > 0)
- `currency`
- `idempotency_key` (optional)
- `status`
- `created_at`

### `wallets`
- `customer_id` (UUID, PK, FK -> `users.id`)
- `balance` (must be >= 0)
- `updated_at`

## Endpoints

### Users
- `POST /users/signup`
- `POST /users/login`
- `GET /users/me` (auth required)

### Orders (auth required)
- `POST /orders`
- `GET /orders`

### Wallet (auth required)
- `GET /wallet/me`
- `POST /wallet/me/credit`
- `POST /wallet/me/debit`

## Request/Response Contracts

### Signup request
```json
{
  "email": "user@example.com",
  "full_name": "Demo User",
  "phone": "+1-555-0101",
  "password": "secret123"
}
```

### Login response
```json
{
  "access_token": "<jwt>",
  "token_type": "bearer"
}
```

### Create order request
```json
{
  "amount": 199.99,
  "currency": "USD",
  "idempotency_key": "my-key-001"
}
```

### Wallet operation request
```json
{
  "amount": 50.0
}
```

## Operational Notes
- Configure values through `.env` (`DATABASE_URL`, `SECRET_KEY`, `CORS_ORIGINS`).
- `init_db()` currently uses `Base.metadata.create_all()`. For production evolution, use migrations.
- SQL bootstrap files are in `sql/schema.sql` and `sql/seed_data.sql`.
