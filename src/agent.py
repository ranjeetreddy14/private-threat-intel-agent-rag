from .llm_client import LLMClient
from .rag_engine import RAGEngine
from .web_search import WebSearch

class Agent:
    def __init__(self):
        self.llm = LLMClient()
        self.rag = RAGEngine()
        self.web = WebSearch()
        
        # State
        self.web_search_allowed = False
        self.pending_query = None
        self.chat_history = [] # Stores {"role": ..., "content": ...}

    def process_query(self, query, chat_history=[], use_web=False):
        """
        Main entry point for processing a user query.
        Handles routing logic entirely in Python.
        Manages chat history internally (last 5 turns).
        """
        import datetime
        import json
        
        # 1. Check for Manual Confirmation
        confirmation_phrases = ["yes", "sure", "search", "ok", "do it", "check web", "check online", "find it online"]
        if self.pending_query and any(phrase in query.lower() for phrase in confirmation_phrases):
            self.web_search_allowed = True
            query = self.pending_query # Restore original query
            self.pending_query = None # Clear pending
        
        # 2. Explicit Web Request (Overrides everything)
        trigger_phrases = ["search web", "check internet", "look up", "google", "online", "latest", "news", "today"]
        if any(phrase in query.lower() for phrase in trigger_phrases):
            self.web_search_allowed = True

        # 3. RAG Search (Always First)
        local_context = []
        rag_results = self.rag.query_db(query)
        
        if rag_results and rag_results['documents'] and rag_results['documents'][0]:
            # Debug logging - prints to console/terminal
            print(f"[DEBUG] RAG query returned {len(rag_results['documents'][0])} results")
            if 'distances' in rag_results and rag_results['distances'][0]:
                distances = rag_results['distances'][0]
                print(f"[DEBUG] Distance range: {min(distances):.3f} - {max(distances):.3f}")
            
            for i, doc in enumerate(rag_results['documents'][0]):
                distance = rag_results['distances'][0][i] if 'distances' in rag_results else 0
                
                # Adjusted thresholds for ChromaDB's cosine distance (0-2 scale)
                # Cosine distance: 0=identical, 1=orthogonal, 2=opposite
                relevance = "LOW"
                if distance < 1.0: relevance = "HIGH"      # Strong semantic match
                elif distance < 1.3: relevance = "MEDIUM"  # Moderate match
                
                if relevance in ["HIGH", "MEDIUM"]:
                    meta = rag_results['metadatas'][0][i]
                    source = meta.get('source', 'Unknown')
                    local_context.append(f"[Source: {source} | Relevance: {relevance}]\n{doc}")
                    print(f"[DEBUG] Including result {i+1}: distance={distance:.3f}, relevance={relevance}, source={source}")

        # 4. Routing Decision
        web_context = []
        
        # Case A: Good Local Context -> Answer
        if local_context:
            pass # Proceed to answer
            
        # Case B: No Local Context
        else:
            if self.web_search_allowed:
                # Web is allowed -> Search
                web_results = self.web.search(query)
                if web_results:
                    web_context.append(web_results)
            else:
                # Web NOT allowed -> Ask Permission
                self.pending_query = query
                return ["I don't have this in my local data. Do you want me to search the web?"], []

        # 5. Construct Context JSON
        final_context = {
            "local_context": local_context,
            "web_context": web_context,
            "query": query
        }
        
        # 6. System Prompt
        current_date = datetime.datetime.now().strftime("%B %d, %Y")
        system_prompt = (
            f"Current Date: {current_date}\n"
            "You are Saturday, a threat-intel assistant.\n"
            "Use the provided context to answer the query.\n"
            "Use local_context first if relevant.\n"
            "Use web_context when available.\n"
            "If both are empty, answer from general knowledge.\n"
            "For threat intel, format with: Overview, Affected, Indicators, Mitigation, Sources.\n"
            "For normal questions, answer simply.\n"
            "Never discuss tools or reasoning."
        )

        # 7. Build Messages
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add internal history (last 5 turns = 10 messages)
        # We slice to keep the last 10 messages
        recent_history = self.chat_history[-10:] if self.chat_history else []
        messages.extend(recent_history)

        # Add current input
        messages.append({"role": "user", "content": json.dumps(final_context)})

        # 8. Call LLM & Wrap Stream
        response_stream = self.llm.chat_completion(messages, stream=True)
        
        # Extract sources
        sources = []
        if local_context: sources.append("Local Database")
        if web_context: sources.append("Web Search")
        
        # Wrapper to capture full response for history
        def stream_wrapper():
            full_response = ""
            for chunk in response_stream:
                content = ""
                if isinstance(chunk, str):
                    content = chunk
                elif hasattr(chunk, 'choices') and chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                
                if content:
                    full_response += content
                    yield chunk
            
            # Update history after stream ends
            # Store RAW query, not the JSON blob, to keep history clean
            self.chat_history.append({"role": "user", "content": query})
            self.chat_history.append({"role": "assistant", "content": full_response})
            
            # Enforce 5-turn limit (10 messages) strictly in storage too
            if len(self.chat_history) > 10:
                self.chat_history = self.chat_history[-10:]

        return stream_wrapper(), sources
