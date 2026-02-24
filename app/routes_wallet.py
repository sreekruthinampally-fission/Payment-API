from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app.schemas import WalletOperation, WalletResponse
from app import services
from app.auth import get_current_user

router = APIRouter(prefix="/wallet", tags=["wallet"], dependencies=[Depends(get_current_user)])


@router.post("/me/credit")
def credit_wallet(
    operation: WalletOperation,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    user_id = current_user["sub"]

    wallet = services.credit_wallet(db, user_id, operation.amount)

    return WalletResponse(
        customer_id=wallet.customer_id,
        balance=float(wallet.balance)
    )

@router.post("/me/debit", response_model=WalletResponse)
def debit_wallet(
    operation: WalletOperation,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    user_id = current_user["sub"]  # Extract user ID from JWT

    try:
        wallet = services.debit_wallet(db, user_id, operation.amount)

        return WalletResponse(
            customer_id=wallet.customer_id,
            balance=float(wallet.balance)
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/me", response_model=WalletResponse)
def get_wallet(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    user_id = current_user["sub"]  

    wallet = services.get_wallet(db, user_id)

    return WalletResponse(
        customer_id=wallet.customer_id,
        balance=float(wallet.balance)
    )
