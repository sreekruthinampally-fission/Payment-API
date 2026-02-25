from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.models import User, Order, Wallet
from app.schemas import UserCreate, OrderCreate
from uuid import UUID
from decimal import Decimal
import uuid


def _commit_and_refresh(db: Session, instance):
    """Commit transaction, refresh ORM state, and rollback on failure."""
    try:
        db.commit()
        db.refresh(instance)
    except SQLAlchemyError:
        db.rollback()
        raise


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()

def create_user(
    db: Session,
    user_data: UserCreate,
    hashed_password: str
) -> User:
    """Persist a new user record."""
    user = User(
        email=user_data.email,
        full_name=user_data.full_name,
        phone=user_data.phone,
        hashed_password=hashed_password,
        is_active=True
    )

    db.add(user)
    _commit_and_refresh(db, user)
    return user


def get_user(db: Session, user_id: UUID) -> User | None:
    return db.query(User).filter(User.id == user_id).first()


def list_users(db: Session, skip: int = 0, limit: int = 100) -> list[User]:
    return db.query(User).offset(skip).limit(limit).all()



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
            return existing

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
    return order


def get_orders_by_customer(db: Session, customer_id: UUID) -> list[Order]:
    return db.query(Order).filter(
        Order.customer_id == customer_id
    ).all()

def _get_wallet_for_update(
    db: Session,
    customer_id: UUID
) -> Wallet:
    """
    Retrieve wallet with row-level lock.
    Prevents lost updates.
    """

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

    return wallet


def get_wallet(db: Session, customer_id: UUID) -> Wallet:
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

    wallet = _get_wallet_for_update(db, customer_id)

    wallet.balance += amount

    _commit_and_refresh(db, wallet)
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

    wallet = _get_wallet_for_update(db, customer_id)

    if wallet.balance < amount:
        db.rollback()
        raise ValueError("Insufficient balance")

    wallet.balance -= amount

    _commit_and_refresh(db, wallet)
    return wallet
