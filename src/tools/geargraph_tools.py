import os
import logging
from typing import Type, List, Optional
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from gqlalchemy import Memgraph
from rdflib import Graph, RDF, RDFS, OWL

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

# --- 4. Search Wrapper Tool ---
# Wir wrappen das Firecrawl Tool hier nicht nochmal neu als Klasse, 
# sondern importieren es direkt in agents.py.
# Aber für Konsistenz in der Klasse GearGraphTools (falls du sie als Namespace brauchtest):

class GearGraphTools:
    """
    Namespace helper to access tool instances easily.
    """
    find_similar_nodes = FindSimilarNodesTool()
    execute_cypher = ExecuteCypherTool()
    validate_ontology_compliance = ValidateOntologyTool()
    search_web = search_tool