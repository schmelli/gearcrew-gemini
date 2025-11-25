from crewai import Task

def create_tasks(extractor, verifier, miner, db_admin, source_text, dataset_name, ontology_file, source_url=None):
    
    # Task 1: Extraction
    extract_task = Task(
        description=f"""Analyze the following source text and extract a list of SPECIFIC hiking gear products mentioned.
        
        CRITICAL RULES:
        1. VALID ITEMS ONLY: You must ONLY extract items that have BOTH a specific BRAND NAME and a PRODUCT MODEL NAME (e.g., "Durston X-Mid 1", "Osprey Exos 58").
        2. IGNORE GENERICS: Do NOT extract generic items or categories (e.g., "heavy-duty trash bag", "comfortable quilt", "lightweight backpack", "a tent"). If it doesn't have a capitalized Brand Name, ignore it.
        3. IGNORE ATTRIBUTES AS ITEMS: Do not list features or attributes (e.g., "waterproof", "15D nylon") as separate items.
        
        For each valid item, extract:
        - Brand Name
        - Product Name
        - Weight (CRITICAL: Look specifically for lbs, oz, g, kg. If found, include it!)
        - ALL Specifications found (Dimensions, Materials, Denier, Temp Ratings, Volume, etc.) - Be exhaustive!
        - Brief Description
        
        Source Text:
        {source_text}""",
        expected_output="A structured list of specific, branded gear items with their raw extracted specs. No generic items.",
        agent=extractor
    )

    # Task 2: Verification
    verify_task = Task(
        description="""Take the list of extracted gear items. 
        For each item, perform a web search to verify:
        1. The spelling of the Brand and Product name.
        2. The accuracy of ALL specs. If specs (weight, material, dims) are missing, FIND THEM on the manufacturer's site.
        3. Ensure the item actually exists as a commercial product.
        4. **CAPTURE URLs**: Record the official Manufacturer Product Page URL and any key review URLs found.
        
        CRITICAL FILTERING STEP:
        - If an item turns out to be a generic description (e.g., "Ultralight Quilt" with no brand) or a feature (e.g., "Hip Belt Pockets"), REMOVE IT from the list.
        - Ensure the "Product Name" is the specific model name (e.g., "X-Mid 1") and not a category (e.g., "1p Tent").
        
        Output a corrected, verified, and FILTERED list of gear items. 
        MUST include: Correct Brand/Model, Expanded Specs (verified), and Found URLs.""",
        expected_output="A verified, corrected, and filtered list of gear items (Brand + Model) with accurate specs and Product URLs.",
        agent=verifier,
        context=[extract_task]
    )

    # Task 3: Knowledge Mining
    mining_task = Task(
        description="""Using the verified gear list and the original source text, 
        identify specific "usage knowledge" or "tips" associated with each item.
        Example: "Durston X-Mid: can be pitched fly-first in rain."
        
        If the source text doesn't have enough info, use your internal knowledge to add 1-2 common pro-tips 
        verified for that specific gear item.""",
        expected_output="The gear list enriched with specific usage tips and practical knowledge points.",
        agent=miner,
        context=[verify_task] # Uses the output of the verifier
    )

    # Task 4: DB Ingestion
    ingest_task = Task(
        description=f"""Take the fully verified and enriched gear data. 
        1. Format the data into a STRICT JSON string. Each item in the list must have the following keys:
           - "brand": Brand Name
           - "model": Product Model Name
           - "weight": Weight string (e.g., "1.5 lbs", "680g") - CRITICAL: Do not omit if available.
           - "specifications": Dictionary of ALL technical specs (Material, Dimensions, Volume, R-Value, etc.)
           - "product_url": Official Manufacturer Product Page URL (found during verification)
           - "description": Brief description
           - "tips": List of usage tips
        2. Use the 'Cognee Add Data' tool to add this JSON string to the dataset '{dataset_name}'.
           - IMPORTANT: Pass the source URL '{source_url}' to the tool if it is not "None" or empty.
        3. Use the 'Cognee Cognify' tool to process the dataset.
        
        Ensure you report the status returned by the tools.""",
        expected_output="Confirmation of JSON data insertion and cognification.",
        agent=db_admin,
        context=[mining_task]
    )

    return [extract_task, verify_task, mining_task, ingest_task]