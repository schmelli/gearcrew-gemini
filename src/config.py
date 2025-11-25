import os
from crewai import LLM
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_gemini_3_pro_preview():
    """Returns the Gemini 3 Pro Preview LLM instance."""
    return LLM(
        model='gemini/gemini-3-pro-preview',
        api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0.0,
        verbose=True
    )

def get_gemini_pro():
    """Returns the Gemini 1.5 Pro LLM instance."""
    return LLM(
        model='gemini/gemini-1.5-pro',
        api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0.0,
        verbose=True
    )

def get_gemini_flash():
    """Returns the Gemini 1.5 Flash LLM instance."""
    return LLM(
        model='gemini/gemini-1.5-flash',
        api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0.0,
        verbose=True
    )

def get_gemini_2_5_pro():
    """Returns the Gemini 2.5 Pro LLM instance."""
    return LLM(
        model='gemini/gemini-2.5-pro',
        api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0.0,
        verbose=True
    )