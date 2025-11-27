from crewai import Task

def create_extraction_tasks(profiler, detective, hunter, source_text, source_url):
    
    # Task 1: Profiling
    profile_task = Task(
        description=f"""
        Analysiere diesen Input-Text und die URL: '{source_url}'.
        1. Um was für eine Quelle handelt es sich?
        2. Welche spezifischen Fehlerarten sind zu erwarten (z.B. "Hillyberg" statt "Hilleberg" bei Audio)?
        3. Gib Anweisungen für den Detective, wie streng er prüfen muss.
        
        INPUT TEXT:
        {source_text[:1000]}...
        """,
        agent=profiler,
        expected_output="Ein kurzer Risiko-Bericht und Verification-Policy."
    )

    # Task 2: Investigation (Der Kern-Task)
    investigation_task = Task(
        description=f"""
        Basierend auf der Policy des Profilers: Extrahiere und verifiziere alle Gear-Items.
        
        QUELLE:
        {source_text}
        
        SCHRITTE:
        1. Extrahiere Roh-Namen.
        2. GRAPH CHECK: Prüfe mit 'Find Similar Nodes', ob wir das Item oder die Brand schon haben.
           -> Wenn ja: Übernimm die Schreibweise und IDs.
        3. WEB CHECK (Firecrawl): Suche fehlende Daten (Gewicht, Material, URL).
           -> Korrigiere Namen.
        
        OUTPUT FORMAT (JSON):
        Eine Liste von Objekten mit: 
        {{
          "original_name": "...", 
          "verified_name": "...", 
          "is_new_to_graph": bool, 
          "specs": {{...}}, 
          "url": "..."
        }}
        """,
        agent=detective,
        context=[profile_task],
        expected_output="Eine JSON-Liste mit vollständig verifizierten Produktdaten."
    )

    # Task 3: Wisdom Hunting
    wisdom_task = Task(
        description=f"""
        Suche nach praktischen Tipps, Tricks und Warnungen im Text.
        
        QUELLE:
        {source_text}
        
        OUTPUT FORMAT (JSON):
        Eine Liste von Objekten:
        {{
            "summary": "...",
            "content": "...",
            "related_product": "..." (oder "General")
        }}
        """,
        agent=hunter,
        expected_output="Eine JSON-Liste mit Gear Insights."
    )

    return [profile_task, investigation_task, wisdom_task]

def create_refinement_task(detective, current_data, user_feedback):
    refine_task = Task(
        description=f"""
        Der User hat Feedback zu den extrahierten Daten gegeben. Bitte aktualisiere die Daten entsprechend.
        
        AKTUELLE DATEN (JSON):
        {current_data}
        
        USER FEEDBACK:
        "{user_feedback}"
        
        AUFGABE:
        1. Verstehe, was der User korrigiert haben will (z.B. falscher Name, falsches Gewicht, falsche Zuordnung).
        2. Wenn nötig, nutze Tools (Suche), um die Korrektur zu verifizieren.
        3. Gib die KORRIGIERTE JSON-Liste zurück.
        
        OUTPUT FORMAT:
        Nur das reine JSON.
        """,
        agent=detective,
        expected_output="Die korrigierte JSON-Liste."
    )
    return [refine_task]

def create_blueprint_task(architect, verified_data_json, verified_insights_json):
    # Task 4: Blueprint (Planung)
    blueprint_task = Task(
        description=f"""
        Nimm die verifizierten Daten und Insights und erstelle den Cypher-Import-Plan.
        
        VERIFIZIERTE DATEN:
        {verified_data_json}
        
        VERIFIZIERTE INSIGHTS:
        {verified_insights_json}
        
        WICHTIG:
        - Nutze für 'is_new_to_graph=False' Items unbedingt MERGE auf den existierenden Namen.
        - Beachte die ProductFamily (Serie) vs. GearItem (Variante) Logik!
        - Gemeinsame Specs -> Family. Spezifische Specs -> Item.
        - **BATCH PROCESSING**: Nutze `UNWIND` für das Einfügen von Daten. Erstelle eine Liste von Maps und iteriere darüber, anstatt viele einzelne MERGE Statements zu schreiben.
        - **INSIGHTS**: Verbinde Insights mit den passenden Items oder Families.
        
        Gib NUR den Cypher-Code in einem Markdown Block zurück (```cypher ... ```).
        """,
        agent=architect,
        expected_output="Ein validierter Cypher-Code Block."
    )
    return [blueprint_task]

def create_execution_tasks(gatekeeper, gardener, approved_cypher_plan, source_info):
    
    # Task 4: Execution
    execute_task = Task(
        description=f"""
        Führe folgenden Cypher-Plan aus, den der User freigegeben hat.
        
        PLAN:
        {approved_cypher_plan}
        
        REASON:
        User Approved Import from {source_info}
        """,
        agent=gatekeeper,
        expected_output="Bestätigung der Ausführung."
    )
    
    # Task 5: Gardening (Memify)
    garden_task = Task(
        description="""
        Prüfe den Graphen nach dem Import.
        1. Gibt es 'Orphan Families' (Familien ohne Items)?
        2. Gibt es Items ohne URL?
        3. Melde Statistiken (z.B. "Jetzt 50 Zelte im Graph").
        """,
        agent=gardener,
        context=[execute_task],
        expected_output="Ein Gesundheits-Bericht des Graphen."
    )
    
    return [execute_task, garden_task]