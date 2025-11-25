import os
from crewai import Crew, Process
from src.agents import create_agents
from src.tasks import create_tasks

# Configuration
DEFAULT_DATASET_NAME = "gear_knowledge_base"
DEFAULT_ONTOLOGY_FILE = "geargraph_ontology.ttl"

def run():
    print("## Welcome to the GearCrew ##")
    print("-------------------------------")
    print(f"Targeting Cognee Server: {os.environ.get('COGNEE_API_URL', 'Default (Local/Cloud)')}")
    
    # 1. Get Input
    print("Please enter the source text (summary of review or transcript):")
    print("(Press Enter twice to finish input)")
    lines = []
    while True:
        line = input()
        if line:
            lines.append(line)
        else:
            break
    source_text = "\n".join(lines)
    
    if not source_text:
        print("No text provided. Exiting.")
        return

    print("\n(Optional) Please enter the source URL/Title for this text:")
    source_url = input()

    # 2. Setup Agents and Tasks
    extractor, verifier, miner, db_admin = create_agents()
    
    tasks = create_tasks(
        extractor=extractor,
        verifier=verifier,
        miner=miner,
        db_admin=db_admin,
        source_text=source_text,
        source_url=source_url,
        dataset_name=DEFAULT_DATASET_NAME,
        ontology_file=DEFAULT_ONTOLOGY_FILE
    )

    # 3. Create Crew
    gear_crew = Crew(
        agents=[extractor, verifier, miner, db_admin],
        tasks=tasks,
        verbose=True, 
        process=Process.sequential 
    )

    # 4. Kickoff
    result = gear_crew.kickoff()
    
    print("\n\n########################")
    print("## GearCrew Finished  ##")
    print("########################\n")
    print("Final Result:")
    print(result)

if __name__ == "__main__":
    run()