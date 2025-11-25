import os
from dotenv import load_dotenv
from src.tools.cognee_tools import CogneeAddDataTool

# Load env
load_dotenv()

def test_ingestion():
    print("Testing Cognee Ingestion...")
    
    # Check if key is loaded
    api_key = os.getenv("LLM_API_KEY")
    if not api_key:
        print("Error: LLM_API_KEY not found in environment.")
        return

    print(f"LLM_API_KEY loaded: {api_key[:10]}...")

    # Initialize tool
    tool = CogneeAddDataTool()
    
    # Dummy data
    data = "The Durston X-Mid 1 is a lightweight trekking pole tent."
    dataset = "geargraph"
    
    print(f"Adding data to dataset '{dataset}'...")
    result = tool._run(data=data, dataset_name=dataset)
    
    print("Result:")
    print(result)

if __name__ == "__main__":
    test_ingestion()
