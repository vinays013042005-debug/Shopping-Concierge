import sqlite3
from typing import Generator
from app.config import DB_PATH

SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS products (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    brand TEXT NOT NULL,
    category TEXT NOT NULL,
    gender TEXT NOT NULL,
    base_price REAL NOT NULL,
    material TEXT NOT NULL,
    fit_type TEXT NOT NULL,
    occasion TEXT NOT NULL,
    description TEXT NOT NULL,
    image_url TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS product_variants (
    id TEXT PRIMARY KEY,
    product_id TEXT NOT NULL,
    size TEXT NOT NULL,
    color TEXT NOT NULL,
    sku TEXT UNIQUE NOT NULL,
    price_override REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS inventory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    variant_id TEXT NOT NULL UNIQUE,
    stock_quantity INTEGER NOT NULL DEFAULT 0,
    reserved_quantity INTEGER NOT NULL DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(variant_id) REFERENCES product_variants(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS customers (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS customer_preferences (
    customer_id TEXT PRIMARY KEY,
    preferred_size TEXT,
    preferred_fit TEXT,
    preferred_colors TEXT,
    preferred_materials TEXT,
    budget_max REAL,
    explicit_style_notes TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(customer_id) REFERENCES customers(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS purchases (
    id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    product_id TEXT NOT NULL,
    variant_id TEXT NOT NULL,
    purchase_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    price_paid REAL NOT NULL,
    rating INTEGER,
    FOREIGN KEY(customer_id) REFERENCES customers(id) ON DELETE CASCADE,
    FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE CASCADE,
    FOREIGN KEY(variant_id) REFERENCES product_variants(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS size_charts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    brand TEXT NOT NULL,
    category TEXT NOT NULL,
    gender TEXT NOT NULL,
    size_label TEXT NOT NULL,
    chest_min_cm REAL NOT NULL,
    chest_max_cm REAL NOT NULL,
    waist_min_cm REAL NOT NULL,
    waist_max_cm REAL NOT NULL,
    hip_min_cm REAL NOT NULL,
    hip_max_cm REAL NOT NULL,
    garment_chest_cm REAL NOT NULL,
    garment_waist_cm REAL NOT NULL,
    garment_hip_cm REAL NOT NULL,
    fit_type TEXT NOT NULL,
    UNIQUE(brand, category, gender, size_label)
);

CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
CREATE INDEX IF NOT EXISTS idx_products_price ON products(base_price);
CREATE INDEX IF NOT EXISTS idx_variants_product ON product_variants(product_id);
CREATE INDEX IF NOT EXISTS idx_inventory_variant ON inventory(variant_id);
CREATE INDEX IF NOT EXISTS idx_size_charts_lookup ON size_charts(brand, category, gender);
"""

def get_connection(db_path=None) -> sqlite3.Connection:
    target_path = db_path or DB_PATH
    conn = sqlite3.connect(str(target_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    return conn

def get_db():
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()

def init_db(db_path=None):
    conn = get_connection(db_path)
    try:
        conn.executescript(SCHEMA_SQL)
        conn.commit()
    finally:
        conn.close()
