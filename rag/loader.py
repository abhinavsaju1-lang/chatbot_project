import os
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from config import Config

def load_and_split_documents(data_dir=None):
    """Load text files from data directory and split into text chunks for vector indexing."""
    if data_dir is None:
        data_dir = Config.DATA_DIR

    if not os.path.exists(data_dir):
        os.makedirs(data_dir, exist_ok=True)
        # Create default file if missing
        default_file = os.path.join(data_dir, "mental_health_guide.txt")
        if not os.path.exists(default_file):
            with open(default_file, "w", encoding="utf-8") as f:
                f.write("MindSense Mental Health Reference Guide: Active listening, stress management, and coping strategies.")

    documents = []
    try:
        loader = DirectoryLoader(data_dir, glob="**/*.txt", loader_cls=TextLoader)
        documents = loader.load()
    except Exception as e:
        print(f"[RAG Loader Error] Failed to load directory documents: {e}")
        # Fallback to direct reading of txt files
        for filename in os.listdir(data_dir):
            if filename.endswith(".txt"):
                filepath = os.path.join(data_dir, filename)
                try:
                    loader = TextLoader(filepath, encoding="utf-8")
                    documents.extend(loader.load())
                except Exception as inner_e:
                    print(f"[RAG Loader Error] Failed loading file {filepath}: {inner_e}")

    # Split documents into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )
    chunks = text_splitter.split_documents(documents)
    print(f"[RAG Loader] Loaded {len(documents)} document(s) into {len(chunks)} text chunks.")
    return chunks
