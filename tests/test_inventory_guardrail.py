import pytest
import sqlite3
import tempfile
from pathlib import Path
from scripts.seed_database import seed_database
from app.services.inventory_guardrail import InventoryGuardrail
from app.database import get_connection

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

def test_inventory_source_of_truth_rejects_out_of_stock(temp_db):
    """Confirm that completely out-of-stock products are rejected."""
    guardrail = InventoryGuardrail(db_path=temp_db)
    # PROD-015 is specifically seeded with 0 stock
    approved, rejected, alternatives = guardrail.inspect_and_filter(
        candidate_product_ids=["PROD-015"]
    )
    assert len(approved) == 0
    assert len(rejected) == 1
    assert "out of stock" in rejected[0]["reason"].lower()

def test_unavailable_sizes_never_recommended_as_available(temp_db):
    """
    CRITICAL REQUIREMENT:
    Confirm that unavailable sizes are NEVER recommended as available.
    PROD-001 has Size XL with stock_quantity = 0.
    """
    guardrail = InventoryGuardrail(db_path=temp_db)
    
    # 1. When requesting XL specifically, PROD-001 should be rejected
    approved, rejected, _ = guardrail.inspect_and_filter(
        candidate_product_ids=["PROD-001"],
        required_size="XL"
    )
    assert len(approved) == 0
    assert len(rejected) == 1
    assert "out of stock" in rejected[0]["reason"].lower()

    # 2. When requesting without size constraint, XL must NOT appear in available_sizes
    approved, _, _ = guardrail.inspect_and_filter(
        candidate_product_ids=["PROD-001"]
    )
    assert len(approved) == 1
    prod = approved[0]
    assert "XL" not in prod["available_sizes"]
    assert "M" in prod["available_sizes"]
    assert "S" in prod["available_sizes"]

def test_strict_budget_constraints(temp_db):
    """Products exceeding budget ceiling must be rejected."""
    guardrail = InventoryGuardrail(db_path=temp_db)
    # PROD-004 is priced at ₹4,200
    approved, rejected, _ = guardrail.inspect_and_filter(
        candidate_product_ids=["PROD-004"],
        budget_max=3000.0
    )
    assert len(approved) == 0
    assert len(rejected) == 1
    assert "exceeds" in rejected[0]["reason"].lower()

def test_product_becoming_out_of_stock_dynamically(temp_db):
    """Verify that if stock is depleted in SQLite, guardrail immediately blocks it."""
    guardrail = InventoryGuardrail(db_path=temp_db)
    
    # Verify PROD-002 is initially approved
    approved, _, _ = guardrail.inspect_and_filter(["PROD-002"])
    assert len(approved) == 1

    # Deplete stock for PROD-002 in SQLite
    conn = get_connection(temp_db)
    conn.execute(
        "UPDATE inventory SET stock_quantity = 0 WHERE variant_id IN (SELECT id FROM product_variants WHERE product_id = 'PROD-002')"
    )
    conn.commit()
    conn.close()

    # Re-run guardrail - must now be rejected!
    approved_after, rejected_after, _ = guardrail.inspect_and_filter(["PROD-002"])
    assert len(approved_after) == 0
    assert len(rejected_after) == 1
    assert "out of stock" in rejected_after[0]["reason"].lower()

def test_suggests_alternatives_when_all_candidates_rejected(temp_db):
    """When all candidate products fail, guardrail suggests valid in-stock alternatives."""
    guardrail = InventoryGuardrail(db_path=temp_db)
    approved, rejected, alternatives = guardrail.inspect_and_filter(
        candidate_product_ids=["PROD-015"], # Out of stock
        budget_max=3000.0
    )
    assert len(approved) == 0
    assert len(alternatives) > 0
    # Every suggested alternative must be in stock
    for alt in alternatives:
        assert len(alt["available_sizes"]) > 0
