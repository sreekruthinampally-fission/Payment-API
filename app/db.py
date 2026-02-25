from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import logging
from app.config import settings
from app.models import Base

logger = logging.getLogger(__name__)

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_timeout=settings.db_pool_timeout,
    pool_recycle=settings.db_pool_recycle,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

def init_db():
    logger.info("db.init.started")
    Base.metadata.create_all(bind=engine)
    logger.info("db.init.succeeded")


def db_healthcheck() -> bool:
    """Return True when DB is reachable and can execute a simple query."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        logger.exception("db.healthcheck.failed")
        return False

def get_db():
    db = SessionLocal()
    logger.debug("db.session.opened")
    try:
        yield db
    finally:
        db.close()
        logger.debug("db.session.closed")
