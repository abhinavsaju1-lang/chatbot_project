import os
from langchain_community.vectorstores import FAISS
from ai.embeddings import get_embedding_model
from rag.loader import load_and_split_documents
from config import Config

def get_or_create_vectorstore(data_dir=None, index_dir=None):
    """Build or load existing FAISS vector store index."""
    if index_dir is None:
        index_dir = Config.FAISS_INDEX_DIR
    if data_dir is None:
        data_dir = Config.DATA_DIR

    embeddings = get_embedding_model()
    if embeddings is None:
        print("[FAISS Warning] Embeddings model not available.")
        return None

    # Check if index files exist
    index_path = os.path.join(index_dir, "index.faiss")
    if os.path.exists(index_path):
        try:
            print("[FAISS] Loading existing FAISS index from disk...")
            vectorstore = FAISS.load_local(
                index_dir,
                embeddings,
                allow_dangerous_deserialization=True
            )
            return vectorstore
        except Exception as e:
            print(f"[FAISS Warning] Could not load existing index: {e}. Rebuilding...")

    # Build new index
    chunks = load_and_split_documents(data_dir)
    if not chunks:
        print("[FAISS Warning] No text chunks available to build index.")
        return None

    try:
        print("[FAISS] Creating new FAISS vector store...")
        vectorstore = FAISS.from_documents(chunks, embeddings)
        os.makedirs(index_dir, exist_ok=True)
        vectorstore.save_local(index_dir)
        print(f"[FAISS] Vector store saved successfully to {index_dir}")
        return vectorstore
    except Exception as e:
        print(f"[FAISS Error] Failed to create vector store: {e}")
        return None
