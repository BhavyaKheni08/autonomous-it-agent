import pytest
import chromadb
from app.core.config import settings

def test_chroma_connection_and_search():
    """
    Validates that the ChromaDB contains data and can retrieve it.
    """
    # 1. Connect
    client = chromadb.PersistentClient(path=settings.CHROMA_DB_PATH)
    
    # 2. Check Collection
    collections = client.list_collections()
    collection_names = [c.name for c in collections]
    assert "tech_docs" in collection_names, "Colleciton 'tech_docs' not found in ChromaDB"
    
    collection = client.get_collection("tech_docs")
    
    # 3. Check Count
    count = collection.count()
    assert count > 0, "ChromaDB collection is empty. Did you run seed_knowledge.py?"
    
    # 4. Perform Search
    # Search for 'password' which is in the dummy policy
    results = collection.query(
        query_texts=["password requirement"],
        n_results=1
    )
    
    docs = results['documents'][0]
    assert len(docs) > 0
    assert "password" in docs[0].lower() or "security" in docs[0].lower()

if __name__ == "__main__":
    test_chroma_connection_and_search()
