import sqlite3
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends
from app.database import get_db
from app.models import CustomerDetail, CustomerPreferencesModel

router = APIRouter(prefix="/api/customers", tags=["Customers & Personalization"])

@router.get("", response_model=List[CustomerDetail])
def list_customers(conn: sqlite3.Connection = Depends(get_db)):
    rows = conn.execute("SELECT id, name, email FROM customers ORDER BY id ASC").fetchall()
    customers = []
    for r in rows:
        cid = r["id"]
        pref_row = conn.execute("SELECT * FROM customer_preferences WHERE customer_id = ?", (cid,)).fetchone()
        prefs = None
        if pref_row:
            prefs = CustomerPreferencesModel(
                preferred_size=pref_row["preferred_size"],
                preferred_fit=pref_row["preferred_fit"],
                preferred_colors=pref_row["preferred_colors"],
                preferred_materials=pref_row["preferred_materials"],
                budget_max=pref_row["budget_max"],
                explicit_style_notes=pref_row["explicit_style_notes"]
            )
        customers.append(CustomerDetail(
            id=cid,
            name=r["name"],
            email=r["email"],
            preferences=prefs,
            recent_purchases=[]
        ))
    return customers

@router.get("/{customer_id}", response_model=CustomerDetail)
def get_customer(customer_id: str, conn: sqlite3.Connection = Depends(get_db)):
    c_row = conn.execute("SELECT id, name, email FROM customers WHERE id = ?", (customer_id,)).fetchone()
    if not c_row:
        raise HTTPException(status_code=404, detail=f"Customer '{customer_id}' not found.")

    pref_row = conn.execute("SELECT * FROM customer_preferences WHERE customer_id = ?", (customer_id,)).fetchone()
    prefs = None
    if pref_row:
        prefs = CustomerPreferencesModel(
            preferred_size=pref_row["preferred_size"],
            preferred_fit=pref_row["preferred_fit"],
            preferred_colors=pref_row["preferred_colors"],
            preferred_materials=pref_row["preferred_materials"],
            budget_max=pref_row["budget_max"],
            explicit_style_notes=pref_row["explicit_style_notes"]
        )

    # Fetch purchases
    pur_query = """
        SELECT pu.id, pu.purchase_date, pu.price_paid, pu.rating,
               p.id as product_id, p.name as product_name, p.brand, p.category,
               pv.size, pv.color
        FROM purchases pu
        JOIN products p ON pu.product_id = p.id
        JOIN product_variants pv ON pu.variant_id = pv.id
        WHERE pu.customer_id = ?
        ORDER BY pu.purchase_date DESC
    """
    pur_rows = conn.execute(pur_query, (customer_id,)).fetchall()
    purchases = [dict(pur) for pur in pur_rows]

    return CustomerDetail(
        id=c_row["id"],
        name=c_row["name"],
        email=c_row["email"],
        preferences=prefs,
        recent_purchases=purchases
    )

@router.put("/{customer_id}/preferences", response_model=CustomerPreferencesModel)
def update_preferences(
    customer_id: str,
    preferences: CustomerPreferencesModel,
    conn: sqlite3.Connection = Depends(get_db)
):
    c_row = conn.execute("SELECT id FROM customers WHERE id = ?", (customer_id,)).fetchone()
    if not c_row:
        raise HTTPException(status_code=404, detail=f"Customer '{customer_id}' not found.")

    conn.execute(
        """
        INSERT INTO customer_preferences (customer_id, preferred_size, preferred_fit, preferred_colors, preferred_materials, budget_max, explicit_style_notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(customer_id) DO UPDATE SET
            preferred_size=excluded.preferred_size,
            preferred_fit=excluded.preferred_fit,
            preferred_colors=excluded.preferred_colors,
            preferred_materials=excluded.preferred_materials,
            budget_max=excluded.budget_max,
            explicit_style_notes=excluded.explicit_style_notes
        """,
        (
            customer_id,
            preferences.preferred_size,
            preferences.preferred_fit,
            preferences.preferred_colors,
            preferences.preferred_materials,
            preferences.budget_max,
            preferences.explicit_style_notes
        )
    )
    conn.commit()
    return preferences
