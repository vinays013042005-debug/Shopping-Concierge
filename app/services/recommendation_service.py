import sqlite3
import logging
from typing import Dict, Any, List, Optional
from app.models import ChatRequest, ChatResponse, ExtractedIntent, RecommendedProduct
from app.services.ollama_service import ollama_service
from app.services.retrieval_service import retrieval_service
from app.services.inventory_guardrail import inventory_guardrail
from app.database import get_connection

logger = logging.getLogger(__name__)

class RecommendationService:
    def __init__(self, db_path=None):
        self.db_path = db_path

    def process_chat(self, request: ChatRequest) -> ChatResponse:
        user_message = request.message.strip()

        # 1. Intent Extraction
        intent_result = ollama_service.extract_intent(user_message)
        raw_intent = intent_result["intent"]
        source = intent_result["source"]

        intent = ExtractedIntent(**raw_intent)

        # Override with manual inputs from UI if provided
        if request.manual_size:
            intent.size = request.manual_size
        if request.manual_budget:
            intent.budget = request.manual_budget

        # 2. Customer Personalization profile lookup
        customer_prefs = None
        past_brands = set()
        if request.customer_id:
            customer_prefs, past_brands = self._get_customer_context(request.customer_id)

        # Merge customer preferences if user didn't explicitly override
        active_budget = intent.budget
        active_size = intent.size
        active_fit = intent.fit_preference
        preferred_colors = []
        preferred_materials = []

        if customer_prefs:
            if not active_budget and customer_prefs.get("budget_max"):
                active_budget = float(customer_prefs["budget_max"])
            if not active_size and customer_prefs.get("preferred_size"):
                active_size = customer_prefs["preferred_size"]
            if not active_fit and customer_prefs.get("preferred_fit"):
                active_fit = customer_prefs["preferred_fit"]
            if customer_prefs.get("preferred_colors"):
                preferred_colors = [c.strip().lower() for c in customer_prefs["preferred_colors"].split(",")]
            if customer_prefs.get("preferred_materials"):
                preferred_materials = [m.strip().lower() for m in customer_prefs["preferred_materials"].split(",")]

        # 3. Formulate RAG query string
        query_terms = [user_message]
        if intent.occasion:
            query_terms.append(f"occasion {intent.occasion}")
        if intent.fit_preference or active_fit:
            query_terms.append(f"fit {intent.fit_preference or active_fit}")
        if intent.material:
            query_terms.append(f"material {intent.material}")
        if intent.color:
            query_terms.append(f"color {intent.color}")
        rag_query = " ".join(query_terms)

        # 4. Semantic vector retrieval
        candidates = retrieval_service.search_candidates(
            query_text=rag_query,
            n_results=12,
            category=intent.category,
            db_path=self.db_path
        )
        candidate_ids = [c["product_id"] for c in candidates]
        sim_scores = {c["product_id"]: c["similarity_score"] for c in candidates}

        # 5. Inventory & Budget Guardrail (SQLite as source of truth)
        approved_products, rejected_products, alternatives = inventory_guardrail.inspect_and_filter(
            candidate_product_ids=candidate_ids,
            budget_max=active_budget,
            required_size=active_size,
            required_color=intent.color
        )

        target_pool = approved_products if approved_products else alternatives

        # 6. Re-ranking based on semantic relevance + customer personalization
        ranked_products = []
        for p in target_pool:
            pid = p["id"]
            base_score = sim_scores.get(pid, 0.60)
            bonus = 0.0
            reasons = []

            # Check fit match
            if active_fit and (active_fit.lower() in p.get("fit_type", "").lower() or p.get("fit_type", "").lower() in active_fit.lower()):
                bonus += 0.20
                reasons.append(f"Matches your '{active_fit}' fit preference")

            # Check material match
            if intent.material and intent.material.lower() in p.get("material", "").lower():
                bonus += 0.20
                reasons.append(f"Crafted from requested {p['material']}")
            elif preferred_materials and any(m in p.get("material", "").lower() for m in preferred_materials):
                bonus += 0.10
                reasons.append(f"Matches your preferred {p['material']} fabric")

            # Check size match
            if active_size and active_size in p.get("available_sizes", []):
                bonus += 0.15
                reasons.append(f"Verified in stock in your size {active_size}")

            # Check color match
            if intent.color:
                reasons.append(f"Available in {p.get('matched_color') or intent.color}")
            elif preferred_colors and any(c in str(p.get("available_colors", [])).lower() for c in preferred_colors):
                bonus += 0.10
                reasons.append("Matches your preferred color palette")

            # Occasion match
            if intent.occasion and (intent.occasion.lower() in p.get("occasion", "").lower() or intent.occasion.lower() in p.get("description", "").lower()):
                bonus += 0.15
                reasons.append(f"Tailored for {p['occasion']}")

            # Budget adherence
            if active_budget:
                reasons.append(f"Priced at ₹{p['price']:,.0f} (within ₹{active_budget:,.0f} budget)")
            else:
                reasons.append(f"Priced at ₹{p['price']:,.0f}")

            # Previous brand loyalty bonus
            if p.get("brand") in past_brands:
                bonus += 0.10
                reasons.append(f"From your favored brand {p['brand']}")

            final_score = min(1.0, round(base_score + bonus, 4))

            ranked_products.append(RecommendedProduct(
                id=p["id"],
                name=p["name"],
                brand=p["brand"],
                category=p["category"],
                price=float(p["price"]),
                material=p["material"],
                fit_type=p["fit_type"],
                occasion=p["occasion"],
                image_url=p["image_url"],
                description=p["description"],
                available_sizes=p["available_sizes"],
                matched_color=p.get("matched_color"),
                relevance_score=final_score,
                match_reasons=reasons
            ))

        ranked_products.sort(key=lambda x: x.relevance_score, reverse=True)

        # 7. Generate grounded explanation
        products_for_explanation = [r.model_dump() for r in ranked_products[:4]]
        reply_text = ollama_service.generate_explanation(
            user_message=user_message,
            products=products_for_explanation,
            intent=intent
        )

        guardrail_summary = {
            "candidate_count": len(candidate_ids),
            "approved_count": len(approved_products),
            "rejected_count": len(rejected_products),
            "rejected_details": rejected_products,
            "alternatives_suggested": len(alternatives) > 0 and len(approved_products) == 0,
            "applied_budget_ceiling": active_budget,
            "applied_size_filter": active_size
        }

        return ChatResponse(
            reply=reply_text,
            extracted_intent=intent,
            recommendations=ranked_products[:6],
            guardrail_summary=guardrail_summary,
            active_customer=request.customer_id,
            llm_source=source
        )

    def _get_customer_context(self, customer_id: str):
        conn = get_connection(self.db_path)
        prefs = None
        past_brands = set()
        try:
            p_row = conn.execute("SELECT * FROM customer_preferences WHERE customer_id = ?", (customer_id,)).fetchone()
            if p_row:
                prefs = dict(p_row)

            # Check purchase history
            b_rows = conn.execute(
                "SELECT DISTINCT p.brand FROM purchases pu JOIN products p ON pu.product_id = p.id WHERE pu.customer_id = ?",
                (customer_id,)
            ).fetchall()
            for b in b_rows:
                past_brands.add(b["brand"])
        finally:
            conn.close()
        return prefs, past_brands

recommendation_service = RecommendationService()
