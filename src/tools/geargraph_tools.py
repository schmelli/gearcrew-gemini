import os
import logging
from typing import Type, List, Optional, Dict, Any
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from gqlalchemy import Memgraph
from rdflib import Graph, RDF, RDFS, OWL
from firecrawl import FirecrawlApp

# Importiere das Firecrawl Tool Wrapper
from src.tools.search_tools import search_tool

# Setup Logging
logging.basicConfig(
    filename='geargraph_ops.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Memgraph Connection (aus Config)
from src.config import memgraph

# --- 1. Find Similar Nodes Tool ---

class FindSimilarNodesInput(BaseModel):
    name: str = Field(..., description="The name of the entity to search for.")
    label: str = Field("GearItem", description="The label to filter by (e.g. 'GearItem', 'OutdoorBrand').")

class FindSimilarNodesTool(BaseTool):
    name: str = "Find Similar Nodes in Graph"
    description: str = "Searches in the existing graph for nodes with similar names to prevent duplicates."
    args_schema: Type[BaseModel] = FindSimilarNodesInput

    def _run(self, name: str, label: str = "GearItem") -> str:
        # Case-insensitive search via Cypher
        query = f"""
        MATCH (n:{label})
        WHERE toLower(n.name) CONTAINS toLower($name) 
           OR toLower($name) CONTAINS toLower(n.name)
        RETURN n.name as Name, labels(n) as Labels, n.productUrl as URL
        LIMIT 5
        """
        try:
            if not memgraph:
                return "Error: No DB Connection"
                
            results = list(memgraph.execute_and_fetch(query, {"name": name}))
            if not results:
                return f"No similar nodes to '{name}' found in Graph."
            
            import json
            return f"SUCCESS: Found existing nodes: {json.dumps(results, default=str)}"
        except Exception as e:
            return f"Graph Lookup Error: {str(e)}"

# --- 2. Execute Cypher Tool ---

class ExecuteCypherInput(BaseModel):
    query: str = Field(..., description="The Cypher query to execute.")
    reason: str = Field(..., description="The reason for this execution (for audit logging).")

class ExecuteCypherTool(BaseTool):
    name: str = "Execute Cypher Plan"
    description: str = "Executes a validated Cypher query against the database. Use ONLY after user approval."
    args_schema: Type[BaseModel] = ExecuteCypherInput

    def _run(self, query: str, reason: str) -> str:
        logging.info(f"EXECUTION | Reason: {reason} | Query: {query}")
        try:
            if not memgraph:
                return "Error: No DB Connection"
            
            memgraph.execute(query)
            return "Success: Query executed successfully."
        except Exception as e:
            logging.error(f"EXECUTION FAILED: {str(e)}")
            return f"Error executing Cypher: {str(e)}"

# --- 3. Validate Ontology Tool ---

class ValidateOntologyInput(BaseModel):
    proposed_entity_type: str = Field(..., description="The node label to check (e.g., 'Tent').")

class ValidateOntologyTool(BaseTool):
    name: str = "Validate Against Ontology"
    description: str = "Checks if a proposed Node Label exists in the official Ontology."
    args_schema: Type[BaseModel] = ValidateOntologyInput

    def _run(self, proposed_entity_type: str) -> str:
        try:
            g = Graph()
            if not os.path.exists("geargraph_ontology.ttl"):
                return "Warning: Ontology file 'geargraph_ontology.ttl' not found. Assuming valid."
                
            g.parse("geargraph_ontology.ttl", format="turtle")
            
            query = f"""
            SELECT ?subject WHERE {{
                ?subject a owl:Class ;
                         rdfs:label ?label .
                FILTER(LCASE(STR(?label)) = LCASE("{proposed_entity_type}"))
            }}
            """
            res = g.query(query)
            if len(res) > 0:
                return f"VALID: '{proposed_entity_type}' exists in ontology."
            else:
                return f"INVALID: '{proposed_entity_type}' not found in ontology."
        except Exception as e:
            return f"Ontology Check Error: {str(e)}"

# --- 4. Firecrawl Extract Tool ---

class FirecrawlExtractInput(BaseModel):
    url: str = Field(..., description="The URL to extract structured data from.")
    schema_dict: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional JSON schema for structured extraction. If not provided, uses a default gear extraction schema."
    )

