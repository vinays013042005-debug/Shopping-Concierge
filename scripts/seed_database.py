"""
Database Initialization and Seeding Script for Hyper-Personalized Retail Concierge.
Safely initializes tables and populates realistic apparel, variants, inventory,
size charts, customers, and purchase histories without duplication.
"""

import sqlite3
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import DB_PATH
from app.database import init_db, get_connection

SAMPLE_PRODUCTS = [
    {
        "id": "PROD-001",
        "name": "Breezy Pastel Linen Shirt",
        "brand": "Linen Trail",
        "category": "Shirts",
        "gender": "Men",
        "base_price": 2299.0,
        "material": "Linen",
        "fit_type": "Loose",
        "occasion": "Beach Wedding",
        "description": "Ultralight breathable pure European flax linen button-down with a relaxed silhouette, mandarin collar, and airy pastel drape ideal for beach weddings and warm coastal celebrations.",
        "image_url": "https://images.unsplash.com/photo-1596755094514-f87e34085b2c?w=500&auto=format&fit=crop&q=80",
        "variants": [
            {"size": "S", "color": "Pastel Blue", "stock": 8, "reserved": 0},
            {"size": "M", "color": "Pastel Blue", "stock": 12, "reserved": 1},
            {"size": "L", "color": "Pastel Blue", "stock": 5, "reserved": 0},
            {"size": "XL", "color": "Pastel Blue", "stock": 0, "reserved": 0},  # Out of stock for testing
            {"size": "M", "color": "Sage Green", "stock": 6, "reserved": 0},
            {"size": "L", "color": "Sage Green", "stock": 4, "reserved": 0},
        ]
    },
    {
        "id": "PROD-002",
        "name": "Sage Slub Cotton Resort Shirt",
        "brand": "Coastal Breeze",
        "category": "Shirts",
        "gender": "Men",
        "base_price": 1799.0,
        "material": "Cotton",
        "fit_type": "Relaxed",
        "occasion": "Beach Wedding",
        "description": "Textured slub cotton camp-collar shirt in subtle sage green. Airy open weave provides effortless comfort for coastal celebrations and warm outdoor dinners.",
        "image_url": "https://images.unsplash.com/photo-1602810318383-e386cc2a3ccf?w=500&auto=format&fit=crop&q=80",
        "variants": [
            {"size": "S", "color": "Sage Green", "stock": 6, "reserved": 0},
            {"size": "M", "color": "Sage Green", "stock": 10, "reserved": 0},
            {"size": "L", "color": "Sage Green", "stock": 7, "reserved": 0},
            {"size": "XL", "color": "Sage Green", "stock": 3, "reserved": 0},
            {"size": "M", "color": "Pastel Pink", "stock": 5, "reserved": 0},
        ]
    },
    {
        "id": "PROD-003",
        "name": "Ivory Linen Spread-Collar Shirt",
        "brand": "Nordic Pure",
        "category": "Shirts",
        "gender": "Men",
        "base_price": 2799.0,
        "material": "Linen",
        "fit_type": "Loose",
        "occasion": "Beach Wedding",
        "description": "Classic ivory relaxed-fit linen shirt featuring mother-of-pearl buttons, curved hemline, and moisture-wicking natural linen drape.",
        "image_url": "https://images.unsplash.com/photo-1598033129183-c4f50c736f10?w=500&auto=format&fit=crop&q=80",
        "variants": [
            {"size": "S", "color": "Ivory", "stock": 4, "reserved": 0},
            {"size": "M", "color": "Ivory", "stock": 9, "reserved": 0},
            {"size": "L", "color": "Ivory", "stock": 8, "reserved": 1},
            {"size": "XL", "color": "Ivory", "stock": 2, "reserved": 0},
        ]
    },
    {
        "id": "PROD-004",
        "name": "Royal Silk-Blend Evening Shirt",
        "brand": "Aura Studio",
        "category": "Shirts",
        "gender": "Men",
        "base_price": 4200.0,
        "material": "Silk Blend",
        "fit_type": "Slim",
        "occasion": "Formal",
        "description": "Lustrous woven silk-blend evening shirt with French cuffs and structured tailoring, tailored for black-tie galas and sophisticated evening dinners.",
        "image_url": "https://images.unsplash.com/photo-1620012253295-c15c429f66bf?w=500&auto=format&fit=crop&q=80",
        "variants": [
            {"size": "S", "color": "Midnight Black", "stock": 3, "reserved": 0},
            {"size": "M", "color": "Midnight Black", "stock": 5, "reserved": 0},
            {"size": "L", "color": "Midnight Black", "stock": 4, "reserved": 0},
        ]
    },
    {
        "id": "PROD-005",
        "name": "Blush Floral Chiffon Maxi Dress",
        "brand": "Aura Studio",
        "category": "Dresses",
        "gender": "Women",
        "base_price": 2899.0,
        "material": "Viscose",
        "fit_type": "Loose",
        "occasion": "Beach Wedding",
        "description": "Tiered pastel blush maxi dress crafted from breathable lightweight chiffon with fluttering sleeve accents and flowy seaside movement.",
        "image_url": "https://images.unsplash.com/photo-1572804013309-59a88b7e92f1?w=500&auto=format&fit=crop&q=80",
        "variants": [
            {"size": "XS", "color": "Blush Pink", "stock": 3, "reserved": 0},
            {"size": "S", "color": "Blush Pink", "stock": 7, "reserved": 0},
            {"size": "M", "color": "Blush Pink", "stock": 11, "reserved": 1},
            {"size": "L", "color": "Blush Pink", "stock": 6, "reserved": 0},
        ]
    },
    {
        "id": "PROD-006",
        "name": "Pastel Lemon Cotton Sundress",
        "brand": "Coastal Breeze",
        "category": "Dresses",
        "gender": "Women",
        "base_price": 2199.0,
        "material": "Cotton",
        "fit_type": "Relaxed",
        "occasion": "Beach Wedding",
        "description": "Sunlit pastel yellow tiered cotton dress featuring smocked bodice, functional pockets, and breezy flared hemline suited for outdoor destination weddings.",
        "image_url": "https://images.unsplash.com/photo-1515372039744-b8f02a3ae446?w=500&auto=format&fit=crop&q=80",
        "variants": [
            {"size": "S", "color": "Pastel Lemon", "stock": 6, "reserved": 0},
            {"size": "M", "color": "Pastel Lemon", "stock": 8, "reserved": 0},
            {"size": "L", "color": "Pastel Lemon", "stock": 5, "reserved": 0},
        ]
    },
    {
        "id": "PROD-007",
        "name": "Emerald Silk Slip Midi Dress",
        "brand": "Velvet & Vine",
        "category": "Dresses",
        "gender": "Women",
        "base_price": 4500.0,
        "material": "Silk",
        "fit_type": "Slim",
        "occasion": "Cocktail",
        "description": "Bias-cut mulberry silk midi dress with cowl neckline and delicate crisscross back straps, ideal for evening cocktail parties and celebrations.",
        "image_url": "https://images.unsplash.com/photo-1595777457583-95e059d581b8?w=500&auto=format&fit=crop&q=80",
        "variants": [
            {"size": "S", "color": "Emerald Green", "stock": 4, "reserved": 0},
            {"size": "M", "color": "Emerald Green", "stock": 6, "reserved": 0},
            {"size": "L", "color": "Emerald Green", "stock": 2, "reserved": 0},
        ]
    },
    {
        "id": "PROD-008",
        "name": "Pleated Linen Drawstring Trousers",
        "brand": "Linen Trail",
        "category": "Trousers",
        "gender": "Unisex",
        "base_price": 2499.0,
        "material": "Linen",
        "fit_type": "Loose",
        "occasion": "Beach Wedding",
        "description": "Relaxed pleated trousers with elasticated drawstring waistband in ecru beige. Breathable wide-leg design for seamless beach mobility and tropical breeze.",
        "image_url": "https://images.unsplash.com/photo-1624378439575-d8705ad7ae80?w=500&auto=format&fit=crop&q=80",
        "variants": [
            {"size": "S", "color": "Ecru Beige", "stock": 5, "reserved": 0},
            {"size": "M", "color": "Ecru Beige", "stock": 9, "reserved": 0},
            {"size": "L", "color": "Ecru Beige", "stock": 8, "reserved": 0},
            {"size": "XL", "color": "Ecru Beige", "stock": 3, "reserved": 0},
        ]
    },
    {
        "id": "PROD-009",
        "name": "Slim-Fit Chino Trousers",
        "brand": "Nordic Pure",
        "category": "Trousers",
        "gender": "Men",
        "base_price": 2699.0,
        "material": "Cotton",
        "fit_type": "Slim",
        "occasion": "Casual",
        "description": "Structured stretch-cotton chinos in navy blue with tapered ankle and clean front pockets. Versatile smart casual essential.",
        "image_url": "https://images.unsplash.com/photo-1473966968600-fa801b869a1a?w=500&auto=format&fit=crop&q=80",
        "variants": [
            {"size": "M", "color": "Navy", "stock": 7, "reserved": 0},
            {"size": "L", "color": "Navy", "stock": 8, "reserved": 0},
        ]
    },
    {
        "id": "PROD-010",
        "name": "Pastel Mint Embroidered Kurta",
        "brand": "Riwaayat",
        "category": "Kurtas",
        "gender": "Men",
        "base_price": 2799.0,
        "material": "Cotton",
        "fit_type": "Loose",
        "occasion": "Festive",
        "description": "Fine handloom cotton kurta featuring subtle tonal thread embroidery around the placket and cuffs in soothing pastel mint green. Perfect for wedding sangeet and haldi.",
        "image_url": "https://images.unsplash.com/photo-1583391733956-3750e0ff4e8b?w=500&auto=format&fit=crop&q=80",
        "variants": [
            {"size": "S", "color": "Pastel Mint", "stock": 4, "reserved": 0},
            {"size": "M", "color": "Pastel Mint", "stock": 10, "reserved": 0},
            {"size": "L", "color": "Pastel Mint", "stock": 7, "reserved": 0},
            {"size": "XL", "color": "Pastel Mint", "stock": 3, "reserved": 0},
        ]
    },
    {
        "id": "PROD-011",
        "name": "Raw Silk Festive Kurta Set",
        "brand": "Riwaayat",
        "category": "Kurtas",
        "gender": "Men",
        "base_price": 5499.0,
        "material": "Silk Blend",
        "fit_type": "Regular",
        "occasion": "Festive",
        "description": "Rich raw-silk blend kurta paired with churidar trousers, featuring antique metallic buttons and mandarin collar for celebratory occasions.",
        "image_url": "https://images.unsplash.com/photo-1610030469983-98e550d6193c?w=500&auto=format&fit=crop&q=80",
        "variants": [
            {"size": "M", "color": "Golden Ivory", "stock": 4, "reserved": 0},
            {"size": "L", "color": "Golden Ivory", "stock": 3, "reserved": 0},
        ]
    },
    {
        "id": "PROD-012",
        "name": "Unstructured Linen Summer Blazer",
        "brand": "Nordic Pure",
        "category": "Blazers",
        "gender": "Men",
        "base_price": 4999.0,
        "material": "Linen",
        "fit_type": "Regular",
        "occasion": "Beach Wedding",
        "description": "Lightweight unlined summer blazer tailored from Irish flax linen. Soft natural shoulders and patch pockets offer refined coastal elegance for seaside weddings.",
        "image_url": "https://images.unsplash.com/photo-1507679799987-c73779587ccf?w=500&auto=format&fit=crop&q=80",
        "variants": [
            {"size": "M", "color": "Sandstone Beige", "stock": 3, "reserved": 0},
            {"size": "L", "color": "Sandstone Beige", "stock": 4, "reserved": 0},
        ]
    },
    {
        "id": "PROD-013",
        "name": "Organic Pima Cotton Tee",
        "brand": "Coastal Breeze",
        "category": "T-Shirts",
        "gender": "Unisex",
        "base_price": 999.0,
        "material": "Cotton",
        "fit_type": "Relaxed",
        "occasion": "Casual",
        "description": "Ultra-soft heavyweight Peruvian Pima cotton crewneck t-shirt in washed pastel sage. Enduring everyday comfort.",
        "image_url": "https://images.unsplash.com/photo-1521572267360-ee0c2909d518?w=500&auto=format&fit=crop&q=80",
        "variants": [
            {"size": "S", "color": "Pastel Sage", "stock": 15, "reserved": 0},
            {"size": "M", "color": "Pastel Sage", "stock": 20, "reserved": 2},
            {"size": "L", "color": "Pastel Sage", "stock": 18, "reserved": 0},
            {"size": "XL", "color": "Pastel Sage", "stock": 10, "reserved": 0},
        ]
    },
    {
        "id": "PROD-014",
        "name": "Vintage Washed Oversized T-Shirt",
        "brand": "Urban Edge",
        "category": "T-Shirts",
        "gender": "Unisex",
        "base_price": 1299.0,
        "material": "Cotton",
        "fit_type": "Oversized",
        "occasion": "Casual",
        "description": "Heavyweight 240 GSM combed cotton tee featuring dropped shoulders, ribbed collar, and relaxed streetwear fit.",
        "image_url": "https://images.unsplash.com/photo-1503342217505-b0a15ec3261c?w=500&auto=format&fit=crop&q=80",
        "variants": [
            {"size": "M", "color": "Washed Charcoal", "stock": 8, "reserved": 0},
            {"size": "L", "color": "Washed Charcoal", "stock": 12, "reserved": 0},
            {"size": "XL", "color": "Washed Charcoal", "stock": 7, "reserved": 0},
        ]
    },
    {
        "id": "PROD-015",
        "name": "Archived Sold-Out Linen Kaftan",
        "brand": "Linen Trail",
        "category": "Shirts",
        "gender": "Unisex",
        "base_price": 2599.0,
        "material": "Linen",
        "fit_type": "Loose",
        "occasion": "Beach Wedding",
        "description": "Special edition beach kaftan. All units currently claimed (zero stock for guardrail verification test).",
        "image_url": "https://images.unsplash.com/photo-1596755094514-f87e34085b2c?w=500&auto=format&fit=crop&q=80",
        "variants": [
            {"size": "M", "color": "Ivory", "stock": 0, "reserved": 0},
            {"size": "L", "color": "Ivory", "stock": 0, "reserved": 0},
        ]
    }
]

