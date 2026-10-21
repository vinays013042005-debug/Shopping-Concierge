import sqlite3
import logging
from typing import List, Dict, Any, Optional, Tuple
from app.database import get_connection

logger = logging.getLogger(__name__)

class InventoryGuardrail:
    """
    SQLite is the absolute source of truth for inventory, pricing, and variant availability.
    This guardrail enforces real-time stock checks, size availability, and budget verification
    prior to returning any recommendations to the user.
    """

    def __init__(self, db_path=None):
        self.db_path = db_path

    def inspect_and_filter(
        self,
        candidate_product_ids: List[str],
        budget_max: Optional[float] = None,
        required_size: Optional[str] = None,
        required_color: Optional[str] = None,
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Takes candidate product IDs from semantic search / RAG retrieval.
        Returns:
            (approved_products, rejected_products, suggested_alternatives)
        """
        if not candidate_product_ids:
            # If no candidates supplied, look for general in-stock alternatives
            alternatives = self._fetch_fallback_alternatives(budget_max)
            return [], [], alternatives

        conn = get_connection(self.db_path)
        approved = []
        rejected = []

        try:
            for pid in candidate_product_ids:
                # 1. Verify existence in SQLite
                p_row = conn.execute(
                    "SELECT id, name, brand, category, gender, base_price, material, fit_type, occasion, description, image_url "
                    "FROM products WHERE id = ?",
                    (pid,)
                ).fetchone()

                if not p_row:
                    rejected.append({
                        "product_id": pid,
                        "name": "Unknown",
                        "reason": "Product ID not found in SQLite product catalog."
                    })
                    continue

                product = dict(p_row)

                # 2. Query all active in-stock variants for this product
                # Only inventory where (stock_quantity - reserved_quantity) > 0 is considered available
                variants_query = """
                    SELECT pv.id as variant_id, pv.size, pv.color, pv.sku, pv.price_override,
                           inv.stock_quantity, inv.reserved_quantity,
                           (inv.stock_quantity - inv.reserved_quantity) as net_stock
                    FROM product_variants pv
                    JOIN inventory inv ON pv.id = inv.variant_id
                    WHERE pv.product_id = ? AND (inv.stock_quantity - inv.reserved_quantity) > 0
                """
                var_rows = conn.execute(variants_query, (pid,)).fetchall()

                if not var_rows:
                    rejected.append({
                        "product_id": pid,
                        "name": product["name"],
                        "reason": "Product is completely out of stock across all sizes and colors."
                    })
                    continue

                in_stock_variants = [dict(v) for v in var_rows]
                available_sizes = sorted(list(set(v["size"] for v in in_stock_variants)))
                available_colors = sorted(list(set(v["color"] for v in in_stock_variants)))

                # 3. Size constraint check
                if required_size:
                    req_size_upper = required_size.upper().strip()
                    matching_size_variants = [v for v in in_stock_variants if v["size"].upper() == req_size_upper]
                    if not matching_size_variants:
                        rejected.append({
                            "product_id": pid,
                            "name": product["name"],
                            "reason": f"Required size '{required_size}' is currently out of stock (available: {', '.join(available_sizes)})."
                        })
                        continue
                    in_stock_variants = matching_size_variants

                # 4. Color constraint check (optional filter)
                matched_color = None
                if required_color:
                    req_color_lower = required_color.lower().strip()
                    color_matches = [
                        v for v in in_stock_variants
                        if req_color_lower in v["color"].lower() or (req_color_lower == "pastel" and any(p in v["color"].lower() for p in ["pastel", "sage", "blush", "mint", "ivory", "beige"]))
                    ]
                    if color_matches:
                        in_stock_variants = color_matches
                        matched_color = in_stock_variants[0]["color"]
                    else:
                        # Soft preference, don't necessarily reject if color is close
                        matched_color = in_stock_variants[0]["color"]
                else:
                    matched_color = in_stock_variants[0]["color"]

                # 5. Price verification from SQLite (source of truth)
                # Compute effective price for the eligible variants
                effective_prices = [
                    v["price_override"] if v["price_override"] is not None else product["base_price"]
                    for v in in_stock_variants
                ]
                current_price = min(effective_prices) if effective_prices else product["base_price"]

                # 6. Budget constraint enforcement
                if budget_max is not None and budget_max > 0:
                    if current_price > budget_max:
                        rejected.append({
                            "product_id": pid,
                            "name": product["name"],
                            "reason": f"Real-time SQLite price (₹{current_price:,.0f}) exceeds the user's budget ceiling of ₹{budget_max:,.0f}."
                        })
                        continue

                # Passed all guardrails!
                product["price"] = current_price
                product["available_sizes"] = available_sizes
                product["available_colors"] = available_colors
                product["matched_color"] = matched_color
                product["eligible_variants"] = in_stock_variants
                approved.append(product)

        finally:
            conn.close()

        # If approved list is empty or very small, find available in-stock alternatives
        alternatives = []
        if len(approved) == 0:
            alternatives = self._fetch_fallback_alternatives(budget_max, required_size)

        return approved, rejected, alternatives

    def _fetch_fallback_alternatives(
        self,
        budget_max: Optional[float] = None,
        required_size: Optional[str] = None,
        limit: int = 3
    ) -> List[Dict[str, Any]]:
        """Finds in-stock alternative products when all candidates fail guardrails."""
        conn = get_connection(self.db_path)
        alternatives = []
        try:
            # Query in-stock products, optionally with budget headroom +25%
            max_p = (budget_max * 1.25) if budget_max else 100000.0
            query = """
                SELECT p.id, p.name, p.brand, p.category, p.gender, p.base_price, p.material,
                       p.fit_type, p.occasion, p.description, p.image_url,
                       GROUP_CONCAT(DISTINCT pv.size) as sizes,
                       GROUP_CONCAT(DISTINCT pv.color) as colors
                FROM products p
                JOIN product_variants pv ON p.id = pv.product_id
                JOIN inventory inv ON pv.id = inv.variant_id
                WHERE (inv.stock_quantity - inv.reserved_quantity) > 0
                  AND p.base_price <= ?
                GROUP BY p.id
                ORDER BY p.base_price ASC
                LIMIT ?
            """
            rows = conn.execute(query, (max_p, limit)).fetchall()
            for r in rows:
                item = dict(r)
                item["price"] = item["base_price"]
                item["available_sizes"] = item["sizes"].split(",") if item["sizes"] else []
                item["available_colors"] = item["colors"].split(",") if item["colors"] else []
                item["matched_color"] = item["available_colors"][0] if item["available_colors"] else None
                alternatives.append(item)
        except Exception as e:
            logger.error(f"Error fetching fallback alternatives: {e}")
        finally:
            conn.close()

        return alternatives

inventory_guardrail = InventoryGuardrail()
