import os
from crewai import LLM
from dotenv import load_dotenv
from gqlalchemy import Memgraph

# Load environment variables
load_dotenv()

# Memgraph Connection Setup
# Wir initialisieren das hier global, damit es in den Tools wiederverwendet werden kann
try:
    MEMGRAPH_HOST = os.getenv("MEMGRAPH_HOST", "geargraph.gearshack.app")
    MEMGRAPH_PORT = int(os.getenv("MEMGRAPH_PORT", 7687))
    MEMGRAPH_USER = os.getenv("MEMGRAPH_USER", "memgraph")
    MEMGRAPH_PASSWORD = os.getenv("MEMGRAPH_PASSWORD", "")
    
    memgraph = Memgraph(
        host=MEMGRAPH_HOST, 
        port=MEMGRAPH_PORT, 
        username=MEMGRAPH_USER, 
        password=MEMGRAPH_PASSWORD, 
        encrypted=True # WICHTIG für dein Nginx Setup
    )
except Exception as e:
    print(f"Warning: Could not initialize Memgraph connection in config: {e}")
    memgraph = None

# Force usage of API Key by removing Service Account from env if present
if "GOOGLE_APPLICATION_CREDENTIALS" in os.environ:
    del os.environ["GOOGLE_APPLICATION_CREDENTIALS"]

def get_gemini_pro():
    """Returns the Gemini 3 Pro LLM instance via Google AI Studio."""
    # Docs recommend Temperature 1.0 for reasoning models
    return LLM(
        model='gemini-2.5-pro',
        api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=1.0, 
        verbose=True,
    )

def get_gemini_flash():
    """Returns the Gemini 3 Pro (Low Thinking) instance via Google AI Studio."""
    # Using Pro with low thinking as the "Flash" equivalent for now
    return LLM(
        model='gemini-2.5-flash',
        api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=1.0,
        verbose=True,
    )