from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.config import settings
from app.db import init_db
from app.routes_users import router as users_router
from app.routes_orders import router as orders_router
from app.routes_wallet import router as wallet_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


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


app.include_router(users_router)
app.include_router(orders_router)
app.include_router(wallet_router)


@app.get("/")
def root():
    return {"message": "Payment API is running"}


@app.get("/health")
def health():
    return {"status": "healthy"}
