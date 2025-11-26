import gradio as gr
from src.agent import Agent
import time

# Initialize Agent
agent = Agent()

# Global state for web search toggle
use_web_search = False

def toggle_web_search(value):
    global use_web_search
    use_web_search = value
    return f"Web search: {'Enabled' if value else 'Disabled'}"

def chat_function(message, history):
    """
    Generator function for Gradio ChatInterface.
    """
    try:
        # Debug print
        print(f"[DEBUG] Message: {message}, History type: {type(history)}, Web: {use_web_search}")
        
        response_stream, sources = agent.process_query(message, chat_history=history, use_web=use_web_search)
        
        partial_message = ""
        for chunk in response_stream:
            # Handle both OpenAI stream objects and simple strings (for fallback)
            if isinstance(chunk, str):
                content = chunk
            elif hasattr(chunk, 'choices') and chunk.choices[0].delta.content is not None:
                content = chunk.choices[0].delta.content
            else:
                content = ""
                
            if content:
                partial_message += content
                yield partial_message

        if sources:
            yield partial_message + f"\n\n**Sources:** {', '.join(sources)}"
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        yield f"⚠️ **System Error:** {str(e)}\n\nPlease check the terminal for details."

def ingest_data(files=None):
    from src.rag_engine import RAGEngine
    import shutil
    import os
    from src.config import DATA_DIR

    # If files are uploaded, save them to DATA_DIR
    if files:
        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR)
            
        saved_count = 0
        for file_obj in files:
            try:
                src_path = file_obj.name
                filename = os.path.basename(src_path)
                dst_path = os.path.join(DATA_DIR, filename)
                shutil.copy2(src_path, dst_path)
                saved_count += 1
            except Exception as e:
                print(f"Error saving file: {e}")
        
        status_msg = f"Saved {saved_count} new files. "
    else:
        status_msg = "No new files uploaded. Scanning existing data folder... "

    rag = RAGEngine()
    ingest_result = rag.ingest_documents()
    return status_msg + ingest_result

with gr.Blocks(title="Local Agentic RAG System") as demo:
    gr.Markdown("# 🤖 Local Agentic RAG System")
    
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### Settings")
            use_web_checkbox = gr.Checkbox(label="Enable Web Search", value=False)
            web_status = gr.Textbox(label="Status", value="Web search: Disabled", interactive=False)
            use_web_checkbox.change(toggle_web_search, inputs=[use_web_checkbox], outputs=[web_status])
            
            gr.Markdown("### Ingestion")
            file_upload = gr.File(label="Upload Documents", file_count="multiple")
            ingest_btn = gr.Button("Ingest Documents")
            ingest_output = gr.Textbox(label="Ingest Status", interactive=False)
            
            ingest_btn.click(ingest_data, inputs=[file_upload], outputs=ingest_output)
            
        with gr.Column(scale=4):
            chatbot = gr.ChatInterface(
                fn=chat_function,
                title="Chat with your Documents",
                description="Ask questions about your local documents in `data/` or enable web search."
            )

if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1", server_port=7860)
