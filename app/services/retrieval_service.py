import os
import sqlite3
import logging
from typing import List, Dict, Any, Optional
from app.config import CHROMA_DIR, CHROMA_COLLECTION_NAME
from app.services.embedding_service import embedding_service
from app.database import get_connection

logger = logging.getLogger(__name__)

class RetrievalService:
    def __init__(self, chroma_dir=CHROMA_DIR, collection_name=CHROMA_COLLECTION_NAME):
        self.chroma_dir = chroma_dir
        self.collection_name = collection_name
        self._client = None
        self._collection = None

    @property
    def collection(self):
        if self._collection is None:
            try:
                import chromadb
                self._client = chromadb.PersistentClient(path=str(self.chroma_dir))
                self._collection = self._client.get_or_create_collection(
                    name=self.collection_name,
                    metadata={"hnsw:space": "cosine"}
                )
            except Exception as e:
                logger.error(f"Failed to initialize ChromaDB collection: {e}")
                self._collection = None
        return self._collection

    def index_products(self, db_path=None) -> int:
        """Indexes all products from SQLite into ChromaDB."""
        conn = get_connection(db_path)
        try:
            query = """
                SELECT p.id, p.name, p.brand, p.category, p.gender, p.base_price,
                       p.material, p.fit_type, p.occasion, p.description,
                       GROUP_CONCAT(DISTINCT pv.color) as colors,
                       GROUP_CONCAT(DISTINCT pv.size) as sizes
                FROM products p
                LEFT JOIN product_variants pv ON p.id = pv.product_id
                GROUP BY p.id
            """
            rows = conn.execute(query).fetchall()
            if not rows:
                logger.warning("No products found in SQLite to index.")
                return 0

            ids = []
            documents = []
            metadatas = []

            for r in rows:
                pid = r["id"]
                doc_text = (
                    f"Product: {r['name']}. Brand: {r['brand']}. Category: {r['category']}. "
                    f"Occasion: {r['occasion']}. Material: {r['material']}. Fit: {r['fit_type']}. "
                    f"Colors available: {r['colors'] or 'Assorted'}. "
                    f"Price: INR {r['base_price']:.0f}. "
                    f"Description: {r['description']}"
                )
                ids.append(pid)
                documents.append(doc_text)
                metadatas.append({
                    "product_id": pid,
                    "brand": str(r["brand"]),
                    "category": str(r["category"]),
                    "gender": str(r["gender"]),
                    "occasion": str(r["occasion"]),
                    "material": str(r["material"]),
                    "fit_type": str(r["fit_type"]),
                    "base_price": float(r["base_price"])
                })

            embeddings = embedding_service.embed_texts(documents)

            col = self.collection
            if col is not None:
                # Upsert into ChromaDB
                col.upsert(
                    ids=ids,
                    documents=documents,
                    embeddings=embeddings,
                    metadatas=metadatas
                )
                logger.info(f"Successfully indexed {len(ids)} products in ChromaDB.")
                return len(ids)
            else:
                logger.warning("ChromaDB collection unavailable; skipped vector indexing.")
                return 0
        finally:
            conn.close()

    def search_candidates(
        self,
        query_text: str,
        n_results: int = 10,
        category: Optional[str] = None,
        db_path=None
    ) -> List[Dict[str, Any]]:
        """
        Retrieves candidate products using ChromaDB semantic search.
        Falls back to SQLite keyword matching if ChromaDB is empty or uninitialized.
        """
        col = self.collection
        results = []

        if col is not None:
            try:
                count = col.count()
                if count > 0:
                    query_embedding = embedding_service.embed_query(query_text)
                    where_filter = None
                    if category and category.lower() not in ["outfit", "apparel", "clothes"]:
                        where_filter = {"category": category}

                    res = col.query(
                        query_embeddings=[query_embedding],
                        n_results=min(n_results, count),
                        where=where_filter,
                        include=["metadatas", "distances", "documents"]
                    )

                    if res and res.get("ids") and len(res["ids"][0]) > 0:
                        for i in range(len(res["ids"][0])):
                            pid = res["ids"][0][i]
                            dist = res["distances"][0][i] if res.get("distances") else 0.5
                            sim_score = max(0.0, 1.0 - dist)
                            meta = res["metadatas"][0][i] if res.get("metadatas") else {}
                            results.append({
                                "product_id": pid,
                                "similarity_score": round(sim_score, 4),
                                "metadata": meta
                            })
                        return results
            except Exception as e:
                logger.warning(f"ChromaDB search failed: {e}. Falling back to SQLite search.")

        # SQLite fallback search
        return self._sqlite_fallback_search(query_text, category, n_results, db_path)

    def _sqlite_fallback_search(
        self,
        query_text: str,
        category: Optional[str],
        limit: int,
        db_path=None
    ) -> List[Dict[str, Any]]:
        conn = get_connection(db_path)
        try:
            tokens = [t.lower() for t in query_text.replace(",", " ").split() if len(t) > 2]
            sql = "SELECT id, name, brand, category, occasion, material, fit_type, base_price, description FROM products WHERE 1=1"
            params = []

            if category and category.lower() not in ["outfit", "apparel", "clothes"]:
                sql += " AND (category = ? OR name LIKE ?)"
                params.extend([category, f"%{category}%"])

            rows = conn.execute(sql, params).fetchall()
            scored = []
            for r in rows:
                score = 0.5
                full_text = f"{r['name']} {r['occasion']} {r['material']} {r['fit_type']} {r['description']}".lower()
                for t in tokens:
                    if t in full_text:
                        score += 0.15
                scored.append({
                    "product_id": r["id"],
                    "similarity_score": min(1.0, round(score, 4)),
                    "metadata": dict(r)
                })

            scored.sort(key=lambda x: x["similarity_score"], reverse=True)
            return scored[:limit]
        finally:
            conn.close()

retrieval_service = RetrievalService()
