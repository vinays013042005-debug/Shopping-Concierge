import re
import json
import logging
from typing import Dict, Any, Optional, List
import requests
from app.config import OLLAMA_BASE_URL, OLLAMA_MODEL, OLLAMA_TIMEOUT_SECONDS
from app.models import ExtractedIntent

logger = logging.getLogger(__name__)

INTENT_EXTRACTION_PROMPT = """You are a senior fashion stylist and retail AI concierge.
Analyze the user's shopping request and extract their specific shopping constraints and style preferences.
Return ONLY valid JSON matching this exact structure:
{{
  "occasion": "beach wedding / casual / formal / etc or null",
  "budget": 3000.0 or null (number only, in INR ₹),
  "category": "shirt / dress / kurta / trousers / etc or null",
  "color": "pastel / blue / green / etc or null",
  "material": "linen / cotton / silk / etc or null",
  "fit_preference": "loose / slim / regular / relaxed or null",
  "size": "XS / S / M / L / XL / XXL or null",
  "customer_preferences": "summary of additional style preferences or null"
}}

User Request: "{user_message}"
JSON:"""

EXPLANATION_PROMPT = """You are a warm, knowledgeable personal retail fashion concierge.
The customer requested: "{user_message}"

We have verified our current SQLite inventory and found these in-stock products matching their criteria:
{products_summary}

Write a concise, polished response (2-4 sentences) presenting these options to the customer.
IMPORTANT RULES:
1. Ground your explanation ONLY in the exact product names, prices, colors, materials, and fits provided above.
2. NEVER invent product names, prices, discounts, or stock details.
3. Highlight how the items specifically fulfill their occasion, budget, fit, or color preferences.
"""

