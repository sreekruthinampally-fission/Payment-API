from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
import logging
from typing import List
from app.db import get_db
from app.schemas import OrderCreate, OrderResponse, OrderDetail
from app.config import settings
from app import services
from app.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("", response_model=OrderResponse, status_code=201)
def create_order(
    order_input: OrderCreate,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user)
):
    """Create an order for the authenticated user."""
    try:
        new_order = services.create_order(
            db=db,
            order_data=order_input,
            user_id=current_user_id
        )
        return OrderResponse(
            order_id=new_order.id,
            status=new_order.status
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except Exception:
        logger.exception("Order processing failed")
        if settings.enable_graceful_degradation:
            raise HTTPException(
                status_code=503,
                detail="Order service temporarily unavailable"
            )
        raise HTTPException(
            status_code=500,
            detail="Order processing failed"
        )


@router.get("", response_model=List[OrderDetail])
def list_orders(
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user)
):
    """List all orders for the authenticated user."""
    orders = services.get_orders_by_customer(db, current_user_id)
    return orders
