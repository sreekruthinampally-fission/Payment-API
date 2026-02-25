from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from uuid import UUID
import logging
from app.db import get_db
from app.schemas import UserCreate, UserResponse, UserDetail, UserLogin, Token
from app import services
from app.auth import create_access_token, hash_password, verify_password, get_current_user
from app.config import settings
from app.security import LoginAttemptLimiter

router = APIRouter(prefix="/users", tags=["users"])
logger = logging.getLogger(__name__)
login_limiter = LoginAttemptLimiter(
    max_attempts=settings.login_attempt_limit,
    window_seconds=settings.login_attempt_window_seconds,
)


@router.post("/signup", response_model=UserResponse, status_code=201)
def signup(user_input: UserCreate, db: Session = Depends(get_db)):
    """Register a new user with email + password credentials."""
    logger.info("user.signup.started", extra={"email": user_input.email})
    existing_user = services.get_user_by_email(db, user_input.email)
    if existing_user:
        logger.warning("user.signup.duplicate_email", extra={"email": user_input.email})
        raise HTTPException(status_code=400, detail="Email already registered")

    password_hash = hash_password(user_input.password)
    created_user = services.create_user(db, user_input, password_hash)
    logger.info(
        "user.signup.succeeded",
        extra={"user_id": str(created_user.id), "email": created_user.email},
    )
    return created_user


@router.post("/login", response_model=Token)
def login(login_input: UserLogin, request: Request, db: Session = Depends(get_db)):
    """Authenticate a user and issue a bearer token."""
    client_ip = request.client.host if request.client else "unknown"
    limiter_key = f"{login_input.email}:{client_ip}"
    if login_limiter.is_blocked(limiter_key):
        logger.warning(
            "user.login.rate_limited",
            extra={"email": login_input.email, "client_ip": client_ip},
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again later.",
        )

    logger.info("user.login.started", extra={"email": login_input.email})
    user_record = services.get_user_by_email(db, login_input.email)
    if not user_record:
        logger.warning("user.login.user_not_found", extra={"email": login_input.email})
        login_limiter.register_failure(limiter_key)
        raise HTTPException(status_code=400, detail="Invalid credentials")

    if not verify_password(login_input.password, user_record.hashed_password):
        logger.warning("user.login.invalid_password", extra={"email": login_input.email})
        login_limiter.register_failure(limiter_key)
        raise HTTPException(status_code=400, detail="Invalid credentials")

    access_token = create_access_token(data={"sub": str(user_record.id)})
    login_limiter.clear(limiter_key)
    logger.info(
        "user.login.succeeded",
        extra={"user_id": str(user_record.id), "email": user_record.email},
    )
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.get("/me", response_model=UserDetail)
def get_current_user_profile(
    current_user_id: UUID = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Return profile details for the authenticated user."""
    logger.info("user.me.started", extra={"user_id": str(current_user_id)})
    user = services.get_user(db, current_user_id)
    if not user:
        logger.warning("user.me.not_found", extra={"user_id": str(current_user_id)})
        raise HTTPException(status_code=404, detail="User not found")
    logger.info("user.me.succeeded", extra={"user_id": str(current_user_id)})
    return user
