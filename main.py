from nicegui import ui, app
from src.agent import Agent
from src.rag_engine import RAGEngine
from src.config import DATA_DIR
import os
import shutil
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
COPYRIGHT_OWNER = os.getenv("COPYRIGHT_OWNER", "Ranjeet Reddy Manchana")

# Initialize Backend
agent = Agent()
rag = RAGEngine()

# Global State
use_web_search = False

def toggle_web_search(e):
    global use_web_search
    use_web_search = e.value
    if e.value:
        ui.notify('Web Search Enabled', type='positive')
    else:
        ui.notify('Web Search Disabled', type='info')

async def handle_upload(e):
    print(f"[DEBUG] Upload request received: {e.name} ({e.type})")
    try:
        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR)
        
        dst_path = os.path.join(DATA_DIR, e.name)
        
        # Simple synchronous write (fast enough for <50MB)
        e.content.seek(0)
        with open(dst_path, 'wb') as f:
            shutil.copyfileobj(e.content, f)
            
        ui.notify(f'Uploaded {e.name}', type='positive')
        print(f"[DEBUG] Successfully saved to: {dst_path}")
    except Exception as ex:
        print(f"[ERROR] Upload failed: {ex}")
        import traceback
        traceback.print_exc()
        ui.notify(f'Error uploading: {ex}', type='negative')

async def run_ingestion():
    spinner.visible = True
    status_label.text = "Ingesting..."
    try:
        result = await io_bound(rag.ingest_documents)
        status_label.text = result
        ui.notify('Ingestion Complete', type='positive')
    except Exception as e:
        status_label.text = f"Error: {e}"
        ui.notify('Ingestion Failed', type='negative')
    finally:
        spinner.visible = False

# Helper to run blocking IO in a separate thread to keep UI responsive
from nicegui import run
async def io_bound(func, *args, **kwargs):
    return await run.io_bound(func, *args, **kwargs)

async def send_message():
    text = text_input.value
    if not text:
        return
    
    text_input.value = ''
    
    # User Message
    with chat_container:
        ui.chat_message(text, name='You', sent=True)
        
    # AI Message Placeholder
    with chat_container:
        ai_message = ui.chat_message('Thinking...', name='Saturday', sent=False)
        spinner_msg = ui.spinner(size='sm')
    
    try:
        # Process Query
        # Note: agent.process_query is synchronous generator, we need to iterate it
        # We'll run the generator in a thread or just iterate carefully.
        # Since it yields chunks, we can't easily run the whole thing in run.io_bound.
        # We will iterate the generator directly. Since it calls LLM (network), it might block slightly,
        # but for a local tool it's acceptable or we can wrap it.
        
        response_content = ""
        sources_list = []
        
        # We need to run the blocking generator in a way that doesn't freeze UI
        # But for simplicity in v1, we'll iterate directly. 
        # Ideally, agent should be async.
        
        # Let's use a simple wrapper to get the full response for now to ensure stability,
        # or iterate if we can.
        
        response_stream, sources = await io_bound(agent.process_query, text, chat_history=[], use_web=use_web_search)
        
        spinner_msg.delete()
        ai_message.clear()
        
        # Stream the response
        with ai_message:
            response_label = ui.markdown()
            
        for chunk in response_stream:
            content = ""
            if isinstance(chunk, str):
                content = chunk
            elif hasattr(chunk, 'choices') and chunk.choices[0].delta.content is not None:
                content = chunk.choices[0].delta.content
            
            if content:
                response_content += content
                response_label.set_content(response_content)
                
        if sources:
            response_content += f"\n\n**Sources:** {', '.join(sources)}"
            response_label.set_content(response_content)
            
    except Exception as e:
        spinner_msg.delete()
        ui.notify(f"Error: {e}", type='negative')

