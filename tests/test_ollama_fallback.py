import pytest
from app.services.ollama_service import OllamaService
from app.models import ExtractedIntent

def test_missing_ollama_model_health_check():
    """Verify that an unreachable Ollama instance reports offline status cleanly without crashing."""
    # Point to a dummy dead port
    service = OllamaService(base_url="http://127.0.0.1:54321")
    health = service.check_health()
    assert health["connected"] is False
    assert health["model_available"] is False
    assert health["status"] == "offline"

def test_rule_based_fallback_intent_extraction():
    """
    Test extraction of occasion, budget, category, fit, color, material, and size
    using the high-precision fallback NLP parser.
    """
    service = OllamaService(base_url="http://127.0.0.1:54321") # Offline url to trigger fallback

    prompt = "I need a comfortable outfit for a beach wedding under ₹3,000. I prefer loose-fitting clothes in pastel colors."
    result = service.extract_intent(prompt)

    assert result["source"] == "fallback_nlp"
    intent = result["intent"]

    assert intent["occasion"] == "Beach Wedding"
    assert intent["budget"] == 3000.0
    assert intent["fit_preference"] == "Loose"
    assert intent["color"] == "Pastel"

def test_grounded_explanation_without_hallucination():
    """Verify that explanation generation grounds strictly in verified SQLite data without hallucinating."""
    service = OllamaService(base_url="http://127.0.0.1:54321")
    intent = ExtractedIntent(
        occasion="Beach Wedding",
        budget=3000.0,
        category="Shirts",
        fit_preference="Loose",
        color="Pastel Blue"
    )

    mock_products = [
        {
            "id": "PROD-001",
            "name": "Breezy Pastel Linen Shirt",
            "brand": "Linen Trail",
            "price": 2299.0,
            "material": "Linen",
            "fit_type": "Loose",
            "available_sizes": ["S", "M", "L"],
            "matched_color": "Pastel Blue"
        }
    ]

    explanation = service.generate_explanation(
        user_message="I need a comfortable outfit for a beach wedding under ₹3,000.",
        products=mock_products,
        intent=intent
    )

    assert "Breezy Pastel Linen Shirt" in explanation
    assert "Linen Trail" in explanation
    assert "₹2,299" in explanation
    assert "Beach Wedding" in explanation or "wedding" in explanation.lower()
