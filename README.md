# Hyper-Personalized Retail Shopping Concierge — E-Commerce RAG

A complete, locally runnable web application featuring a conversational AI shopping assistant powered by Retrieval-Augmented Generation (RAG), strict SQLite inventory guardrails, personal style ranking, and a photo-based sizing assistant with landmark proportion estimation.

Runs **100% locally on your computer** without paid API keys or cloud dependencies.

---

## 1. System Architecture & Features

```
┌────────────────────────────────────────────────────────────────────────┐
│                        Fashion E-Commerce UI                           │
│     (Stylist Chatbot | Photo Size Assistant | Live Inventory | Profile)│
└─────────────────────────────────┬──────────────────────────────────────┘
                                  │ HTTP / JSON
                                  ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        FastAPI Backend Engine                          │
│                                                                        │
│   ┌────────────────────┐   ┌───────────────────┐   ┌────────────────┐  │
│   │ Local LLM (Ollama) │   │ ChromaDB Vector DB│   │ SQLite (Truth) │  │
│   │   Qwen 2.5 3B      │   │  all-MiniLM-L6-v2 │   │ Catalog/Stock/ │  │
│   │ (Fallback NLP Rule)│   │  Semantic Embeds  │   │ Size Charts    │  │
│   └─────────▲──────────┘   └─────────▲─────────┘   └───────▲────────┘  │
│             │                        │                     │           │
│   ┌─────────┴────────────────────────┴─────────────────────┴────────┐  │
│   │          Inventory Guardrail & Personalization Agent            │  │
│   │  • Verifies live SQLite stock across sizes & variants           │  │
│   │  • Enforces budget constraints & blocks unavailable sizes       │  │
│   │  • Scores candidate items using customer preferences            │  │
│   │  • Synthesizes grounded explanations without hallucination      │  │
│   └─────────────────────────────────────────────────────────────────┘  │
│                                                                        │
│   ┌─────────────────────────────────────────────────────────────────┐  │
│   │                 Photo-Based Size Assistant                      │  │
│   │  • OpenCV & MediaPipe Pose landmark proportion detection        │  │
│   │  • Calibrated height scaling & brand size-chart matching        │  │
│   │  • Ephemeral local processing: zero image retention             │  │
│   └─────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────────┘
```

### Key Modules:
- **Stylist Chatbot & RAG Retrieval**: Understands complex user requests (e.g. *"I need a comfortable outfit for a beach wedding under ₹3,000. I prefer loose-fitting clothes in pastel colors."*), extracts intent parameters (occasion, budget, category, fit, color, material, size), retrieves semantic candidates from ChromaDB, and generates strictly grounded recommendations.
- **SQLite Inventory Guardrail**: The relational database is the absolute source of truth for stock and pricing. The guardrail rejects out-of-stock variants, verifies size availability, blocks items violating budget caps, and suggests in-stock alternatives if all candidates fail.
- **Customer Personalization**: Profiles store size, fit, color palettes, fabric preferences, budget ceilings, and purchase history to provide transparent ranking boosts without requiring sensitive personal disclosures.
- **Photo-Based Size Assistant**: Detects proportional 2D body landmarks (shoulders, torso, hips) using MediaPipe and OpenCV, applies optional user height calibration, matches against brand-specific size charts, and indicates confidence levels with ethical disclaimers. Temporary photos are processed in memory and never stored.
- **Local LLM with Graceful Fallback**: Connects to local Ollama with `qwen2.5:3b`. If Ollama is offline or the model is not pulled, the system automatically falls back to an internal high-precision rule-based NLP parser so the application continues to run end-to-end without interruption.

---

## 2. Technology Stack

- **Frontend**: Responsive HTML5, CSS3 (luxury fashion boutique theme), Vanilla JavaScript.
- **Backend**: Python 3.11 with FastAPI and Uvicorn.
- **Local LLM**: Ollama with `qwen2.5:3b` (HTTP API on `http://127.0.0.1:11434`).
- **Vector Embeddings**: Sentence Transformers (`all-MiniLM-L6-v2`) with 384-dimensional cosine index.
- **Vector Store**: ChromaDB (persistent local storage).
- **Relational Database**: SQLite with WAL mode and foreign key integrity.
- **Computer Vision**: OpenCV (`cv2`) and MediaPipe Pose (`mediapipe`).
- **Testing**: Pytest with automated test coverage across all major components.

