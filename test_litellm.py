from litellm import completion
import os
from dotenv import load_dotenv

load_dotenv()

try:
    print("Testing Gemini 3 Pro Preview...")
    response = completion(
        model="gemini/gemini-3-pro-preview",
        messages=[{"role": "user", "content": "Hello, are you Gemini 3?"}],
        api_key=os.getenv("GOOGLE_API_KEY")
    )
    print("Success!")
    print(response)
except Exception as e:
    print(f"Error: {e}")
