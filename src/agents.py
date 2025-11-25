from crewai import Agent
from src.config import get_gemini_3_pro_preview
from src.tools.search_tools import search_tool
from src.tools.cognee_tools import CogneeAddDataTool, CogneeCognifyTool

# Initialize Tools
cognee_add_tool = CogneeAddDataTool()
cognee_cognify_tool = CogneeCognifyTool()

def create_agents():
    gemini_3_pro_preview = get_gemini_3_pro_preview()

    # Agent 1: Gear Info Extractor
    extractor = Agent(
        role='Gear Information Extractor',
        goal='Extract precise gear specifications (name, weight, materials, etc.) from raw text.',
        backstory="""You are a meticulous technical analyst. You receive raw summaries or transcripts 
        and extract structured data about hiking gear. You do not hallucinate; if a spec isn't there, you don't invent it.""",
        llm=gemini_3_pro_preview,
        verbose=True,
        allow_delegation=False
    )

    # Agent 2: Info Verifier
    verifier = Agent(
        role='Gear Information Verifier',
        goal='Verify extracted gear data against the internet, correct errors, and collect official product URLs.',
        backstory="""You are a skepticism-driven fact-checker. You take the extracted data and search the web 
        to ensure brand names (e.g., "ZPacks" not "CBacks"), weights, and model names are accurate. 
        You correct any discrepancies found in the source text.""",
        tools=[search_tool],
        llm=gemini_3_pro_preview,
        verbose=True,
        allow_delegation=False
    )

    # Agent 3: Knowledge Miner
    miner = Agent(
        role='Gear Knowledge Specialist',
        goal='Extract practical usage tips, tricks, and specific "gear knowledge" related to the verified items.',
        backstory="""You are an experienced thru-hiker. You look at the gear item and the context 
        to find specific, non-obvious usage tips (e.g., "pitch fly first in rain"). 
        You focus on "how-to" and practical benefits.""",
        llm=gemini_3_pro_preview,
        verbose=True,
        allow_delegation=False
    )

    # Agent 4: Database Administrator
    db_admin = Agent(
        role='Graph Database Administrator',
        goal='Populate the Cognee graph database with the verified and enriched gear information.',
        backstory="""You are responsible for the integrity of the knowledge graph. 
        You take the final, verified, and enriched data and commit it to the database using the appropriate tools. 
        You ensure the ontology is respected.""",
        tools=[cognee_add_tool, cognee_cognify_tool],
        llm=gemini_3_pro_preview,
        verbose=True,
        allow_delegation=False
    )

    return extractor, verifier, miner, db_admin