SAMPLE_CUSTOMERS = [
    {
        "id": "CUST-101",
        "name": "Aarav Sharma",
        "email": "aarav.sharma@example.com",
        "preferences": {
            "preferred_size": "M",
            "preferred_fit": "Loose",
            "preferred_colors": "Pastel Blue, Sage Green, Ecru Beige",
            "preferred_materials": "Linen, Cotton",
            "budget_max": 3000.0,
            "explicit_style_notes": "Prefers breathable beach wedding attire in soothing pastel tones."
        },
        "purchases": [
            {"product_id": "PROD-001", "variant_index": 1, "price_paid": 2299.0, "rating": 5}
        ]
    },
    {
        "id": "CUST-102",
        "name": "Priya Nair",
        "email": "priya.nair@example.com",
        "preferences": {
            "preferred_size": "S",
            "preferred_fit": "Relaxed",
            "preferred_colors": "Blush Pink, Pastel Lemon, Sage Green",
            "preferred_materials": "Viscose, Cotton, Silk",
            "budget_max": 3500.0,
            "explicit_style_notes": "Floral destination wedding sundresses and breezy silhouettes."
        },
        "purchases": [
            {"product_id": "PROD-005", "variant_index": 1, "price_paid": 2899.0, "rating": 5}
        ]
    },
    {
        "id": "CUST-103",
        "name": "Rohan Verma",
        "email": "rohan.verma@example.com",
        "preferences": {
            "preferred_size": "L",
            "preferred_fit": "Slim",
            "preferred_colors": "Midnight Black, Navy",
            "preferred_materials": "Silk Blend, Wool",
            "budget_max": 7500.0,
            "explicit_style_notes": "Tailored evening wear, blazers, and luxury formal apparel."
        },
        "purchases": [
            {"product_id": "PROD-004", "variant_index": 2, "price_paid": 4200.0, "rating": 4}
        ]
    }
]

