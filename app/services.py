from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.models import User, Order, Wallet
from app.schemas import UserCreate, OrderCreate
from uuid import UUID
from decimal import Decimal
import logging
import uuid

logger = logging.getLogger(__name__)


def _commit_and_refresh(db: Session, instance):
    """Commit transaction, refresh ORM state, and rollback on failure."""
    try:
        db.commit()
        db.refresh(instance)
        logger.info(
            "db.commit_refresh.succeeded",
            extra={"entity": instance.__class__.__name__},
        )
    except SQLAlchemyError:
        db.rollback()
        logger.exception(
            "db.commit_refresh.failed",
            extra={"entity": instance.__class__.__name__},
        )
        raise


def get_user_by_email(db: Session, email: str) -> User | None:
    logger.info("service.user.get_by_email.started", extra={"email": email})
    user = db.query(User).filter(User.email == email).first()
    logger.info(
        "service.user.get_by_email.completed",
        extra={"email": email, "found": user is not None},
    )
    return user

def create_user(
    db: Session,
    user_data: UserCreate,
    hashed_password: str
) -> User:
    """Persist a new user record."""
    logger.info("service.user.create.started", extra={"email": user_data.email})
    user = User(
        email=user_data.email,
        full_name=user_data.full_name,
        phone=user_data.phone,
        hashed_password=hashed_password,
        is_active=True
    )

    db.add(user)
    _commit_and_refresh(db, user)
    logger.info(
        "service.user.create.succeeded",
        extra={"user_id": str(user.id), "email": user.email},
    )
    return user


def get_user(db: Session, user_id: UUID) -> User | None:
    logger.info("service.user.get.started", extra={"user_id": str(user_id)})
    user = db.query(User).filter(User.id == user_id).first()
    logger.info(
        "service.user.get.completed",
        extra={"user_id": str(user_id), "found": user is not None},
    )
    return user


def list_users(db: Session, skip: int = 0, limit: int = 100) -> list[User]:
    logger.info("service.user.list.started", extra={"skip": skip, "limit": limit})
    users = db.query(User).offset(skip).limit(limit).all()
    logger.info("service.user.list.completed", extra={"count": len(users)})
    return users



def create_order(
    db: Session,
    order_data: OrderCreate,
    user_id: UUID
) -> Order:
    """
    Create order securely.
    - customer_id comes ONLY from authenticated user
    - idempotency supported
    """

    if order_data.idempotency_key:
        existing = db.query(Order).filter(
            Order.idempotency_key == order_data.idempotency_key
        ).first()
        if existing:
            logger.info(
                "service.order.idempotent_hit",
                extra={
                    "user_id": str(user_id),
                    "order_id": str(existing.id),
                    "idempotency_key": order_data.idempotency_key,
                },
            )
            return existing

    logger.info(
        "service.order.create.started",
        extra={
            "user_id": str(user_id),
            "amount": str(order_data.amount),
            "currency": order_data.currency,
            "idempotency_key": order_data.idempotency_key,
        },
    )
    order = Order(
        id=uuid.uuid4(),
        customer_id=user_id,
        amount=order_data.amount,
        currency=order_data.currency,
        idempotency_key=order_data.idempotency_key,
        status="created"
    )

    db.add(order)
    _commit_and_refresh(db, order)
    logger.info(
        "service.order.create.succeeded",
        extra={"user_id": str(user_id), "order_id": str(order.id)},
    )
    return order


def get_orders_by_customer(db: Session, customer_id: UUID) -> list[Order]:
    logger.info("service.order.list.started", extra={"user_id": str(customer_id)})
    orders = db.query(Order).filter(
        Order.customer_id == customer_id
    ).all()
    logger.info(
        "service.order.list.completed",
        extra={"user_id": str(customer_id), "count": len(orders)},
    )
    return orders

def _get_wallet_for_update(
    db: Session,
    customer_id: UUID
) -> Wallet:
    """
    Retrieve wallet with row-level lock.
    Prevents lost updates.
    """

    logger.info("service.wallet.lock_fetch.started", extra={"user_id": str(customer_id)})
    wallet = db.query(Wallet)\
        .filter(Wallet.customer_id == customer_id)\
        .with_for_update()\
        .first()

    if not wallet:
        wallet = Wallet(
            customer_id=customer_id,
            balance=Decimal("0.00")
        )
        db.add(wallet)
        db.flush()
        logger.info("service.wallet.lock_fetch.created", extra={"user_id": str(customer_id)})

    logger.info("service.wallet.lock_fetch.completed", extra={"user_id": str(customer_id)})
    return wallet


def get_wallet(db: Session, customer_id: UUID) -> Wallet:
    logger.info("service.wallet.get.started", extra={"user_id": str(customer_id)})
    wallet = db.query(Wallet).filter(
        Wallet.customer_id == customer_id
    ).first()

    if not wallet:
        wallet = Wallet(
            customer_id=customer_id,
            balance=Decimal("0.00")
        )
        db.add(wallet)
        _commit_and_refresh(db, wallet)
        logger.info("service.wallet.created", extra={"user_id": str(customer_id)})

    logger.info("service.wallet.get.succeeded", extra={"user_id": str(customer_id)})
    return wallet


def credit_wallet(
    db: Session,
    customer_id: UUID,
    amount: Decimal
) -> Wallet:
    """
    Safe wallet credit using row-level locking.
    Prevents race conditions and lost updates.
    """

    logger.info(
        "service.wallet.credit.started",
        extra={"user_id": str(customer_id), "amount": str(amount)},
    )
    wallet = _get_wallet_for_update(db, customer_id)

    wallet.balance += amount

    _commit_and_refresh(db, wallet)
    logger.info(
        "service.wallet.credit.succeeded",
        extra={"user_id": str(customer_id), "balance": str(wallet.balance)},
    )
    return wallet


def debit_wallet(
    db: Session,
    customer_id: UUID,
    amount: Decimal
) -> Wallet:
    """
    Safe wallet debit with:
    - row-level locking
    - sufficient funds validation
    - atomic commit
    """

    logger.info(
        "service.wallet.debit.started",
        extra={"user_id": str(customer_id), "amount": str(amount)},
    )
    wallet = _get_wallet_for_update(db, customer_id)

    if wallet.balance < amount:
        db.rollback()
        logger.warning(
            "service.wallet.debit.insufficient_funds",
            extra={
                "user_id": str(customer_id),
                "amount": str(amount),
                "balance": str(wallet.balance),
            },
        )
        raise ValueError("Insufficient balance")

    wallet.balance -= amount

    _commit_and_refresh(db, wallet)
    logger.info(
        "service.wallet.debit.succeeded",
        extra={"user_id": str(customer_id), "balance": str(wallet.balance)},
    )
    return wallet
