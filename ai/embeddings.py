import os

def get_embedding_model():
    """
    Lazily loads the HuggingFace sentence-transformers embedding model.
    Wrapped in try-except to prevent Out-Of-Memory (OOM) crashes on 512MB RAM tiers.
    """
    try:
        from langchain_community.embeddings import HuggingFaceEmbeddings
        model_name = os.getenv("EMBEDDING_MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2")
        embeddings = HuggingFaceEmbeddings(model_name=model_name)
        return embeddings
    except (ImportError, MemoryError) as e:
        print(f"[Embeddings Notice] HuggingFace embeddings skipped/unavailable ({e}). Using lightweight RAG.")
        return None
    except Exception as e:
        print(f"[Embeddings Error] Failed to load HuggingFace embeddings: {e}")
        return None