# Brand size charts across categories
SIZE_CHARTS = [
    # Linen Trail - Shirts (Men)
    {"brand": "Linen Trail", "category": "Shirts", "gender": "Men", "size_label": "S", "chest_min_cm": 88, "chest_max_cm": 94, "waist_min_cm": 74, "waist_max_cm": 80, "hip_min_cm": 90, "hip_max_cm": 96, "garment_chest_cm": 104, "garment_waist_cm": 100, "garment_hip_cm": 104, "fit_type": "Loose"},
    {"brand": "Linen Trail", "category": "Shirts", "gender": "Men", "size_label": "M", "chest_min_cm": 95, "chest_max_cm": 102, "waist_min_cm": 81, "waist_max_cm": 88, "hip_min_cm": 97, "hip_max_cm": 104, "garment_chest_cm": 112, "garment_waist_cm": 108, "garment_hip_cm": 112, "fit_type": "Loose"},
    {"brand": "Linen Trail", "category": "Shirts", "gender": "Men", "size_label": "L", "chest_min_cm": 103, "chest_max_cm": 110, "waist_min_cm": 89, "waist_max_cm": 96, "hip_min_cm": 105, "hip_max_cm": 112, "garment_chest_cm": 120, "garment_waist_cm": 116, "garment_hip_cm": 120, "fit_type": "Loose"},
    {"brand": "Linen Trail", "category": "Shirts", "gender": "Men", "size_label": "XL", "chest_min_cm": 111, "chest_max_cm": 118, "waist_min_cm": 97, "waist_max_cm": 104, "hip_min_cm": 113, "hip_max_cm": 120, "garment_chest_cm": 128, "garment_waist_cm": 124, "garment_hip_cm": 128, "fit_type": "Loose"},

    # Coastal Breeze - Shirts & T-Shirts
    {"brand": "Coastal Breeze", "category": "Shirts", "gender": "Men", "size_label": "S", "chest_min_cm": 86, "chest_max_cm": 92, "waist_min_cm": 72, "waist_max_cm": 78, "hip_min_cm": 88, "hip_max_cm": 94, "garment_chest_cm": 100, "garment_waist_cm": 96, "garment_hip_cm": 100, "fit_type": "Relaxed"},
    {"brand": "Coastal Breeze", "category": "Shirts", "gender": "Men", "size_label": "M", "chest_min_cm": 93, "chest_max_cm": 100, "waist_min_cm": 79, "waist_max_cm": 86, "hip_min_cm": 95, "hip_max_cm": 102, "garment_chest_cm": 108, "garment_waist_cm": 104, "garment_hip_cm": 108, "fit_type": "Relaxed"},
    {"brand": "Coastal Breeze", "category": "Shirts", "gender": "Men", "size_label": "L", "chest_min_cm": 101, "chest_max_cm": 108, "waist_min_cm": 87, "waist_max_cm": 94, "hip_min_cm": 103, "hip_max_cm": 110, "garment_chest_cm": 116, "garment_waist_cm": 112, "garment_hip_cm": 116, "fit_type": "Relaxed"},
    {"brand": "Coastal Breeze", "category": "Shirts", "gender": "Men", "size_label": "XL", "chest_min_cm": 109, "chest_max_cm": 116, "waist_min_cm": 95, "waist_max_cm": 102, "hip_min_cm": 111, "hip_max_cm": 118, "garment_chest_cm": 124, "garment_waist_cm": 120, "garment_hip_cm": 124, "fit_type": "Relaxed"},

    # Aura Studio - Dresses (Women)
    {"brand": "Aura Studio", "category": "Dresses", "gender": "Women", "size_label": "XS", "chest_min_cm": 78, "chest_max_cm": 83, "waist_min_cm": 60, "waist_max_cm": 65, "hip_min_cm": 85, "hip_max_cm": 90, "garment_chest_cm": 88, "garment_waist_cm": 72, "garment_hip_cm": 96, "fit_type": "Loose"},
    {"brand": "Aura Studio", "category": "Dresses", "gender": "Women", "size_label": "S", "chest_min_cm": 84, "chest_max_cm": 89, "waist_min_cm": 66, "waist_max_cm": 71, "hip_min_cm": 91, "hip_max_cm": 96, "garment_chest_cm": 94, "garment_waist_cm": 78, "garment_hip_cm": 102, "fit_type": "Loose"},
    {"brand": "Aura Studio", "category": "Dresses", "gender": "Women", "size_label": "M", "chest_min_cm": 90, "chest_max_cm": 96, "waist_min_cm": 72, "waist_max_cm": 78, "hip_min_cm": 97, "hip_max_cm": 103, "garment_chest_cm": 102, "garment_waist_cm": 86, "garment_hip_cm": 110, "fit_type": "Loose"},
    {"brand": "Aura Studio", "category": "Dresses", "gender": "Women", "size_label": "L", "chest_min_cm": 97, "chest_max_cm": 104, "waist_min_cm": 79, "waist_max_cm": 86, "hip_min_cm": 104, "hip_max_cm": 111, "garment_chest_cm": 110, "garment_waist_cm": 94, "garment_hip_cm": 118, "fit_type": "Loose"},

    # Linen Trail - Trousers (Unisex / Men)
    {"brand": "Linen Trail", "category": "Trousers", "gender": "Unisex", "size_label": "S", "chest_min_cm": 80, "chest_max_cm": 86, "waist_min_cm": 72, "waist_max_cm": 78, "hip_min_cm": 88, "hip_max_cm": 94, "garment_chest_cm": 0, "garment_waist_cm": 82, "garment_hip_cm": 104, "fit_type": "Loose"},
    {"brand": "Linen Trail", "category": "Trousers", "gender": "Unisex", "size_label": "M", "chest_min_cm": 87, "chest_max_cm": 94, "waist_min_cm": 79, "waist_max_cm": 86, "hip_min_cm": 95, "hip_max_cm": 102, "garment_chest_cm": 0, "garment_waist_cm": 90, "garment_hip_cm": 112, "fit_type": "Loose"},
    {"brand": "Linen Trail", "category": "Trousers", "gender": "Unisex", "size_label": "L", "chest_min_cm": 95, "chest_max_cm": 102, "waist_min_cm": 87, "waist_max_cm": 94, "hip_min_cm": 103, "hip_max_cm": 110, "garment_chest_cm": 0, "garment_waist_cm": 98, "garment_hip_cm": 120, "fit_type": "Loose"},
    {"brand": "Linen Trail", "category": "Trousers", "gender": "Unisex", "size_label": "XL", "chest_min_cm": 103, "chest_max_cm": 110, "waist_min_cm": 95, "waist_max_cm": 102, "hip_min_cm": 111, "hip_max_cm": 118, "garment_chest_cm": 0, "garment_waist_cm": 106, "garment_hip_cm": 128, "fit_type": "Loose"},

    # Riwaayat - Kurtas (Men)
    {"brand": "Riwaayat", "category": "Kurtas", "gender": "Men", "size_label": "S", "chest_min_cm": 88, "chest_max_cm": 93, "waist_min_cm": 74, "waist_max_cm": 79, "hip_min_cm": 90, "hip_max_cm": 95, "garment_chest_cm": 106, "garment_waist_cm": 102, "garment_hip_cm": 108, "fit_type": "Loose"},
    {"brand": "Riwaayat", "category": "Kurtas", "gender": "Men", "size_label": "M", "chest_min_cm": 94, "chest_max_cm": 101, "waist_min_cm": 80, "waist_max_cm": 87, "hip_min_cm": 96, "hip_max_cm": 103, "garment_chest_cm": 114, "garment_waist_cm": 110, "garment_hip_cm": 116, "fit_type": "Loose"},
    {"brand": "Riwaayat", "category": "Kurtas", "gender": "Men", "size_label": "L", "chest_min_cm": 102, "chest_max_cm": 109, "waist_min_cm": 88, "waist_max_cm": 95, "hip_min_cm": 104, "hip_max_cm": 111, "garment_chest_cm": 122, "garment_waist_cm": 118, "garment_hip_cm": 124, "fit_type": "Loose"},
    {"brand": "Riwaayat", "category": "Kurtas", "gender": "Men", "size_label": "XL", "chest_min_cm": 110, "chest_max_cm": 117, "waist_min_cm": 96, "waist_max_cm": 103, "hip_min_cm": 112, "hip_max_cm": 119, "garment_chest_cm": 130, "garment_waist_cm": 126, "garment_hip_cm": 132, "fit_type": "Loose"}
]

