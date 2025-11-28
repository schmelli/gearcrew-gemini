"""
GearCrew Monitor - Streamlit UI for monitoring and controlling the multi-agent system.

Run with: streamlit run crew_monitor.py
"""
import streamlit as st
import time
from datetime import datetime
from typing import Dict, List, Optional
import json

# Page config
st.set_page_config(
    page_title="GearCrew Monitor",
    page_icon="⚙️",
    layout="wide"
)

# Initialize session state
if 'running' not in st.session_state:
    st.session_state.running = False
if 'paused' not in st.session_state:
    st.session_state.paused = False
if 'logs' not in st.session_state:
    st.session_state.logs = []
if 'discoveries' not in st.session_state:
    st.session_state.discoveries = []
if 'current_agent' not in st.session_state:
    st.session_state.current_agent = None
if 'pending_approval' not in st.session_state:
    st.session_state.pending_approval = None


def add_log(message: str, level: str = "info"):
    """Add a log entry"""
    st.session_state.logs.append({
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "level": level,
        "message": message
    })
    # Keep last 100 logs
    st.session_state.logs = st.session_state.logs[-100:]


# Sidebar - Control Panel
with st.sidebar:
    st.title("⚙️ GearCrew Control")

    st.header("🎯 Source Configuration")

    source_type = st.selectbox(
        "Source Type",
        ["YouTube Playlist", "YouTube Search", "Manufacturer Website", "Custom URLs"]
    )

    if source_type == "YouTube Playlist":
        playlist_url = st.text_input(
            "YouTube Playlist URL or Name",
            placeholder="GearGraph Material"
        )
        st.caption("Enter playlist name or full URL")

    elif source_type == "YouTube Search":
        search_query = st.text_input(
            "Search Query",
            placeholder="ultralight tent review 2025"
        )

    elif source_type == "Manufacturer Website":
        manufacturer = st.selectbox(
            "Select Manufacturer",
            ["Durston Gear", "Zpacks", "Hyperlite Mountain Gear", "NEMO Equipment",
             "Big Agnes", "Enlightened Equipment", "Gossamer Gear", "Custom..."]
        )
        if manufacturer == "Custom...":
            custom_url = st.text_input("Custom URL")

    elif source_type == "Custom URLs":
        custom_urls = st.text_area(
            "URLs (one per line)",
            placeholder="https://example.com/product1\nhttps://example.com/product2"
        )

    st.divider()

    st.header("🎛️ Execution Options")

    col1, col2 = st.columns(2)
    with col1:
        max_items = st.number_input("Max Items", 1, 100, 20)
    with col2:
        quality_threshold = st.slider("Quality %", 70, 100, 85)

    human_approval = st.checkbox("Require approval before graph load", value=True)
    verbose_mode = st.checkbox("Verbose logging", value=True)

    st.divider()

    # Control buttons
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("▶️ Start", disabled=st.session_state.running, use_container_width=True):
            st.session_state.running = True
            st.session_state.paused = False
            add_log("🚀 Starting GearCrew flow...", "info")

    with col2:
        if st.button("⏸️ Pause" if not st.session_state.paused else "▶️ Resume",
                    disabled=not st.session_state.running, use_container_width=True):
            st.session_state.paused = not st.session_state.paused
            status = "paused" if st.session_state.paused else "resumed"
            add_log(f"⏸️ Flow {status}", "warning")

    with col3:
        if st.button("⏹️ Stop", disabled=not st.session_state.running, use_container_width=True):
            st.session_state.running = False
            st.session_state.paused = False
            add_log("🛑 Flow stopped", "error")


# Main content
st.title("🔧 GearCrew Multi-Agent Monitor")

# Status bar
status_col1, status_col2, status_col3, status_col4 = st.columns(4)

with status_col1:
    status = "🟢 Running" if st.session_state.running and not st.session_state.paused else \
             "🟡 Paused" if st.session_state.paused else "⚪ Idle"
    st.metric("Status", status)

with status_col2:
    st.metric("Discoveries", len(st.session_state.discoveries))

with status_col3:
    st.metric("Current Agent", st.session_state.current_agent or "None")

with status_col4:
    pending = "⚠️ Yes" if st.session_state.pending_approval else "✅ None"
    st.metric("Pending Approval", pending)

st.divider()

# Main tabs
tab1, tab2, tab3, tab4 = st.tabs(["📊 Live View", "🔍 Discoveries", "✅ Approvals", "📜 Logs"])