class OllamaService:
    def __init__(self, base_url: str = OLLAMA_BASE_URL, model: str = OLLAMA_MODEL):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = OLLAMA_TIMEOUT_SECONDS

    def check_health(self) -> Dict[str, Any]:
        """Check if Ollama server is running and if the model is available."""
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=3)
            if resp.status_code == 200:
                data = resp.json()
                models = [m.get("name", "") for m in data.get("models", [])]
                model_found = any(self.model in m for m in models)
                return {
                    "connected": True,
                    "model_available": model_found,
                    "target_model": self.model,
                    "available_models": models,
                    "status": "online" if model_found else "model_not_pulled"
                }
        except Exception as e:
            logger.warning(f"Ollama health check failed: {e}")
        return {
            "connected": False,
            "model_available": False,
            "target_model": self.model,
            "available_models": [],
            "status": "offline"
        }

    def extract_intent(self, user_message: str) -> Dict[str, Any]:
        """
        Attempts to extract shopping intent via Ollama.
        Gracefully falls back to heuristic/regex NLP parser if Ollama is unreachable.
        """
        health = self.check_health()
        if health["connected"] and health["model_available"]:
            try:
                payload = {
                    "model": self.model,
                    "prompt": INTENT_EXTRACTION_PROMPT.format(user_message=user_message),
                    "stream": False,
                    "options": {
                        "temperature": 0.1,
                        "num_predict": 256
                    }
                }
                resp = requests.post(f"{self.base_url}/api/generate", json=payload, timeout=self.timeout)
                if resp.status_code == 200:
                    raw_text = resp.json().get("response", "").strip()
                    # Clean markdown code blocks if any
                    cleaned = re.sub(r"^```(?:json)?\s*", "", raw_text, flags=re.MULTILINE)
                    cleaned = re.sub(r"\s*```$", "", cleaned, flags=re.MULTILINE).strip()
                    parsed = json.loads(cleaned)
                    return {
                        "intent": self._sanitize_intent(parsed),
                        "source": "ollama"
                    }
            except Exception as e:
                logger.warning(f"Ollama intent extraction failed or timed out: {e}. Falling back to rule-based parser.")
        
        # Fallback parser
        fallback_data = self._rule_based_extract(user_message)
        return {
            "intent": fallback_data,
            "source": "fallback_nlp"
        }

    def generate_explanation(self, user_message: str, products: List[Dict[str, Any]], intent: ExtractedIntent) -> str:
        """
        Generates a natural shopping response.
        Falls back to deterministic template generation if Ollama is unavailable.
        """
        if not products:
            budget_str = f" under ₹{int(intent.budget):,}" if intent.budget else ""
            category_str = f" in {intent.category}" if intent.category else ""
            return (
                f"I looked through our current inventory, but I couldn't find available items matching all your criteria"
                f"{category_str}{budget_str}. I've adjusted the filters to show the closest available styles below."
            )

        health = self.check_health()
        if health["connected"] and health["model_available"]:
            try:
                products_summary = "\n".join([
                    f"- {p['name']} ({p['brand']}): ₹{p['price']:.0f}, {p['material']}, {p['fit_type']} fit, "
                    f"colors: {p.get('matched_color') or 'Multiple'}, sizes: {', '.join(p['available_sizes'])}. "
                    f"Description: {p['description']}"
                    for p in products[:4]
                ])
                payload = {
                    "model": self.model,
                    "prompt": EXPLANATION_PROMPT.format(
                        user_message=user_message,
                        products_summary=products_summary
                    ),
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "num_predict": 300
                    }
                }
                resp = requests.post(f"{self.base_url}/api/generate", json=payload, timeout=self.timeout)
                if resp.status_code == 200:
                    text = resp.json().get("response", "").strip()
                    if text:
                        return text
            except Exception as e:
                logger.warning(f"Ollama explanation generation failed: {e}. Using deterministic explanation.")

        # Grounded rule-based explanation
        top_prod = products[0]
        count = len(products)
        fit_phrase = f"with a relaxed {top_prod['fit_type'].lower()} fit" if top_prod.get('fit_type') else ""
        material_phrase = f"crafted from breathable {top_prod.get('material', '').lower()}" if top_prod.get('material') else ""
        desc_pieces = [p for p in [material_phrase, fit_phrase] if p]
        desc_comb = " and ".join(desc_pieces)
        
        reply = (
            f"Here are {count} curated options matching your request! "
            f"The top recommendation is the **{top_prod['name']}** from {top_prod['brand']} at ₹{top_prod['price']:,.0f}"
            f"{f' ({desc_comb})' if desc_comb else ''}. "
            f"It aligns perfectly with your {intent.occasion or 'planned'} event and is currently in stock in sizes: {', '.join(top_prod['available_sizes'])}."
        )
        return reply

    def _sanitize_intent(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Cleans and validates the parsed dictionary from LLM."""
        sanitized = {}
        # Budget
        budget = data.get("budget")
        if budget is not None:
            try:
                if isinstance(budget, (int, float)):
                    sanitized["budget"] = float(budget)
                else:
                    # extract numeric
                    num = re.findall(r"\d+", str(budget).replace(",", ""))
                    if num:
                        sanitized["budget"] = float(num[0])
                    else:
                        sanitized["budget"] = None
            except Exception:
                sanitized["budget"] = None
        else:
            sanitized["budget"] = None

        # String fields
        for field in ["occasion", "category", "color", "material", "fit_preference", "size", "customer_preferences"]:
            val = data.get(field)
            if val and str(val).strip().lower() not in ["null", "none", "n/a", ""]:
                sanitized[field] = str(val).strip()
            else:
                sanitized[field] = None

        return sanitized

    def _rule_based_extract(self, message: str) -> Dict[str, Any]:
        """High-precision heuristic NLP parser for shopping queries."""
        text = message.lower()
        intent = {
            "occasion": None,
            "budget": None,
            "category": None,
            "color": None,
            "material": None,
            "fit_preference": None,
            "size": None,
            "customer_preferences": None
        }

        # 1. Budget extraction (e.g. "under ₹3,000", "below 3000", "max 2500", "under 3000", "budget 4000")
        budget_match = re.search(
            r"(?:under|below|less\s+than|within|max|budget\s*(?:of|is|:)?)\s*(?:₹|rs\.?|inr)?\s*([0-9]{1,3}(?:,[0-9]{3})*|[0-9]+)",
            text
        )
        if not budget_match:
            # check for "3000 rs" or "₹ 3000"
            budget_match = re.search(r"(?:₹|rs\.?)\s*([0-9]{1,3}(?:,[0-9]{3})*|[0-9]+)", text)

        if budget_match:
            try:
                raw_budget = budget_match.group(1).replace(",", "")
                intent["budget"] = float(raw_budget)
            except ValueError:
                pass

        # 2. Occasion
        occasions = [
            ("beach wedding", "Beach Wedding"),
            ("destination wedding", "Beach Wedding"),
            ("beach party", "Beach"),
            ("wedding", "Wedding"),
            ("cocktail", "Cocktail"),
            ("formal", "Formal"),
            ("office", "Formal"),
            ("work", "Formal"),
            ("casual", "Casual"),
            ("party", "Party"),
            ("festive", "Festive"),
            ("summer", "Summer / Resort"),
            ("resort", "Resort Wear")
        ]
        for term, label in occasions:
            if re.search(rf"\b{re.escape(term)}\b", text):
                intent["occasion"] = label
                break

        # 3. Category
        categories = [
            ("shirt", "Shirts"),
            ("shirts", "Shirts"),
            ("dress", "Dresses"),
            ("dresses", "Dresses"),
            ("kurta", "Kurtas"),
            ("kurtas", "Kurtas"),
            ("trouser", "Trousers"),
            ("trousers", "Trousers"),
            ("pant", "Trousers"),
            ("pants", "Trousers"),
            ("blazer", "Blazers"),
            ("blazers", "Blazers"),
            ("suit", "Blazers"),
            ("t-shirt", "T-Shirts"),
            ("tshirt", "T-Shirts"),
            ("outfit", "Outfit"),
            ("clothes", "Apparel")
        ]
        for term, label in categories:
            if re.search(rf"\b{re.escape(term)}\b", text):
                intent["category"] = label
                break

        # 4. Color / Palette
        colors = [
            ("pastel", "Pastel"),
            ("pastel blue", "Pastel Blue"),
            ("sage green", "Sage Green"),
            ("blush pink", "Blush Pink"),
            ("mint green", "Mint Green"),
            ("blue", "Blue"),
            ("green", "Green"),
            ("pink", "Pink"),
            ("beige", "Beige"),
            ("white", "White"),
            ("ivory", "Ivory"),
            ("navy", "Navy"),
            ("black", "Black"),
            ("yellow", "Yellow"),
            ("coral", "Coral"),
            ("olive", "Olive")
        ]
        for term, label in colors:
            if re.search(rf"\b{re.escape(term)}\b", text):
                intent["color"] = label
                break

        # 5. Material
        materials = [
            ("linen", "Linen"),
            ("cotton", "Cotton"),
            ("silk blend", "Silk Blend"),
            ("silk", "Silk"),
            ("viscose", "Viscose"),
            ("chambray", "Chambray"),
            ("satin", "Satin"),
            ("wool", "Wool")
        ]
        for term, label in materials:
            if re.search(rf"\b{re.escape(term)}\b", text):
                intent["material"] = label
                break

        # 6. Fit preference
        fits = [
            ("loose-fitting", "Loose"),
            ("loose fitting", "Loose"),
            ("loose", "Loose"),
            ("relaxed", "Relaxed"),
            ("oversized", "Oversized"),
            ("slim-fit", "Slim"),
            ("slim fit", "Slim"),
            ("slim", "Slim"),
            ("regular-fit", "Regular"),
            ("regular", "Regular")
        ]
        for term, label in fits:
            if re.search(rf"\b{re.escape(term)}\b", text):
                intent["fit_preference"] = label
                break

        # 7. Size
        size_match = re.search(r"\b(?:size\s+)?(XXL|XL|L|M|S|XS)\b", message)
        if size_match:
            intent["size"] = size_match.group(1).upper()

        # 8. Extra notes
        if "pastel" in text and intent["color"] is None:
            intent["color"] = "Pastel"

        intent["customer_preferences"] = message.strip()
        return intent

ollama_service = OllamaService()