def seed_database(db_path=None):
    init_db(db_path)
    conn = get_connection(db_path)

    try:
        # 1. Insert Products & Variants & Inventory
        for p in SAMPLE_PRODUCTS:
            conn.execute(
                """
                INSERT INTO products (id, name, brand, category, gender, base_price, material, fit_type, occasion, description, image_url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name=excluded.name,
                    brand=excluded.brand,
                    category=excluded.category,
                    gender=excluded.gender,
                    base_price=excluded.base_price,
                    material=excluded.material,
                    fit_type=excluded.fit_type,
                    occasion=excluded.occasion,
                    description=excluded.description,
                    image_url=excluded.image_url
                """,
                (p["id"], p["name"], p["brand"], p["category"], p["gender"], p["base_price"],
                 p["material"], p["fit_type"], p["occasion"], p["description"], p["image_url"])
            )

            for i, v in enumerate(p.get("variants", [])):
                var_id = f"VAR-{p['id']}-{v['size']}-{v['color'].replace(' ', '')}"
                sku = f"SKU-{p['id']}-{v['size']}-{i+1:02d}"
                conn.execute(
                    """
                    INSERT INTO product_variants (id, product_id, size, color, sku, price_override)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        size=excluded.size,
                        color=excluded.color,
                        sku=excluded.sku
                    """,
                    (var_id, p["id"], v["size"], v["color"], sku, None)
                )

                conn.execute(
                    """
                    INSERT INTO inventory (variant_id, stock_quantity, reserved_quantity)
                    VALUES (?, ?, ?)
                    ON CONFLICT(variant_id) DO UPDATE SET
                        stock_quantity=excluded.stock_quantity,
                        reserved_quantity=excluded.reserved_quantity
                    """,
                    (var_id, v["stock"], v["reserved"])
                )

        # 2. Insert Customers & Preferences & Purchases
        for c in SAMPLE_CUSTOMERS:
            conn.execute(
                """
                INSERT INTO customers (id, name, email)
                VALUES (?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name=excluded.name,
                    email=excluded.email
                """,
                (c["id"], c["name"], c["email"])
            )

            pref = c.get("preferences", {})
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
                (c["id"], pref.get("preferred_size"), pref.get("preferred_fit"), pref.get("preferred_colors"),
                 pref.get("preferred_materials"), pref.get("budget_max"), pref.get("explicit_style_notes"))
            )

            for pur in c.get("purchases", []):
                pur_id = f"PUR-{c['id']}-{pur['product_id']}"
                # Get variant id
                v_row = conn.execute("SELECT id FROM product_variants WHERE product_id = ? LIMIT 1", (pur["product_id"],)).fetchone()
                var_id = v_row["id"] if v_row else f"VAR-{pur['product_id']}-M"
                conn.execute(
                    """
                    INSERT INTO purchases (id, customer_id, product_id, variant_id, price_paid, rating)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        price_paid=excluded.price_paid,
                        rating=excluded.rating
                    """,
                    (pur_id, c["id"], pur["product_id"], var_id, pur["price_paid"], pur["rating"])
                )

        # 3. Insert Size Charts
        for sc in SIZE_CHARTS:
            conn.execute(
                """
                INSERT INTO size_charts (brand, category, gender, size_label, chest_min_cm, chest_max_cm, waist_min_cm, waist_max_cm, hip_min_cm, hip_max_cm, garment_chest_cm, garment_waist_cm, garment_hip_cm, fit_type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(brand, category, gender, size_label) DO UPDATE SET
                    chest_min_cm=excluded.chest_min_cm,
                    chest_max_cm=excluded.chest_max_cm,
                    waist_min_cm=excluded.waist_min_cm,
                    waist_max_cm=excluded.waist_max_cm,
                    hip_min_cm=excluded.hip_min_cm,
                    hip_max_cm=excluded.hip_max_cm,
                    garment_chest_cm=excluded.garment_chest_cm,
                    garment_waist_cm=excluded.garment_waist_cm,
                    garment_hip_cm=excluded.garment_hip_cm,
                    fit_type=excluded.fit_type
                """,
                (sc["brand"], sc["category"], sc["gender"], sc["size_label"],
                 sc["chest_min_cm"], sc["chest_max_cm"], sc["waist_min_cm"], sc["waist_max_cm"],
                 sc["hip_min_cm"], sc["hip_max_cm"], sc["garment_chest_cm"], sc["garment_waist_cm"],
                 sc["garment_hip_cm"], sc["fit_type"])
            )

        conn.commit()
        print(f"Successfully seeded database at {db_path or DB_PATH}")
    finally:
        conn.close()

if __name__ == "__main__":
    seed_database()
