import asyncio
import cognee
import os
import importlib
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

# Configure Cognee to use your self-hosted instance
# We set this globally, but we might need to re-set it if we reload the module.
os.environ["COGNEE_API_URL"] = "http://116.203.232.88:8000/api/v1"
if os.getenv("COGWIT_API_KEY"):
    os.environ["COGNEE_API_KEY"] = os.getenv("COGWIT_API_KEY")

class CogneeAddDataInput(BaseModel):
    data: str = Field(..., description="The text content to add to the knowledge graph.")
    dataset_name: str = Field(..., description="The name of the dataset to organize this data.")
    source_url: str = Field(None, description="The URL of the source (e.g., YouTube video or article) for attribution.")

class CogneeAddDataTool(BaseTool):
    name: str = "Cognee Add Data"
    description: str = "Adds verified gear information to the self-hosted Cognee graph database, with optional source attribution."
    args_schema: type[BaseModel] = CogneeAddDataInput

    def _run(self, data: str, dataset_name: str, source_url: str = None) -> str:
        """
        Adds data to Cognee.
        """
        # RELOAD cognee to avoid 'Event loop is closed' or 'bound to different loop' errors
        # caused by global state persisting across CrewAI's separate tool executions.
        importlib.reload(cognee)
        
        # Re-apply configuration after reload just in case it's stored in the module
        os.environ["COGNEE_API_URL"] = "http://116.203.232.88:8000/api/v1"
        if os.getenv("COGWIT_API_KEY"):
            os.environ["COGNEE_API_KEY"] = os.getenv("COGWIT_API_KEY")

        async def async_add():
            try:
                # Prepare data with metadata if source is provided
                # Since cognee.add might accept raw text or specific formats,
                # we'll prepend the source info to the text block for now to ensure it's captured
                # or pass it as metadata if the SDK supports it (sticking to text prepending for safety).
                final_data = data
                if source_url:
                    final_data = f"Source: {source_url}\n\n{data}"
                
                await cognee.add(final_data, dataset_name)
                return f"Successfully added data to dataset '{dataset_name}' on self-hosted server."
            except Exception as e:
                return f"Error adding data to Cognee: {str(e)}"

        return asyncio.run(async_add())

class CogneeCognifyInput(BaseModel):
    dataset_id: str = Field(..., description="The name/ID of the dataset to cognify.")
    ontology_file: str = Field(None, description="Path to the local ontology file (e.g., geargraph_ontology.ttl).")

class CogneeCognifyTool(BaseTool):
    name: str = "Cognee Cognify"
    description: str = "Processes the dataset using the GearGraph ontology."
    args_schema: type[BaseModel] = CogneeCognifyInput

    def _run(self, dataset_id: str, ontology_file: str = "geargraph_ontology.ttl") -> str:
        """
        Triggers the cognify process.
        """
        # RELOAD cognee to ensure fresh async primitives for the new event loop
        importlib.reload(cognee)

        # Re-apply configuration
        os.environ["COGNEE_API_URL"] = "http://116.203.232.88:8000/api/v1"
        if os.getenv("COGWIT_API_KEY"):
            os.environ["COGNEE_API_KEY"] = os.getenv("COGWIT_API_KEY")

        async def async_cognify():
            try:
                print(f"Cognifying dataset '{dataset_id}' using ontology '{ontology_file}'...")
                
                try:
                    await cognee.cognify(datasets=[dataset_id], ontology_path=ontology_file)
                except TypeError:
                    # Fallback if specific SDK version doesn't support ontology_path kwarg
                    await cognee.cognify(datasets=[dataset_id])

                return f"Cognify process completed for dataset '{dataset_id}' with ontology '{ontology_file}'."
            except Exception as e:
                return f"Error during cognify: {str(e)}"

        return asyncio.run(async_cognify())