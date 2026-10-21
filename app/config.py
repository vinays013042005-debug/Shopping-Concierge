import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

CHROMA_DIR = BASE_DIR / "chroma_db"
CHROMA_DIR.mkdir(exist_ok=True)

TEMP_UPLOAD_DIR = DATA_DIR / "temp_uploads"
TEMP_UPLOAD_DIR.mkdir(exist_ok=True)

DB_PATH = DATA_DIR / "retail_concierge.db"

# Embedding & Vector Database Settings
CHROMA_COLLECTION_NAME = "retail_products"
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"

# Ollama LLM Settings
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
OLLAMA_TIMEOUT_SECONDS = int(os.getenv("OLLAMA_TIMEOUT_SECONDS", "30"))

# Upload Constraints
MAX_UPLOAD_SIZE_BYTES = 5 * 1024 * 1024  # 5MB
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}

# Project Metadata
APP_TITLE = "Hyper-Personalized Retail Shopping Concierge"
APP_DESCRIPTION = "Local E-Commerce RAG assistant with inventory guardrails, personal style ranking, and photo-based sizing assistant."
APP_VERSION = "1.0.0"
