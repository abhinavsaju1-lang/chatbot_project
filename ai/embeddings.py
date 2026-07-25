import os
from langchain_community.embeddings import HuggingFaceEmbeddings

def get_embedding_model():
    """Load and return the HuggingFace sentence-transformers embedding model."""
    try:
        # Uses small, fast, highly effective 384-dim embedding model
        model_name = "sentence-transformers/all-MiniLM-L6-v2"
        embeddings = HuggingFaceEmbeddings(model_name=model_name)
        return embeddings
    except Exception as e:
        print(f"[Embeddings Error] Failed to load HuggingFace embeddings: {e}")
        return None
