import chromadb
from chromadb.config import Settings
import os

DB_DIR = os.path.join(os.path.dirname(__file__), "chroma_data")
os.makedirs(DB_DIR, exist_ok=True)

# Initialize ChromaDB persistent client
chroma_client = chromadb.PersistentClient(path=DB_DIR)

# Collection for past investigations/RCAs
memory_collection = chroma_client.get_or_create_collection(
    name="investigation_memory",
    metadata={"hnsw:space": "cosine"}
)

def add_memory(doc_id: str, text: str, metadata: dict):
    """Add a new RCA or investigation summary to the vector database."""
    memory_collection.add(
        documents=[text],
        metadatas=[metadata],
        ids=[doc_id]
    )

def search_memory(query: str, n_results: int = 3) -> list:
    """Search for relevant past investigations based on a new query/IOC."""
    results = memory_collection.query(
        query_texts=[query],
        n_results=n_results
    )
    
    if not results or not results['documents'] or len(results['documents'][0]) == 0:
        return []
        
    return [
        {"text": doc, "metadata": meta} 
        for doc, meta in zip(results['documents'][0], results['metadatas'][0])
    ]
