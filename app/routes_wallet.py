from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
import logging
from app.db import get_db
from app.schemas import WalletOperation, WalletResponse
from app import services
from app.auth import get_current_user

router = APIRouter(prefix="/wallet", tags=["wallet"])
logger = logging.getLogger(__name__)


@router.post("/me/credit", response_model=WalletResponse)
def credit_wallet(
    operation: WalletOperation,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user)
):
    """Credit the authenticated user's wallet."""
    logger.info(
        "wallet.credit.started",
        extra={"user_id": str(current_user_id), "amount": str(operation.amount)},
    )
    wallet = services.credit_wallet(db, current_user_id, operation.amount)
    logger.info(
        "wallet.credit.succeeded",
        extra={"user_id": str(current_user_id), "balance": str(wallet.balance)},
    )

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
    logger.info(
        "wallet.debit.started",
        extra={"user_id": str(current_user_id), "amount": str(operation.amount)},
    )
    try:
        wallet = services.debit_wallet(db, current_user_id, operation.amount)
        logger.info(
            "wallet.debit.succeeded",
            extra={"user_id": str(current_user_id), "balance": str(wallet.balance)},
        )

        return WalletResponse(
            customer_id=wallet.customer_id,
            balance=wallet.balance
        )

    except ValueError as e:
        logger.warning(
            "wallet.debit.rejected",
            extra={"user_id": str(current_user_id), "reason": str(e)},
        )
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/me", response_model=WalletResponse)
def get_wallet(
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user)
):
    """Get wallet balance for the authenticated user."""
    logger.info("wallet.get.started", extra={"user_id": str(current_user_id)})
    wallet = services.get_wallet(db, current_user_id)

    if not wallet:
        logger.warning("wallet.get.not_found", extra={"user_id": str(current_user_id)})
        raise HTTPException(status_code=404, detail="Wallet not found")
    logger.info(
        "wallet.get.succeeded",
        extra={"user_id": str(current_user_id), "balance": str(wallet.balance)},
    )

    return WalletResponse(
        customer_id=wallet.customer_id,
        balance=wallet.balance
    )
