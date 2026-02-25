from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from app.db import get_db
from app.schemas import UserCreate, UserResponse, UserDetail, UserLogin, Token
from app import services
from app.auth import create_access_token, hash_password, verify_password, get_current_user

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/signup", response_model=UserResponse, status_code=201)
def signup(user_input: UserCreate, db: Session = Depends(get_db)):
    """Register a new user with email + password credentials."""
    existing_user = services.get_user_by_email(db, user_input.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    password_hash = hash_password(user_input.password)
    created_user = services.create_user(db, user_input, password_hash)
    return created_user


@router.post("/login", response_model=Token)
def login(login_input: UserLogin, db: Session = Depends(get_db)):
    """Authenticate a user and issue a bearer token."""
    user_record = services.get_user_by_email(db, login_input.email)
    if not user_record:
        raise HTTPException(status_code=400, detail="Invalid credentials")

    if not verify_password(login_input.password, user_record.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    access_token = create_access_token(data={"sub": str(user_record.id)})
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
    user = services.get_user(db, current_user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
