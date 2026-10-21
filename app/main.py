import os
import sqlite3
import logging
from pathlib import Path
from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from app.config import (
    APP_TITLE, APP_DESCRIPTION, APP_VERSION,
    DB_PATH, BASE_DIR
)
from app.database import get_db, init_db
from contextlib import asynccontextmanager
from app.models import HealthResponse
from app.services.ollama_service import ollama_service
from app.services.retrieval_service import retrieval_service
from app.routes import chat, products, customers, size_assistant

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("retail_concierge")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing Hyper-Personalized Retail Shopping Concierge...")
    # Check if database exists, otherwise run initial seeding
    if not DB_PATH.exists():
        logger.info("Database file not found. Seeding initial database...")
        from scripts.seed_database import seed_database
        seed_database()

    # Verify or initialize vector store
    try:
        col = retrieval_service.collection
        if col is not None and col.count() == 0:
            logger.info("Vector database is empty. Indexing products into ChromaDB...")
            retrieval_service.index_products()
    except Exception as e:
        logger.warning(f"Startup vector index notice: {e}")
    yield

app = FastAPI(
    title=APP_TITLE,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(chat.router)
app.include_router(products.router)
app.include_router(customers.router)
app.include_router(size_assistant.router)

# Mount Static Files & Frontend
STATIC_DIR = BASE_DIR / "app" / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

INDEX_HTML_PATH = BASE_DIR / "app" / "templates" / "index.html"

@app.get("/", include_in_schema=False)
def get_index():
    if INDEX_HTML_PATH.exists():
        return FileResponse(str(INDEX_HTML_PATH))
    return {"message": f"Welcome to {APP_TITLE}. Please access /docs for API documentation."}

@app.get("/api/health", response_model=HealthResponse, tags=["Health"])
def health_check(conn: sqlite3.Connection = Depends(get_db)):
    # 1. SQLite status
    sqlite_ok = False
    prod_count = 0
    try:
        row = conn.execute("SELECT COUNT(*) as cnt FROM products").fetchone()
        prod_count = row["cnt"] if row else 0
        sqlite_ok = True
    except Exception as e:
        logger.error(f"Database health check error: {e}")

    # 2. ChromaDB status
    chroma_ok = False
    chroma_items = 0
    try:
        col = retrieval_service.collection
        if col is not None:
            chroma_items = col.count()
            chroma_ok = True
    except Exception as e:
        logger.warning(f"ChromaDB health check warning: {e}")

    # 3. Ollama status
    ollama_health = ollama_service.check_health()

    return HealthResponse(
        status="healthy" if sqlite_ok else "degraded",
        ollama_connected=ollama_health["connected"],
        ollama_model=ollama_health["target_model"],
        ollama_details=ollama_health,
        vector_db_connected=chroma_ok,
        vector_db_items_count=chroma_items,
        sqlite_connected=sqlite_ok,
        total_products_count=prod_count
    )
