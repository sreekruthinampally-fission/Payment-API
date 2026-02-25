from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from fastapi import HTTPException
from app.config import settings
from app.db import init_db, db_healthcheck
from app.logging_config import setup_logging
from app.middleware_logging import RequestLoggingMiddleware
from app.routes_users import router as users_router
from app.routes_orders import router as orders_router
from app.routes_wallet import router as wallet_router

setup_logging(settings.log_level, settings.log_format)
logger = logging.getLogger(__name__)
access_logger = logging.getLogger("app.access")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("application startup begin")
    access_logger.info("access logger active")
    if settings.app_env.lower() == "production":
        if len(settings.secret_key) < 32:
            raise RuntimeError("SECRET_KEY must be at least 32 characters in production.")
        if not settings.cors_origins:
            raise RuntimeError("CORS_ORIGINS must be configured in production.")
    if settings.create_tables_on_startup:
        logger.warning("create_tables_on_startup.enabled")
        init_db()
    else:
        logger.info("create_tables_on_startup.disabled")
    logger.info(
        "middleware loaded",
        extra={"middlewares": [m.cls.__name__ for m in app.user_middleware]},
    )
    logger.info("application startup complete")
    yield
    logger.info("application shutdown complete")


app = FastAPI(
    title="Payment API",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestLoggingMiddleware)


app.include_router(users_router)
app.include_router(orders_router)
app.include_router(wallet_router)


@app.get("/")
def root():
    return {"message": "Payment API is running"}


@app.get("/health")
def health():
    db_ok = db_healthcheck()
    if not db_ok:
        raise HTTPException(status_code=503, detail={"status": "unhealthy", "database": "down"})
    return {"status": "healthy", "database": "up"}
