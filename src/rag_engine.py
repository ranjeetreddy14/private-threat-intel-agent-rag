import os
import chromadb
from chromadb.utils import embedding_functions
from .config import DB_DIR, CHROMA_COLLECTION_NAME, DATA_DIR, CHUNK_SIZE, CHUNK_OVERLAP
from pypdf import PdfReader

class RAGEngine:
    def __init__(self):
        self.client = chromadb.PersistentClient(path=DB_DIR)
        self.embedding_fn = embedding_functions.DefaultEmbeddingFunction()
        self.collection = self.client.get_or_create_collection(
            name=CHROMA_COLLECTION_NAME,
            embedding_function=self.embedding_fn
        )

    def ingest_documents(self, folder_path=DATA_DIR):
        """
        Reads all supported files from the data directory and adds them to the vector DB.
        """
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            return "Data directory created. Please add files."

        files = [f for f in os.listdir(folder_path) if f.endswith(('.txt', '.md', '.pdf', '.json'))]
        if not files:
            return "No documents found to ingest."

        documents = []
        metadatas = []
        ids = []

        for filename in files:
            file_path = os.path.join(folder_path, filename)
            text = ""
            try:
                if filename.endswith('.pdf'):
                    reader = PdfReader(file_path)
                    for page in reader.pages:
                        text += page.extract_text() + "\n"
                elif filename.endswith('.json'):
                    text = self._parse_json(file_path)
                else:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        text = f.read()
                
                # Simple chunking
                chunks = self._chunk_text(text)
                for i, chunk in enumerate(chunks):
                    documents.append(chunk)
                    metadatas.append({"source": filename, "chunk_id": i})
                    ids.append(f"{filename}_{i}")
            except Exception as e:
                print(f"Failed to process {filename}: {e}")

        if documents:
            self.collection.upsert(documents=documents, metadatas=metadatas, ids=ids)
            return f"Successfully ingested {len(documents)} chunks from {len(files)} files."
        return "No valid content found."

    def _parse_json(self, file_path):
        """
        Parses JSON files (STIX or CVE) and extracts a human-readable summary.
        """
        import json
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Case 1: CVE Record
            if 'cveMetadata' in data or data.get('dataType') == 'CVE_RECORD':
                return self._parse_cve(data)
            
            # Case 2: CISA KEV Catalog
            if 'vulnerabilities' in data and 'catalogVersion' in data:
                return self._parse_kev(data)
            
            # Case 3: STIX Bundle (Fallback)
            return self._parse_stix(data)

        except Exception as e:
            return f"Error parsing JSON file: {e}"

    def _parse_kev(self, data):
        """
        Parses CISA Known Exploited Vulnerabilities (KEV) catalog.
        """
        summary = []
        catalog_title = data.get('title', 'CISA KEV Catalog')
        summary.append(f"Catalog: {catalog_title}")
        
        vulnerabilities = data.get('vulnerabilities', [])
        for vuln in vulnerabilities:
            cve_id = vuln.get('cveID', 'Unknown CVE')
            vendor = vuln.get('vendorProject', 'Unknown Vendor')
            product = vuln.get('product', 'Unknown Product')
            desc = vuln.get('shortDescription', '')
            date_added = vuln.get('dateAdded', '')
            action = vuln.get('requiredAction', '')
            
            entry = f"CVE: {cve_id} | Vendor: {vendor} | Product: {product} | Date Added: {date_added}"
            if desc:
                entry += f" | Description: {desc}"
            if action:
                entry += f" | Required Action: {action}"
                
            summary.append(entry)
            
        return "\n".join(summary)

    def _parse_cve(self, data):
        """
        Extracts info from a CVE JSON record.
        """
        summary = []
        meta = data.get('cveMetadata', {})
        cve_id = meta.get('cveId', 'Unknown CVE')
        state = meta.get('state', '')
        
        summary.append(f"CVE ID: {cve_id} | State: {state}")
        
        containers = data.get('containers', {}).get('cna', {})
        
        # Descriptions
        descriptions = containers.get('descriptions', [])
        for d in descriptions:
            val = d.get('value', '')
            if val:
                summary.append(f"Description: {val}")
        
        # Affected Products
        affected = containers.get('affected', [])
        for item in affected:
            vendor = item.get('vendor', 'Unknown')
            product = item.get('product', 'Unknown')
            summary.append(f"Affected Product: {vendor} {product}")
            
        # Solutions
        solutions = containers.get('solutions', [])
        for s in solutions:
            val = s.get('value', '')
            if val:
                summary.append(f"Solution: {val}")
                
        return "\n".join(summary)

    def _parse_stix(self, data):
        """
        Parses STIX data.
        """
        # Check if it's a STIX Bundle
        objects = data.get('objects', [])
        if not objects and isinstance(data, list):
            objects = data # Maybe a list of objects directly
        elif not objects and 'type' in data:
            objects = [data] # Single object
        
        summary = []
        for obj in objects:
            obj_type = obj.get('type', 'unknown')
            name = obj.get('name', 'Unnamed')
            desc = obj.get('description', '')
            pattern = obj.get('pattern', '')
            
            # Format a readable sentence for the LLM
            entry = f"STIX Object: {obj_type.upper()} | Name: {name}"
            if desc:
                entry += f" | Description: {desc}"
            if pattern:
                entry += f" | Pattern: {pattern}"
            
            # Handle specific types like Indicators, Malware, Threat Actors
            if obj_type == 'indicator':
                valid_from = obj.get('valid_from', '')
                entry += f" | Valid From: {valid_from}"
            
            summary.append(entry)
        
        return "\n".join(summary)

    def query_db(self, query, n_results=5):
        """
        Retrieves relevant documents for a query.
        """
        results = self.collection.query(query_texts=[query], n_results=n_results)
        return results

    def _chunk_text(self, text):
        """
        Splits text into chunks with overlap.
        """
        chunks = []
        start = 0
        text_len = len(text)
        while start < text_len:
            end = start + CHUNK_SIZE
            chunks.append(text[start:end])
            start += (CHUNK_SIZE - CHUNK_OVERLAP)
        return chunks