class FirecrawlExtractTool(BaseTool):
    name: str = "Firecrawl Structured Data Extractor"
    description: str = (
        "Extracts structured data from web pages using Firecrawl's LLM-powered extraction. "
        "Particularly useful for extracting gear specifications from manufacturer pages. "
        "Can use custom schemas or defaults to extracting product details like name, weight, materials, price, etc."
    )
    args_schema: Type[BaseModel] = FirecrawlExtractInput

    def __init__(self):
        """Initialize Firecrawl with API key from environment."""
        super().__init__()
        api_key = os.getenv("FIRECRAWL_API_KEY")
        if not api_key:
            raise ValueError(
                "FIRECRAWL_API_KEY not found. "
                "Please add FIRECRAWL_API_KEY=your-key to the .env file."
            )
        object.__setattr__(self, '_firecrawl_app', FirecrawlApp(api_key=api_key))

    def _run(self, url: str, schema_dict: Optional[Dict[str, Any]] = None) -> str:
        """
        Extract structured data from a URL using Firecrawl.

        Args:
            url: The URL to extract data from
            schema_dict: Optional custom schema for extraction

        Returns:
            JSON string with extracted data
        """
        try:
            app = object.__getattribute__(self, '_firecrawl_app')

            # Default schema for outdoor gear extraction
            if schema_dict is None:
                schema_dict = {
                    "type": "object",
                    "properties": {
                        "product_name": {"type": "string", "description": "The name of the product"},
                        "brand": {"type": "string", "description": "The manufacturer or brand name"},
                        "weight_grams": {"type": "number", "description": "Product weight in grams"},
                        "weight_ounces": {"type": "number", "description": "Product weight in ounces"},
                        "material": {"type": "string", "description": "Primary material(s) used"},
                        "price_usd": {"type": "number", "description": "Price in USD"},
                        "dimensions": {"type": "string", "description": "Product dimensions"},
                        "product_url": {"type": "string", "description": "Official product URL"},
                        "image_url": {"type": "string", "description": "Product image URL"},
                        "description": {"type": "string", "description": "Product description"},
                        "features": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of key features"
                        }
                    }
                }

            # Use Firecrawl's extract endpoint with correct parameter format
            # Correct API: app.extract(urls=[url], schema=schema_dict)
            result = app.extract(urls=[url], schema=schema_dict)

            import json
            if result and hasattr(result, 'success') and result.success:
                if hasattr(result, 'data') and result.data:
                    return f"SUCCESS: Extracted data from {url}\n{json.dumps(result.data, indent=2, default=str)}"
                else:
                    return f"Extraction completed but no data returned from {url}"
            else:
                error_msg = getattr(result, 'error', 'Unknown error')
                return f"Extraction failed for {url}: {error_msg}"

        except Exception as e:
            logging.error(f"Firecrawl extract failed for {url}: {str(e)}")
            return f"Error extracting data from {url}: {str(e)}"

# --- 5. Firecrawl Scrape Tool ---

class FirecrawlScrapeInput(BaseModel):
    url: str = Field(..., description="The URL to scrape.")

class FirecrawlScrapeTool(BaseTool):
    name: str = "Firecrawl Web Scraper"
    description: str = (
        "Scrapes a web page and returns clean Markdown content. "
        "Useful for extracting and analyzing page content when structured extraction isn't needed."
    )
    args_schema: Type[BaseModel] = FirecrawlScrapeInput

    def __init__(self):
        """Initialize Firecrawl with API key from environment."""
        super().__init__()
        api_key = os.getenv("FIRECRAWL_API_KEY")
        if not api_key:
            raise ValueError(
                "FIRECRAWL_API_KEY not found. "
                "Please add FIRECRAWL_API_KEY=your-key to the .env file."
            )
        object.__setattr__(self, '_firecrawl_app', FirecrawlApp(api_key=api_key))

    def _run(self, url: str) -> str:
        """
        Scrape a web page and return Markdown content.

        Args:
            url: The URL to scrape

        Returns:
            Markdown content from the page
        """
        try:
            app = object.__getattribute__(self, '_firecrawl_app')
            result = app.scrape(url=url, formats=['markdown'])

            if result and hasattr(result, 'markdown') and result.markdown:
                return result.markdown
            else:
                return f"Error: No markdown content found for {url}"

        except Exception as e:
            return f"Error scraping {url}: {str(e)}"

# --- Namespace Helper ---

class GearGraphTools:
    """
    Namespace helper to access tool instances easily.
    """
    find_similar_nodes = FindSimilarNodesTool()
    execute_cypher = ExecuteCypherTool()
    validate_ontology_compliance = ValidateOntologyTool()
    search_web = search_tool
    firecrawl_extract = FirecrawlExtractTool()
    firecrawl_scrape = FirecrawlScrapeTool()