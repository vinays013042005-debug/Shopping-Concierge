from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class VariantDetail(BaseModel):
    id: str
    product_id: str
    size: str
    color: str
    sku: str
    price: float
    stock_quantity: int
    reserved_quantity: int
    is_available: bool

class ProductDetail(BaseModel):
    id: str
    name: str
    brand: str
    category: str
    gender: str
    base_price: float
    material: str
    fit_type: str
    occasion: str
    description: str
    image_url: str
    variants: List[VariantDetail] = []
    available_sizes: List[str] = []
    available_colors: List[str] = []
    in_stock: bool = True

class CustomerPreferencesModel(BaseModel):
    preferred_size: Optional[str] = None
    preferred_fit: Optional[str] = None
    preferred_colors: Optional[str] = None
    preferred_materials: Optional[str] = None
    budget_max: Optional[float] = None
    explicit_style_notes: Optional[str] = None

class CustomerDetail(BaseModel):
    id: str
    name: str
    email: str
    preferences: Optional[CustomerPreferencesModel] = None
    recent_purchases: List[Dict[str, Any]] = []

class ExtractedIntent(BaseModel):
    occasion: Optional[str] = None
    budget: Optional[float] = None
    category: Optional[str] = None
    color: Optional[str] = None
    material: Optional[str] = None
    fit_preference: Optional[str] = None
    size: Optional[str] = None
    customer_preferences: Optional[str] = None

class ChatRequest(BaseModel):
    message: str
    customer_id: Optional[str] = None
    manual_size: Optional[str] = None
    manual_budget: Optional[float] = None

class RecommendedProduct(BaseModel):
    id: str
    name: str
    brand: str
    category: str
    price: float
    material: str
    fit_type: str
    occasion: str
    image_url: str
    description: str
    available_sizes: List[str]
    matched_color: Optional[str] = None
    relevance_score: float
    match_reasons: List[str]

class ChatResponse(BaseModel):
    reply: str
    extracted_intent: ExtractedIntent
    recommendations: List[RecommendedProduct]
    guardrail_summary: Dict[str, Any]
    active_customer: Optional[str] = None
    llm_source: str = "ollama"

class SizeChartRow(BaseModel):
    id: int
    brand: str
    category: str
    gender: str
    size_label: str
    chest_min_cm: float
    chest_max_cm: float
    waist_min_cm: float
    waist_max_cm: float
    hip_min_cm: float
    hip_max_cm: float
    garment_chest_cm: float
    garment_waist_cm: float
    garment_hip_cm: float
    fit_type: str

class SizeEstimateResponse(BaseModel):
    success: bool
    confidence_level: str  # "high", "medium", "low", "uncalibrated"
    confidence_score: float  # 0.0 - 1.0
    recommended_size: str
    alternative_sizes: List[str]
    estimated_measurements_cm: Dict[str, float]
    proportions: Dict[str, float]
    brand_used: str
    category_used: str
    brand_size_chart: List[Dict[str, Any]] = []
    calibration_method: str
    notes: List[str]
    disclaimer: str

class HealthResponse(BaseModel):
    status: str
    ollama_connected: bool
    ollama_model: str
    ollama_details: Optional[Dict[str, Any]] = None
    vector_db_connected: bool
    vector_db_items_count: int
    sqlite_connected: bool
    total_products_count: int
