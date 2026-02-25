from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from app.db import get_db
from app.schemas import WalletOperation, WalletResponse
from app import services
from app.auth import get_current_user

router = APIRouter(prefix="/wallet", tags=["wallet"])


@router.post("/me/credit", response_model=WalletResponse)
def credit_wallet(
    operation: WalletOperation,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user)
):
    """Credit the authenticated user's wallet."""
    wallet = services.credit_wallet(db, current_user_id, operation.amount)

    return WalletResponse(
        customer_id=wallet.customer_id,
        balance=wallet.balance
    )


@router.post("/me/debit", response_model=WalletResponse)
def debit_wallet(
    operation: WalletOperation,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user)
):
    """Debit the authenticated user's wallet."""
    try:
        wallet = services.debit_wallet(db, current_user_id, operation.amount)

        return WalletResponse(
            customer_id=wallet.customer_id,
            balance=wallet.balance
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/me", response_model=WalletResponse)
def get_wallet(
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user)
):
    """Get wallet balance for the authenticated user."""
    wallet = services.get_wallet(db, current_user_id)

    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")

    return WalletResponse(
        customer_id=wallet.customer_id,
        balance=wallet.balance
    )