with tab1:
    st.header("Live Agent Activity")

    # Agent status cards
    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("🔎 Gear-heads")
        with st.container(border=True):
            st.caption("Discovery Team")
            agents = ["YouTube Scanner", "Website Scanner", "Blog Scanner", "Reddit Scanner"]
            for agent in agents:
                status_icon = "🟢" if st.session_state.current_agent == agent else "⚪"
                st.text(f"{status_icon} {agent}")

    with col2:
        st.subheader("📚 Curators")
        with st.container(border=True):
            st.caption("Research Team")
            agents = ["Graph Verifier", "Researcher", "Validator", "Citation Agent"]
            for agent in agents:
                status_icon = "🟢" if st.session_state.current_agent == agent else "⚪"
                st.text(f"{status_icon} {agent}")

    with col3:
        st.subheader("🏗️ Architects")
        with st.container(border=True):
            st.caption("Graph Team")
            agents = ["Cypher Validator", "Relationship Gardener"]
            for agent in agents:
                status_icon = "🟢" if st.session_state.current_agent == agent else "⚪"
                st.text(f"{status_icon} {agent}")

    # Current task display
    st.subheader("Current Task")
    with st.container(border=True):
        if st.session_state.running:
            st.info("🔄 Processing... (This would show real-time agent thoughts)")
            # Placeholder for streaming agent output
            with st.expander("Agent Reasoning (expand to see)"):
                st.code("""
[Agent: YouTube Scanner]
Thinking: Analyzing video "Durston X-Mid Pro 2 Review"
- Extracting product mentions...
- Found: X-Mid Pro 2, weight mentioned: 28oz
- Creating ProductDiscovery object...
- Priority: 9 (detailed product review)
                """)
        else:
            st.caption("No active task. Click Start to begin.")

with tab2:
    st.header("Discovered Items")

    # Sample discoveries for demo
    sample_discoveries = [
        {"type": "Product", "name": "Durston X-Mid Pro 2", "brand": "Durston Gear",
         "source": "YouTube", "confidence": 0.95, "status": "pending"},
        {"type": "Insight", "name": "Seam sealing tip", "product": "X-Mid Pro 2",
         "source": "YouTube", "confidence": 0.8, "status": "researched"},
    ]

    if sample_discoveries:
        for disc in sample_discoveries:
            with st.container(border=True):
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.write(f"**{disc['type']}**: {disc['name']}")
                    st.caption(f"Source: {disc['source']} | Brand: {disc.get('brand', 'N/A')}")
                with col2:
                    st.metric("Confidence", f"{disc['confidence']:.0%}")
                with col3:
                    st.write(f"Status: {disc['status']}")
    else:
        st.info("No discoveries yet. Start the flow to begin scanning.")

with tab3:
    st.header("Pending Approvals")

    # Human-in-the-loop approval section
    if st.session_state.pending_approval:
        with st.container(border=True):
            st.warning("⚠️ Approval Required")
            st.json(st.session_state.pending_approval)

            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("✅ Approve", type="primary", use_container_width=True):
                    add_log("✅ Approved by user", "info")
                    st.session_state.pending_approval = None
            with col2:
                if st.button("✏️ Modify", use_container_width=True):
                    st.info("Modification interface would open here")
            with col3:
                if st.button("❌ Reject", use_container_width=True):
                    add_log("❌ Rejected by user", "warning")
                    st.session_state.pending_approval = None
    else:
        st.success("✅ No pending approvals")

    # Show what requires approval
    st.subheader("Approval Triggers")
    st.markdown("""
    The system will pause for your approval when:
    - 📊 **Cypher Code Ready**: Before loading data to GearGraph
    - ⚠️ **Low Confidence**: Discovery confidence < 70%
    - 🔀 **Duplicate Detected**: Potential duplicate in database
    - ❓ **Ambiguous Data**: Conflicting information from sources
    """)

with tab4:
    st.header("Execution Logs")

    # Log display
    if st.session_state.logs:
        log_container = st.container(height=400)
        with log_container:
            for log in reversed(st.session_state.logs):
                icon = {"info": "ℹ️", "warning": "⚠️", "error": "❌", "success": "✅"}.get(log["level"], "📝")
                st.text(f"[{log['timestamp']}] {icon} {log['message']}")
    else:
        st.info("No logs yet. Start the flow to see activity.")

    if st.button("Clear Logs"):
        st.session_state.logs = []
        st.rerun()


# Footer
st.divider()
st.caption("GearCrew Multi-Agent System | Built with CrewAI + Streamlit")
