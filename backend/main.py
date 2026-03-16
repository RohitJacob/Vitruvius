import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings
from services.session_manager import session_manager
from routers import upload, analysis, review, generate

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-7s [%(name)s] %(message)s",
    datefmt="%H:%M:%S",
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)


@asynccontextmanager
async def lifespan(app: FastAPI):
    session_manager.start_cleanup_task()
    yield
    session_manager.stop_cleanup_task()


app = FastAPI(
    title="Vitruvius",
    description="Architect Site Visit Report Generator",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5111"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router, prefix="/api", tags=["upload"])
app.include_router(analysis.router, prefix="/api", tags=["analysis"])
app.include_router(review.router, prefix="/api", tags=["review"])
app.include_router(generate.router, prefix="/api", tags=["generate"])


@app.get("/api/health")
async def health():
    settings = get_settings()
    return {
        "status": "ok",
        "vision_model": settings.vision_model,
        "text_model": settings.text_model,
    }
