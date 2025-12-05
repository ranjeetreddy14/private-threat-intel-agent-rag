# Saturday's Threat Database (Private Threat Intel Agent)

**Saturday** is a private, secure, AI-powered research assistant designed specifically for threat intelligence. It leverages local Large Language Models (LLMs) and Retrieval-Augmented Generation (RAG) to provide answers based on your internal datasets (PDFs, STIX, CVEs) without exposing sensitive data to the cloud.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![Status](https://img.shields.io/badge/status-active-success.svg)

## Features

*   **Fully Private**: Runs entirely on your local machine using `llama-cpp-python`. No data leaves your network.
*   **RAG Engine**: Automatically ingests and understands:
    *   PDF Threat Reports
    *   CVE JSON Records
    *   STIX/TAXII Objects
    *   Text Notes
*   **Smart Routing**: The agent intelligently decides the best source for your answer:
    1.  **Local Context**: Checks your private database first.
    2.  **Web Search**: Falls back to the web for the latest vulnerabilities (if enabled).
    3.  **General Knowledge**: Uses the LLM's base knowledge for general queries.
*   **Web Search Integration**: Real-time internet access for up-to-the-minute threat data.
*   **Modern UI**: A beautiful, dark-mode, glassmorphism interface built with NiceGUI.

## System Design

The system is built on a modular architecture designed for privacy and extensibility.

```mermaid
flowchart TD
    User[User] -->|"Query"| UI[NiceGUI Interface]
    UI -->|"Process"| Agent[Agent Core]
    
    subgraph "Decision Engine"
        Agent -->|"1. Search"| RAG[RAG Engine]
        Agent -->|"2. Fallback"| Web[Web Search]
        Agent -->|"3. Generate"| LLM[Local LLM]
    end
    
    subgraph "Data Layer"
        RAG <-->|"Retrieve"| Chroma[ChromaDB Vector Store]
        RAG <--|"Ingest"| Files["PDFs<br>JSONs<br>STIX Files"]
    end
    
    Web <-->|"Fetch"| Internet((Internet))
    
    LLM -->|"Response"| Agent
    Agent -->|"Answer"| UI
```

### Components
- **Agent (`src/agent.py`)**: The brain of the system. It handles the logic for routing queries, managing chat history, and constructing the context for the LLM.
- **RAG Engine (`src/rag_engine.py`)**: Manages document ingestion, parsing (PDF/JSON), chunking, and vector retrieval using ChromaDB.
- **Web Search (`src/web_search.py`)**: Provides real-time search capabilities to supplement local data.
- **LLM Client (`src/llm_client.py`)**: Interfaces with the local Llama model for inference.

## Installation

1.  **Clone the repository**
    ```bash
    git clone https://github.com/ranjeetreddy14/private-threat-intel-agent-rag.git
    cd private-threat-intel-agent-rag
    ```

2.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Download Model**
    Place your GGUF model (e.g., `llama-2-7b-chat.gguf`) in the `models/` directory.

4.  **Run the Application**
    ```bash
    python main.py
    ```
    Access the UI at `http://localhost:8081`.

## Usage

1.  **Upload Data**: Use the sidebar to upload PDF reports or CVE JSON files.
2.  **Ingest**: Click "Ingest Documents" to process them into the vector database.
3.  **Chat**: Ask questions like "What are the latest indicators for APT29?" or "Summarize CVE-2024-1234".
4.  **Web Search**: Toggle "Enable Web Search" if you need information outside your local dataset.

## License

This project is licensed under the MIT License.
