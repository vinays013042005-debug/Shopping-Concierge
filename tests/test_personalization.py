import pytest
import tempfile
from pathlib import Path
from scripts.seed_database import seed_database
from app.services.recommendation_service import RecommendationService
from app.models import ChatRequest

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

def test_customer_personalization_boosts_ranking(temp_db):
    """
    Customer CUST-101 (Aarav Sharma) has:
    - preferred_fit: 'Loose'
    - preferred_materials: 'Linen, Cotton'
    - preferred_colors: 'Pastel Blue, Sage Green'
    - budget_max: 3000.0
    - past brand loyalty: Linen Trail
    """
    rec_service = RecommendationService(db_path=temp_db)
    
    # Run chat with customer CUST-101
    req = ChatRequest(
        message="I need a comfortable outfit for a beach wedding under ₹3,000.",
        customer_id="CUST-101"
    )
    resp = rec_service.process_chat(req)

    assert len(resp.recommendations) > 0
    top_pick = resp.recommendations[0]
    # Linen Trail Breezy Linen Shirt should be top pick
    assert top_pick.brand == "Linen Trail"
    assert top_pick.material == "Linen"
    assert top_pick.fit_type == "Loose"
    assert top_pick.price <= 3000.0
    # Match reasons should reflect customer preferences
    reasons_text = " ".join(top_pick.match_reasons).lower()
    assert "fit" in reasons_text or "linen" in reasons_text or "budget" in reasons_text
