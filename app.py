import streamlit as st
from crewai import Crew, Process
from src.agents import create_research_agents, create_ops_agents, create_completion_agent
from src.tasks import create_extraction_tasks, create_blueprint_task, create_refinement_task, create_execution_tasks, create_completion_task
import os
from dotenv import load_dotenv
import json

load_dotenv()

st.set_page_config(page_title="GearGraph Ops", layout="wide", page_icon="⚙️")

# Session State Init
if 'step' not in st.session_state:
    st.session_state['step'] = 'input'
if 'extracted_data' not in st.session_state:
    st.session_state['extracted_data'] = None
if 'cypher_plan' not in st.session_state:
    st.session_state['cypher_plan'] = ""
if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = []

# Sidebar
with st.sidebar:
    st.title("GearGraph Ops")
    st.info("Connected to Memgraph @ " + os.getenv("MEMGRAPH_HOST", "Unknown"))
    
    st.markdown("### Progress")
    if st.session_state['step'] == 'input':
        st.progress(0)
    elif st.session_state['step'] == 'review':
        st.progress(25)
    elif st.session_state['step'] == 'architect':
        st.progress(50)
    elif st.session_state['step'] == 'execute':
        st.progress(75)
    elif st.session_state['step'] == 'complete':
        st.progress(100)

    if st.button("Reset Process"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# --- STEP 1: INPUT & EXTRACTION ---
if st.session_state['step'] == 'input':
    st.header("🕵️ Step 1: Research & Extraction")
    
    source_url = st.text_input("Source URL (Video/Article):")
    source_text = st.text_area("Transcript / Review Text:", height=200)
    
    if st.button("Start Investigation"):
        if not source_text:
            st.error("Please provide text.")
        else:
            try:
                with st.status("🤖 Agents at work...", expanded=True) as status:
                    st.write("Initializing Agents...")
                    profiler, detective, hunter, architect = create_research_agents()
                    
                    st.write("🔍 Profiler, Detective & Hunter are analyzing...")
                    tasks = create_extraction_tasks(profiler, detective, hunter, source_text, source_url)
                    
                    extraction_crew = Crew(
                        agents=[profiler, detective, hunter],
                        tasks=tasks,
                        verbose=True
                    )
                    
                    result = extraction_crew.kickoff()
                    
                    # Parse Result (Access Task Outputs Directly)
                    # tasks[1] = Detective (Items)
                    # tasks[2] = Hunter (Wisdom)
                    
                    # Helper to clean JSON string
                    def clean_json(text):
                        if "```json" in text:
                            return text.split("```json")[1].split("```")[0].strip()
                        elif "```" in text:
                            return text.split("```")[1].split("```")[0].strip()
                        return text.strip()

                    try:
                        # CrewAI Task Output handling
                        # Note: In newer CrewAI versions, task.output is an object. We try .raw or str()
                        
                        item_raw = tasks[1].output.raw if hasattr(tasks[1].output, 'raw') else str(tasks[1].output)
                        wisdom_raw = tasks[2].output.raw if hasattr(tasks[2].output, 'raw') else str(tasks[2].output)
                        
                        st.session_state['extracted_data'] = clean_json(item_raw)
                        st.session_state['extracted_insights'] = clean_json(wisdom_raw)
                        
                    except Exception as e:
                        st.error(f"Error parsing task outputs: {e}")
                        # Fallback to previous hack if direct access fails (unlikely but safe)
                        raw_result = str(result)
                        import re
                        json_blocks = re.findall(r"```json(.*?)```", raw_result, re.DOTALL)
                        if len(json_blocks) >= 2:
                            st.session_state['extracted_data'] = json_blocks[0].strip()
                            st.session_state['extracted_insights'] = json_blocks[1].strip()
                        else:
                            st.session_state['extracted_data'] = raw_result
                            st.session_state['extracted_insights'] = "[]"
                            
                    st.session_state['source_info'] = source_url or "Manual Text"
                    st.session_state['step'] = 'review'
                    st.rerun()
                        
            except Exception as e:
                st.error(f"Critical Error during extraction: {e}")

# --- STEP 2: DATA REVIEW & REFINEMENT ---
elif st.session_state['step'] == 'review':
    st.header("🧐 Step 2: Review Extracted Data")
    
    tab1, tab2 = st.tabs(["📦 Gear Items", "🧠 Gear Wisdom"])
    
    with tab1:
        col1, col2 = st.columns([2, 1])
        with col1:
            try:
                data_json = json.loads(st.session_state['extracted_data'])
                for idx, item in enumerate(data_json):
                    with st.expander(f"📦 {item.get('verified_name', 'Unknown Item')}", expanded=True):
                        st.json(item)
                        if item.get('is_new_to_graph'):
                            st.caption("🆕 New Item")
                        else:
                            st.caption("🔗 Existing Item")
            except:
                st.error("Invalid Item JSON")
                st.code(st.session_state['extracted_data'])
        
        with col2:
            st.info("Chat to refine Items")
            # Chat logic for Items (same as before)
            if prompt := st.chat_input("Refine Item Data..."):
                st.session_state['chat_history'].append({"role": "user", "content": prompt})
                # ... (Refinement Logic for Items) ...
                # For brevity, I'm keeping the logic simple here. In a real app, we'd need to know WHICH tab is active.
                # Streamlit chat_input is global. Let's assume the prompt context implies what to fix.
                
                with st.status("🕵️ Detective is refining...", expanded=True):
                    profiler, detective, hunter, architect = create_research_agents()
                    tasks = create_refinement_task(detective, st.session_state['extracted_data'], prompt)
                    crew = Crew(agents=[detective], tasks=tasks, verbose=True)
                    res = crew.kickoff()
                    # Parse...
                    raw = str(res)
                    if "```json" in raw: raw = raw.split("```json")[1].split("```")[0].strip()
                    st.session_state['extracted_data'] = raw
                    st.rerun()

    with tab2:
        st.subheader("Extracted Insights")
        try:
            insights_json = json.loads(st.session_state.get('extracted_insights', '[]'))
            if not insights_json:
                st.info("No insights found.")
            
            for idx, insight in enumerate(insights_json):
                with st.expander(f"💡 {insight.get('summary', 'Insight')}", expanded=True):
                    st.write(insight.get('content'))
                    st.caption(f"Applies to: {insight.get('related_product')}")
        except:
            st.error("Invalid Insight JSON")
            st.code(st.session_state.get('extracted_insights'))
            
    st.divider()
    if st.button("✅ Approve Data & Generate Plan", type="primary"):
        st.session_state['step'] = 'architect'
        st.rerun()

# --- STEP 3: ARCHITECT (CYPHER PLAN) ---
elif st.session_state['step'] == 'architect':
    st.header("🏗️ Step 3: Architect Plan")
    
    with st.status("📐 Architect is designing the graph update...", expanded=True):
        profiler, detective, hunter, architect = create_research_agents()
        # Pass BOTH data sets
        tasks = create_blueprint_task(
            architect, 
            st.session_state['extracted_data'],
            st.session_state.get('extracted_insights', '[]')
        )
        
        architect_crew = Crew(
            agents=[architect],
            tasks=tasks,
            verbose=True
        )
        
        result = architect_crew.kickoff()
        
        # Extract Cypher
        if "```cypher" in str(result):
            code = str(result).split("```cypher")[1].split("```")[0].strip()
            st.session_state['cypher_plan'] = code
        else:
            st.session_state['cypher_plan'] = str(result)
            
        st.success("Plan Generated!")
    
    # Show Plan
    with st.expander("View Cypher Query (Advanced)", expanded=False):
        st.session_state['cypher_plan'] = st.text_area("Cypher Code", st.session_state['cypher_plan'], height=300)
        
    if st.button("🚀 Execute Import"):
        st.session_state['step'] = 'execute'
        st.rerun()

# --- STEP 4: EXECUTION ---
elif st.session_state['step'] == 'execute':
    st.header("🚀 Step 4: Execution & Insights")
    
    try:
        with st.status("💾 Writing to Graph...", expanded=True) as status:
            gatekeeper, gardener = create_ops_agents()
            tasks = create_execution_tasks(
                gatekeeper, 
                gardener, 
                st.session_state['cypher_plan'], 
                st.session_state.get('source_info', 'Unknown')
            )
            
            ops_crew = Crew(
                agents=[gatekeeper, gardener],
                tasks=tasks,
                verbose=True
            )
            
            result = ops_crew.kickoff()
            
            st.success("Import Successful!")
            st.subheader("🌿 Gardener's Report")
            st.markdown(result)

            st.divider()
            if st.button("🔍 Run Data Completion", type="primary"):
                st.session_state['step'] = 'complete'
                st.rerun()

            if st.button("Skip Completion & Start New"):
                st.session_state['step'] = 'input'
                st.session_state['extracted_data'] = None
                st.session_state['extracted_insights'] = None
                st.session_state['cypher_plan'] = ""
                st.session_state['chat_history'] = []
                st.rerun()

    except Exception as e:
        st.error(f"Execution Failed: {e}")

# --- STEP 5: DATA COMPLETION ---
elif st.session_state['step'] == 'complete':
    st.header("🔍 Step 5: Data Completion")

    st.info("""
    The Data Completion agent will:
    - Find products with missing weight, URLs, or images
    - Search the web for missing information
    - Extract structured data from manufacturer pages
    - Update the graph with complete information
    """)

    try:
        with st.status("🔎 Completing missing data...", expanded=True) as status:
            completer = create_completion_agent()
            tasks = create_completion_task(completer)

            completion_crew = Crew(
                agents=[completer],
                tasks=tasks,
                verbose=True
            )

            result = completion_crew.kickoff()

            st.success("Data Completion Finished!")
            st.subheader("📊 Completion Report")
            st.markdown(result)

            if st.button("Start New Import"):
                st.session_state['step'] = 'input'
                st.session_state['extracted_data'] = None
                st.session_state['extracted_insights'] = None
                st.session_state['cypher_plan'] = ""
                st.session_state['chat_history'] = []
                st.rerun()

    except Exception as e:
        st.error(f"Data Completion Failed: {e}")
        if st.button("Skip & Start New"):
            st.session_state['step'] = 'input'
            st.rerun()