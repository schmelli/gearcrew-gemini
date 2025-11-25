import streamlit as st
from crewai import Crew, Process
from src.agents import create_agents
from src.tasks import create_tasks
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Page Config
st.set_page_config(
    page_title="GearCrew Dashboard",
    page_icon="🏔️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .stApp {
        background-color: #0e1117;
        color: #fafafa;
    }
    .stTextArea textarea {
        background-color: #262730;
        color: #fafafa;
        border-radius: 10px;
    }
    .stButton button {
        background-color: #ff4b4b;
        color: white;
        border-radius: 20px;
        padding: 10px 24px;
        font-weight: bold;
        border: none;
        transition: all 0.3s ease;
    }
    .stButton button:hover {
        background-color: #ff3333;
        transform: scale(1.05);
    }
    h1 {
        font-family: 'Helvetica Neue', sans-serif;
        font-weight: 700;
        color: #ff4b4b;
    }
    h2, h3 {
        font-family: 'Helvetica Neue', sans-serif;
        color: #e0e0e0;
    }
    .css-1d391kg {
        padding-top: 3rem;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/hiking.png", width=80)
    st.title("GearCrew")
    st.markdown("---")
    st.markdown("**AI Agents:**")
    st.markdown("- 🕵️ **Extractor** (Gemini 2.5 Pro)")
    st.markdown("- 🔍 **Verifier** (Gemini 2.5 Pro)")
    st.markdown("- 🧠 **Miner** (Gemini 2.5 Pro)")
    st.markdown("- 💾 **DB Admin** (Gemini 2.5 Pro)")
    st.markdown("---")
    st.info("Powered by CrewAI & Cognee")

# Main Content
st.title("🏔️ GearCrew AI Researcher")
st.markdown("### Transform raw gear reviews into structured knowledge.")

# Input Section
source_text = st.text_area(
    "Paste Review Summary or Transcript:",
    height=200,
    placeholder="e.g., The Durston X-Mid 1 is a 1.7lb trekking pole tent made of silpoly..."
)

source_url = st.text_input(
    "Source URL / Title (Optional):",
    placeholder="e.g., https://youtube.com/... or 'OutdoorGearLab Review'"
)

# Configuration (Hidden for now, but good for future)
dataset_name = "geargraph"
ontology_file = "geargraph_ontology.ttl"

if st.button("🚀 Analyze Gear"):
    if not source_text:
        st.warning("Please provide some text to analyze.")
    else:
        with st.status("🤖 GearCrew is working...", expanded=True) as status:
            try:
                # 1. Setup Agents
                st.write("Initializing Agents...")
                extractor, verifier, miner, db_admin = create_agents()
                
                # 2. Setup Tasks
                st.write("Creating Tasks...")
                tasks = create_tasks(
                    extractor=extractor,
                    verifier=verifier,
                    miner=miner,
                    db_admin=db_admin,
                    source_text=source_text,
                    dataset_name=dataset_name,
                    ontology_file=ontology_file,
                    source_url=source_url
                )
                
                # 3. Create Crew
                gear_crew = Crew(
                    agents=[extractor, verifier, miner, db_admin],
                    tasks=tasks,
                    verbose=True,
                    process=Process.sequential
                )
                
                # 4. Kickoff
                st.write("🚀 Kicking off the Crew...")
                result = gear_crew.kickoff()
                
                status.update(label="✅ Analysis Complete!", state="complete", expanded=False)
                
                st.divider()
                st.subheader("📝 Final Result")
                st.markdown(result)
                
            except Exception as e:
                status.update(label="❌ Error Occurred", state="error")
                st.error(f"An error occurred: {str(e)}")

# Footer
st.markdown("---")
st.caption("© 2024 GearCrew Project")
