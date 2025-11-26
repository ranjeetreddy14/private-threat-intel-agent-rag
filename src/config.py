import os

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_DIR = os.path.join(BASE_DIR, "db")
MODEL_PATH = r"c:\private_rag_saturday\models\qwen2.5-3b-instruct-q4_k_m.gguf"
LLAMA_SERVER_PATH = r"c:\private_rag_saturday\llama\llama-b7108-bin-win-cpu-x64\llama-server.exe"

# Server Settings
LLAMA_HOST = "127.0.0.1"
LLAMA_PORT = 8080
LLAMA_API_BASE = f"http://{LLAMA_HOST}:{LLAMA_PORT}/v1"

# RAG Settings
CHROMA_COLLECTION_NAME = "rag_collection"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
