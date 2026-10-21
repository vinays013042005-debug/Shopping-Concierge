import pytest
import tempfile
from pathlib import Path
from scripts.seed_database import seed_database
from app.services.retrieval_service import RetrievalService

@pytest.fixture
def temp_db():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)
    seed_database(db_path)
    yield db_path
    if db_path.exists():
        try:
            db_path.unlink()
        except Exception:
            pass

def test_sqlite_fallback_search_finds_relevant_products(temp_db):
    retrieval = RetrievalService()
    results = retrieval.search_candidates(
        query_text="beach wedding linen shirt pastel",
        n_results=5,
        category="Shirts",
        db_path=temp_db
    )
    assert len(results) > 0
    top_id = results[0]["product_id"]
    assert top_id in ["PROD-001", "PROD-002", "PROD-003"]

def test_metadata_filtering_by_category(temp_db):
    retrieval = RetrievalService()
    # Search within Dresses
    results = retrieval.search_candidates(
        query_text="beach wedding outfit",
        n_results=5,
        category="Dresses",
        db_path=temp_db
    )
    assert len(results) > 0
    for r in results:
        assert r["metadata"]["category"] == "Dresses"

def test_empty_search_results(temp_db):
    retrieval = RetrievalService()
    results = retrieval.search_candidates(
        query_text="nonexistentastronautspacesuitxyz12345",
        n_results=5,
        category="AstronautSuits",
        db_path=temp_db
    )
    assert len(results) == 0
