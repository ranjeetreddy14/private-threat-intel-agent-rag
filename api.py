from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from src.agent import Agent
from src.rag_engine import RAGEngine
from src.config import DATA_DIR
import os
import shutil
import json
from typing import Optional
from dotenv import load_dotenv

# Load environment
load_dotenv()

app = FastAPI(title="Saturday's Threat Database")

# CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize backend
agent = Agent()
rag = RAGEngine()

# Request models
class ChatRequest(BaseModel):
    message: str
    use_web: bool = False

# Serve frontend
@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()

# Chat endpoint with streaming
@app.post("/api/chat")
async def chat(request: ChatRequest):
    async def generate():
        try:
            response_stream, sources = agent.process_query(
                request.message, 
                chat_history=[], 
                use_web=request.use_web
            )
            
            # Stream chunks
            for chunk in response_stream:
                content = ""
                if isinstance(chunk, str):
                    content = chunk
                elif hasattr(chunk, 'choices') and chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                
                if content:
                    yield f"data: {json.dumps({'type': 'chunk', 'content': content})}\n\n"
            
            # Send sources
            if sources:
                yield f"data: {json.dumps({'type': 'sources', 'sources': sources})}\n\n"
            
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")

# Upload endpoint
@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR)
        
        file_path = os.path.join(DATA_DIR, file.filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        return {"status": "success", "filename": file.filename, "message": f"Uploaded {file.filename}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Ingestion endpoint
@app.post("/api/ingest")
async def ingest_documents():
    try:
        result = rag.ingest_documents()
        return {"status": "success", "message": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Status endpoint
@app.get("/api/status")
async def get_status():
    try:
        # Count files in data directory
        files = []
        if os.path.exists(DATA_DIR):
            files = [f for f in os.listdir(DATA_DIR) if f.endswith(('.txt', '.md', '.pdf', '.json'))]
        
        return {
            "status": "online",
            "files_count": len(files),
            "files": files
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

# Mount static files (must be last)
app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8081)
