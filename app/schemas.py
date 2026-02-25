from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID
from decimal import Decimal



# User Schemas


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    password: str = Field(..., min_length=6)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str
    phone: Optional[str]
    created_at: datetime
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class UserDetail(UserResponse):
    pass


class Token(BaseModel):
    access_token: str
    token_type: str



# Order Schemas


class OrderCreate(BaseModel):
    amount: Decimal = Field(..., gt=0)
    currency: str = Field(default="INR", pattern=r'^[A-Z]{3}$')
    idempotency_key: Optional[str] = Field(None, max_length=255)


class OrderResponse(BaseModel):
    order_id: UUID
    status: str

    model_config = ConfigDict(from_attributes=True)


class OrderDetail(BaseModel):
    id: UUID
    customer_id: UUID
    amount: Decimal
    currency: str
    status: str
    idempotency_key: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)



# Wallet Schemas


class WalletOperation(BaseModel):
    amount: Decimal = Field(..., gt=0)


class WalletResponse(BaseModel):
    customer_id: UUID
    balance: Decimal

    model_config = ConfigDict(from_attributes=True)


class WalletDetail(BaseModel):
    customer_id: UUID
    balance: Decimal
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
