import sqlite3
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query, Depends
from app.database import get_db
from app.models import ProductDetail, VariantDetail

router = APIRouter(prefix="/api/products", tags=["Products"])

@router.get("", response_model=List[ProductDetail])
def list_products(
    category: Optional[str] = Query(None, description="Filter by clothing category"),
    max_price: Optional[float] = Query(None, description="Filter by maximum price"),
    fit_type: Optional[str] = Query(None, description="Filter by fit style"),
    occasion: Optional[str] = Query(None, description="Filter by occasion"),
    in_stock_only: bool = Query(True, description="Only return items with available stock"),
    conn: sqlite3.Connection = Depends(get_db)
):
    sql = """
        SELECT p.id, p.name, p.brand, p.category, p.gender, p.base_price,
               p.material, p.fit_type, p.occasion, p.description, p.image_url
        FROM products p
        WHERE 1=1
    """
    params = []

    if category:
        sql += " AND p.category = ?"
        params.append(category)
    if max_price:
        sql += " AND p.base_price <= ?"
        params.append(max_price)
    if fit_type:
        sql += " AND LOWER(p.fit_type) = LOWER(?)"
        params.append(fit_type)
    if occasion:
        sql += " AND LOWER(p.occasion) LIKE LOWER(?)"
        params.append(f"%{occasion}%")

    sql += " ORDER BY p.base_price ASC"
    rows = conn.execute(sql, params).fetchall()

    results = []
    for r in rows:
        pid = r["id"]
        # Fetch variants and inventory
        var_query = """
            SELECT pv.id, pv.product_id, pv.size, pv.color, pv.sku,
                   COALESCE(pv.price_override, ?) as price,
                   inv.stock_quantity, inv.reserved_quantity,
                   (inv.stock_quantity - inv.reserved_quantity) as net_stock
            FROM product_variants pv
            JOIN inventory inv ON pv.id = inv.variant_id
            WHERE pv.product_id = ?
        """
        v_rows = conn.execute(var_query, (r["base_price"], pid)).fetchall()
        variants = []
        available_sizes = []
        available_colors = []

        for v in v_rows:
            is_avail = (v["net_stock"] > 0)
            variants.append(VariantDetail(
                id=v["id"],
                product_id=v["product_id"],
                size=v["size"],
                color=v["color"],
                sku=v["sku"],
                price=float(v["price"]),
                stock_quantity=v["stock_quantity"],
                reserved_quantity=v["reserved_quantity"],
                is_available=is_avail
            ))
            if is_avail:
                if v["size"] not in available_sizes:
                    available_sizes.append(v["size"])
                if v["color"] not in available_colors:
                    available_colors.append(v["color"])

        has_stock = len(available_sizes) > 0
        if in_stock_only and not has_stock:
            continue

        results.append(ProductDetail(
            id=r["id"],
            name=r["name"],
            brand=r["brand"],
            category=r["category"],
            gender=r["gender"],
            base_price=float(r["base_price"]),
            material=r["material"],
            fit_type=r["fit_type"],
            occasion=r["occasion"],
            description=r["description"],
            image_url=r["image_url"],
            variants=variants,
            available_sizes=available_sizes,
            available_colors=available_colors,
            in_stock=has_stock
        ))

    return results

@router.get("/{product_id}", response_model=ProductDetail)
def get_product(product_id: str, conn: sqlite3.Connection = Depends(get_db)):
    row = conn.execute(
        "SELECT id, name, brand, category, gender, base_price, material, fit_type, occasion, description, image_url "
        "FROM products WHERE id = ?",
        (product_id,)
    ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail=f"Product with ID '{product_id}' not found.")

    var_query = """
        SELECT pv.id, pv.product_id, pv.size, pv.color, pv.sku,
               COALESCE(pv.price_override, ?) as price,
               inv.stock_quantity, inv.reserved_quantity,
               (inv.stock_quantity - inv.reserved_quantity) as net_stock
        FROM product_variants pv
        JOIN inventory inv ON pv.id = inv.variant_id
        WHERE pv.product_id = ?
    """
    v_rows = conn.execute(var_query, (row["base_price"], product_id)).fetchall()
    variants = []
    available_sizes = []
    available_colors = []

    for v in v_rows:
        is_avail = (v["net_stock"] > 0)
        variants.append(VariantDetail(
            id=v["id"],
            product_id=v["product_id"],
            size=v["size"],
            color=v["color"],
            sku=v["sku"],
            price=float(v["price"]),
            stock_quantity=v["stock_quantity"],
            reserved_quantity=v["reserved_quantity"],
            is_available=is_avail
        ))
        if is_avail:
            if v["size"] not in available_sizes:
                available_sizes.append(v["size"])
            if v["color"] not in available_colors:
                available_colors.append(v["color"])

    return ProductDetail(
        id=row["id"],
        name=row["name"],
        brand=row["brand"],
        category=row["category"],
        gender=row["gender"],
        base_price=float(row["base_price"]),
        material=row["material"],
        fit_type=row["fit_type"],
        occasion=row["occasion"],
        description=row["description"],
        image_url=row["image_url"],
        variants=variants,
        available_sizes=available_sizes,
        available_colors=available_colors,
        in_stock=(len(available_sizes) > 0)
    )
