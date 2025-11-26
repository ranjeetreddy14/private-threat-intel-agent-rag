from src.rag_engine import RAGEngine
import sys

def main():
    print("Initializing RAG Engine...")
    rag = RAGEngine()
    print("Ingesting documents from data/ ...")
    result = rag.ingest_documents()
    print(result)

if __name__ == "__main__":
    main()
