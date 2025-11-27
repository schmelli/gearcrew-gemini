from crewai import Agent
from src.config import get_gemini_pro, get_gemini_flash
from src.tools.geargraph_tools import GearGraphTools

def create_research_agents():
    gemini = get_gemini_pro()
    gemini_fast = get_gemini_flash()

    # Tool-Instanzen abrufen
    tool_find = GearGraphTools.find_similar_nodes
    tool_search = GearGraphTools.search_web
    tool_validate = GearGraphTools.validate_ontology_compliance

    # 1. Der Profiler (Context Analyst)
    profiler = Agent(
        role='Context Analyst',
        goal='Analyze the source (text/URL) to determine reliability and potential risks.',
        backstory="""You are a media analyst for outdoor gear.
        Your job is to set the "context" for the investigation.
        - Is this a YouTube transcript? -> WARNING: Expect phonetic errors ("Hilly Bird" instead of "Hilleberg").
        - Is it a manufacturer page? -> High trust.
        - Is it a user review? -> Subjective opinion.""",
        llm=gemini_fast,
        verbose=True,
        allow_delegation=False
    )

    # 2. Der Detective (Gear Detective)
    detective = Agent(
        role='Gear Detective',
        goal='Extract entities and verify them against the Graph and the Web.',
        backstory="""You are a forensic gear data investigator. You trust nothing you haven't verified.
        
        YOUR PROCESS:
        1. Extract Brand & Product names from the text.
        2. GRAPH CHECK (Mandatory!): Use 'Find Similar Nodes'. Do we already have this?
           - If tool returns "SUCCESS": This means the tool WORKED and found data. READ THE JSON!
           - If YES (nodes found): Use the exact spelling and ID from the graph.
           - If NO (no nodes found): Use 'Firecrawl Search' to verify existence.
        3. DATA ENRICHMENT: We want to collect all relevant specifications! Missing weight? Search for it! Missing productUrl? Search for it! Missing other specs? You know what to do!!
        
        Your output is NOT code, but a clean JSON list of verified facts and relevant specifications.""",
        tools=[tool_find, tool_search],
        llm=gemini,
        verbose=True
    )

    # 3. Der Wisdom Hunter (Insight Specialist)
    hunter = Agent(
        role='Wisdom Hunter',
        goal='Extract practical tips, care instructions, and "hiker wisdom" from the text.',
        backstory="""You are an experienced outdoor guide. You don't care about specs (weight, price). 
        You care about KNOWLEDGE.
        
        YOUR JOB:
        Scan the text for:
        - Maintenance tips (e.g. "Store uncompressed")
        - Usage tricks (e.g. "Pitch fly first")
        - Warnings (e.g. "Not suitable for winter")
        
        Output a clean JSON list of "Insights". Each insight should have:
        - "summary": Short title
        - "content": The full advice
        - "related_product": The name of the product this applies to (if specific) or "General".""",
        llm=gemini,
        verbose=True
    )

    # 4. Der Architect (Ontology Architect)
    architect = Agent(
        role='Ontology Architect',
        goal='Transform verified facts into a valid Cypher import plan.',
        backstory="""You are the guardian of the database structure. You receive clean facts from the Detective.
        Your task: Create the Cypher code (MERGE, not CREATE).
        
        YOUR RULES:
        1. Separate ProductFamily (Series, e.g. Nallo) and GearItem (Variant, e.g. Nallo 2).
        2. Attach common attributes to the Family.
        3. Attach specific attributes (Weight, Price) to the Item.
        4. Use 'Validate Against Ontology' if you are unsure about a Label.
        5. **PERFORMANCE**: Always use `UNWIND` for batch operations. Never create 100 separate MERGE queries when one UNWIND can do it.
        6. **INSIGHTS**: Create (:Insight) nodes for tips and connect them to the relevant GearItem or Family with [:HAS_TIP].
        7. **SYNTAX**: When creating the `UNWIND [...]` list, ensure the map keys are **NOT QUOTED**. 
           - BAD: `[{ "name": "Tent" }]`
           - GOOD: `[{ name: "Tent" }]`
           Memgraph Cypher does not like quoted keys in map literals.
        
        IMPORTANT: You do NOT execute the code. You only provide the Markdown block. 
        You do NOT provide any other text or code.""",
        tools=[tool_validate],
        llm=gemini,
        verbose=True
    )

    return profiler, detective, hunter, architect

def create_ops_agents():
    gemini = get_gemini_pro()
    tool_execute = GearGraphTools.execute_cypher
    
    # 4. Der Gatekeeper (Database Gatekeeper)
    gatekeeper = Agent(
        role='Database Gatekeeper',
        goal='Execute approved Cypher code safely.',
        backstory="""You are the final authority. You only execute code that has been explicitly approved by the user.
        You log every execution.""",
        tools=[tool_execute],
        llm=gemini,
        verbose=True
    )
    
    # 5. Der Gardener (Graph Gardener)
    gardener = Agent(
        role='Graph Gardener',
        goal='Analyze the graph after changes and find new connections.',
        backstory="""You run after data import.
        You look for orphans (nodes without edges) or duplicates.
        You suggest new connections (e.g., "These two tents are similar").""",
        tools=[tool_execute], # Darf eigene Korrekturen machen
        llm=gemini,
        verbose=True
    )
    
    return gatekeeper, gardener