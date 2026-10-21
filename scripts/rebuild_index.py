"""
Script to rebuild ChromaDB semantic vector embeddings from SQLite product catalog.
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.retrieval_service import retrieval_service

def main():
    print("Indexing products into ChromaDB vector database...")
    count = retrieval_service.index_products()
    print(f"Indexing complete! Successfully indexed {count} products.")

if __name__ == "__main__":
    main()