---

## 3. Installation & Environment Setup

### Prerequisites
- Python 3.11 installed.
- (Optional but recommended) [Ollama](https://ollama.com) installed for local LLM inference.

### Step 1: Clone / Navigate to Directory
```powershell
cd "c:\Users\harsh\OneDrive\Documents\e-commerce(RAG)"
```

### Step 2: Activate the Virtual Environment
A Python virtual environment `.venv` is included:
```powershell
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1

# Or run directly via .venv python executable:
.\.venv\Scripts\python --version
```

### Step 3: Verify Dependencies
Dependencies are already installed in `.venv`. To re-install or update:
```powershell
.\.venv\Scripts\python -m pip install -r requirements.txt
```

---

## 4. Local LLM Setup (Ollama with Qwen 2.5 3B)

1. Download and install Ollama from [https://ollama.com](https://ollama.com).
2. Start the Ollama server:
   ```powershell
   ollama serve
   ```
3. In a separate terminal, pull the Qwen 2.5 3B model:
   ```powershell
   ollama pull qwen2.5:3b
   ```
4. Verify the model is running:
   ```powershell
   ollama list
   ```

> **Note on Fallback Mode**: If Ollama is not running or the model is not yet downloaded, ATELIER automatically activates its internal rule-based NLP extraction and template-grounded explanation engine. All search, filtering, inventory guardrails, size estimation, and UI features continue to work seamlessly.

---

## 5. Database & Vector Store Initialization

Initialize the SQLite database with realistic apparel products, variants, customers, and size charts:
```powershell
.\.venv\Scripts\python scripts\seed_database.py
```

Rebuild the ChromaDB semantic vector embeddings:
```powershell
.\.venv\Scripts\python scripts\rebuild_index.py
```

---

## 6. Running the Application

Start the FastAPI application with Uvicorn:
```powershell
.\.venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Open your browser and navigate to:
- **Interactive Web App**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Interactive Swagger API Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **API Health Check**: [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)

---

## 7. Running the Automated Test Suite

Run all automated unit and integration tests:
```powershell
.\.venv\Scripts\python -m pytest tests/ -v
```

The automated test suite verifies:
1. `tests/test_inventory_guardrail.py`:
   - Out-of-stock products rejected against SQLite.
   - **Crucial verification**: Confirming that unavailable sizes are never recommended as available.
   - Strict budget ceiling enforcement.
   - Immediate detection when an in-stock product dynamically transitions to 0 stock.
   - Suggestion of available alternatives when candidate items fail guardrails.
2. `tests/test_search_and_rag.py`:
   - Semantic retrieval and SQLite keyword fallback.
   - Strict metadata filtering (category, fit, occasion).
   - Empty search results handling.
3. `tests/test_personalization.py`:
   - Customer profile loading and style alignment.
   - Preference-based scoring boosts for fit, fabric, color, and brand loyalty.
4. `tests/test_size_assistant.py`:
   - Brand size chart matching with height calibration.
   - Uncalibrated photo confidence indicators and disclaimer generation.
   - Low confidence and corrupted image handling.
5. `tests/test_ollama_fallback.py`:
   - Missing Ollama server / offline model health detection.
   - Fallback NLP parser extracting occasion, budget, fit, color, material, and category.
   - Grounded explanation generation without hallucination.
6. `tests/test_api_endpoints.py`:
   - `GET /api/health`, `GET /api/products`, `POST /api/chat`, `GET /api/customers/{id}`, `PUT /api/customers/{id}/preferences`.
   - Explicit consent validation (`POST /api/size-assistant/analyze` rejects unconsented requests with HTTP 400).
   - Rejection of invalid file formats.

---

## 8. Privacy, Security & Limitations

- **Local Inference**: All embeddings, image landmark detections, and database operations execute locally. No user photos, chat logs, or measurements leave your machine.
- **Ephemeral Photo Processing**: Photographs uploaded for size estimation are read in memory, analyzed for 2D proportional ratios, and never committed to disk or saved to any database.
- **Photo Sizing Limitations**:
  - A 2D photograph captures projected silhouette width, not 3D body circumference. Measurements are calibrated approximations using anthropometric ellipse models.
  - Sizing estimates should always be confirmed against garment ease and individual fit preference.
  - The system never infers weight, medical conditions, or sensitive demographic attributes.