# --- UI Layout ---
@ui.page('/')
def main_page():
    # Dark Mode & Theme
    ui.dark_mode().enable()
    
    # Custom CSS for Glassmorphism
    ui.add_head_html('''
        <style>
            .glass-panel {
                background: rgba(30, 41, 59, 0.7);
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 12px;
            }
            .gradient-text {
                background: linear-gradient(to right, #60a5fa, #a78bfa);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }
        </style>
    ''')

    # Header
    with ui.header().classes('bg-transparent p-4'):
        ui.label("🛡️ Saturday's Threat Database").classes('text-2xl font-bold gradient-text')
        ui.label("Your Private, Secure, AI Research Assistant").classes('text-sm text-gray-400 ml-4 self-center')

    # Main Layout
    with ui.row().classes('w-full h-screen no-wrap gap-4 p-4'):
        
        # Sidebar (Left Panel)
        with ui.column().classes('w-1/4 min-w-[250px] h-full glass-panel p-4 gap-4'):
            ui.label("⚙️ Settings").classes('text-lg font-bold text-gray-200')
            
            # Web Search
            ui.switch('Enable Web Search', on_change=toggle_web_search).classes('text-blue-400')
            
            ui.separator().classes('bg-gray-700')
            
            ui.label("📂 Ingestion").classes('text-lg font-bold text-gray-200')
            
            # File Upload
            ui.upload(label="Upload Documents", auto_upload=True, on_upload=handle_upload, max_file_size=50_000_000).classes('w-full')
            
            # Ingest Button
            global spinner, status_label
            with ui.row().classes('items-center'):
                ui.button('Ingest Documents', on_click=run_ingestion).props('icon=sync').classes('bg-blue-600 hover:bg-blue-500')
                spinner = ui.spinner().props('size=md').classes('ml-2')
                spinner.visible = False
            
            status_label = ui.label("Ready").classes('text-sm text-gray-400')

        # Chat Area (Right Panel)
        with ui.column().classes('flex-1 h-full glass-panel p-4 relative'):
            
            # Chat Messages Container
            global chat_container
            with ui.scroll_area().classes('w-full h-full pb-20 pr-4') as chat_scroll:
                chat_container = ui.column().classes('w-full gap-2')
                # Welcome Message
                with chat_container:
                    ui.chat_message("Hello! I'm Saturday. How can I help you with your threat research today?", 
                                  name='Saturday', sent=False, avatar='https://robohash.org/saturday?set=set4')

            # Input Area (Fixed at bottom)
            with ui.row().classes('absolute bottom-4 left-4 right-4 gap-2'):
                global text_input
                text_input = ui.input(placeholder='Ask a question...').props('rounded outlined input-class="text-white"').classes('w-full flex-grow glass-panel px-4')
                text_input.on('keydown.enter', send_message)
                
                ui.button(icon='send', on_click=send_message).props('round flat').classes('text-blue-400')

# --- Helper for Non-Blocking Generation ---
def generate_response_sync(text, use_web):
    """
    Synchronous wrapper to consume the generator and return the full text.
    This runs in a separate thread to avoid blocking the UI.
    """
    full_response = ""
    sources_text = ""
    try:
        response_stream, sources = agent.process_query(text, chat_history=[], use_web=use_web)
        
        for chunk in response_stream:
            content = ""
            if isinstance(chunk, str):
                content = chunk
            elif hasattr(chunk, 'choices') and chunk.choices[0].delta.content is not None:
                content = chunk.choices[0].delta.content
            
            if content:
                full_response += content
                
        if sources:
            sources_text = f"\n\n**Sources:** {', '.join(sources)}"
            
        return full_response, sources_text
    except Exception as e:
        return f"Error: {e}", ""

async def send_message():
    text = text_input.value
    if not text:
        return
    
    text_input.value = ''
    
    # User Message
    with chat_container:
        ui.chat_message(text, name='You', sent=True)
        
    # AI Message Placeholder
    with chat_container:
        ai_message = ui.chat_message('Thinking...', name='Saturday', sent=False)
        spinner_msg = ui.spinner(size='sm')
    
    try:
        # Run generation in a separate thread
        response_text, sources_text = await run.io_bound(generate_response_sync, text, use_web_search)
        
        spinner_msg.delete()
        ai_message.clear()
        
        # Display response
        with ai_message:
            ui.markdown(response_text + sources_text)
            
    except Exception as e:
        spinner_msg.delete()
        ui.notify(f"Error: {e}", type='negative')

    # Footer
    with ui.footer().classes('bg-transparent justify-center p-2'):
        ui.html(f"<div class='text-xs text-gray-500'>© 2025 {COPYRIGHT_OWNER}</div>", sanitize=False)

ui.run(title="Saturday's Threat Database", dark=True, port=8081, reload=False)
