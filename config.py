import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "mindsense_default_secret_key_2026")
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/mindsense_db?serverSelectionTimeoutMS=5000&connectTimeoutMS=5000")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    
    # Path configuration
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    DATA_DIR = os.path.join(BASE_DIR, "data")
    FAISS_INDEX_DIR = os.path.join(BASE_DIR, "rag", "faiss_index")
