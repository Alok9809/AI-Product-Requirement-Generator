import os
import time
import streamlit as st
from prd_generator import LLMService, BusinessAnalystAgent, ProductManagerAgent, DatabaseManager

# Set Streamlit Page Configuration
st.set_page_config(
    page_title="AI Product Requirement Generator",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom styles for modern, premium look
st.markdown("""
<style>
    .main-title {
        font-size: 2.8rem;
        font-weight: 800;
        background: linear-gradient(135deg, #FF4B4B, #FF8F8F);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .subtitle {
        font-size: 1.1rem;
        color: #7f8c8d;
        margin-bottom: 2rem;
    }
    .persona-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 1.5rem;
        border-left: 5px solid #FF4B4B;
        margin-bottom: 1rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    .dark .persona-card {
        background-color: #1e242b;
        border-left: 5px solid #FF4B4B;
        color: #f8f9fa;
    }
    .badge-high {
        background-color: #ffcccc;
        color: #cc0000;
        padding: 0.2rem 0.5rem;
        border-radius: 5px;
        font-weight: bold;
    }
    .badge-medium {
        background-color: #ffe5cc;
        color: #cc6600;
        padding: 0.2rem 0.5rem;
        border-radius: 5px;
        font-weight: bold;
    }
    .badge-low {
        background-color: #e5ffcc;
        color: #336600;
        padding: 0.2rem 0.5rem;
        border-radius: 5px;
        font-weight: bold;
    }
    .us-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    .dark .us-card {
        background-color: #1a202c;
        border: 1px solid #2d3748;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Session State
if "selected_prd_id" not in st.session_state:
    st.session_state.selected_prd_id = None
if "current_prd" not in st.session_state:
    st.session_state.current_prd = None
if "api_key_input" not in st.session_state:
    st.session_state.api_key_input = ""

# Load default key if present in env
default_api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or ""

# Sidebar
with st.sidebar:
    st.image("https://img.icons8.com/color/96/artificial-intelligence.png", width=80)
    st.title("AI PRD Assistant")
    
    # API Key Configuration
    st.subheader("🔑 Configuration")
    user_api_key = st.text_input(
        "Gemini API Key",
        value=st.session_state.api_key_input if st.session_state.api_key_input else default_api_key,
        type="password",
        help="Provide your Gemini API Key. If set in environmental variables, this can be left blank."
    )
    
    if user_api_key:
        os.environ["GEMINI_API_KEY"] = user_api_key
        st.session_state.api_key_input = user_api_key

    # Initialize Services
    llm_service = LLMService()
    ba_agent = BusinessAnalystAgent(llm_service)
    pm_agent = ProductManagerAgent(llm_service)
    db_manager = DatabaseManager()

    # DB Connection Status Indicator
    st.markdown("---")
    st.subheader("🔌 Database Connection")
    if db_manager.is_connected:
        st.success("Connected to MongoDB")
    else:
        st.warning("MongoDB offline (Running in-memory)")

    # History list
    st.markdown("---")
    st.subheader("📜 Generated PRDs History")
    
    # Refresh history
    history = db_manager.get_history()
    
    if not history:
        st.info("No saved PRDs found.")
    else:
        for item in history:
            col1, col2 = st.columns([4, 1])
            
            # Select button
            button_label = f"📝 {item['product_idea'][:22]}..." if len(item['product_idea']) > 22 else f"📝 {item['product_idea']}"
            if col1.button(button_label, key=f"sel_{item['id']}", use_container_width=True):
                st.session_state.selected_prd_id = item['id']
                st.session_state.current_prd = db_manager.get_prd_by_id(item['id'])
                st.rerun()
            
            # Delete button
            if col2.button("🗑️", key=f"del_{item['id']}", help="Delete PRD"):
                db_manager.delete_prd(item['id'])
                # If deleted the currently viewed PRD, clear state
                if st.session_state.selected_prd_id == item['id']:
                    st.session_state.selected_prd_id = None
                    st.session_state.current_prd = None
                st.rerun()

    # Clear screen button
    if st.session_state.current_prd:
        st.markdown("---")
        if st.button("➕ Generate New PRD", type="primary", use_container_width=True):
            st.session_state.selected_prd_id = None
            st.session_state.current_prd = None
            st.rerun()

# Main Workspace
st.markdown('<div class="main-title">AI Product Requirement Generator</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Convert raw business ideas into production-ready specifications using a multi-agent system.</div>', unsafe_allow_html=True)

# Check API Key
if not os.environ.get("GEMINI_API_KEY") and not os.environ.get("GOOGLE_API_KEY"):
    st.info("💡 **Getting Started:** Enter a Gemini API Key in the sidebar configuration to call Gemini. (Offline mode/mock data will be used if no key is entered.)")

# Check if we should render history detail or the form
if st.session_state.current_prd:
    prd = st.session_state.current_prd
    
    st.markdown(f"### Current PRD: **{prd['product_idea']}**")
    st.caption(f"Database Record ID: `{prd['id']}` | Generated: {prd.get('timestamp', 'Unknown')}")
    
    # Render generated specifications in tabs
    tab_full, tab_problem, tab_stories, tab_functional, tab_risks = st.tabs([
        "📄 Full PRD (Markdown)",
        "👥 Problem & Personas",
        "📝 User Stories",
        "⚙️ Functional Specs",
        "⚠️ Risks & Non-Functional"
    ])
    
    # 1. Full PRD Markdown
    with tab_full:
        st.subheader("Document Output")
        st.download_button(
            label="⬇️ Download Markdown (.md)",
            data=prd['full_prd_markdown'],
            file_name=f"PRD_{prd['product_idea'].replace(' ', '_')[:30]}.md",
            mime="text/markdown",
            use_container_width=True
        )
        st.markdown("---")
        st.markdown(prd['full_prd_markdown'])

    # 2. Problem & Personas
    with tab_problem:
        st.subheader("1. Core Problem Statement")
        st.info(prd['ba_data'].get('problem_statement', 'No problem statement.'))
        
        st.subheader("2. Target Personas")
        personas = prd['ba_data'].get('personas', [])
        if not personas:
            st.write("No personas defined.")
        else:
            cols = st.columns(len(personas))
            for idx, persona in enumerate(personas):
                with cols[idx]:
                    st.markdown(f"""
                    <div class="persona-card">
                        <h3>👤 {persona.get('name', 'N/A')}</h3>
                        <strong>Role:</strong> {persona.get('role', 'N/A')}<br>
                        <strong>Details:</strong> {persona.get('details', 'N/A')}<br><br>
                        <strong>Goals:</strong> {persona.get('goals', 'N/A')}<br>
                        <strong>Pain Points:</strong> {persona.get('pain_points', 'N/A')}
                    </div>
                    """, unsafe_allow_html=True)

    # 3. User Stories
    with tab_stories:
        st.subheader("3. Product User Stories")
        stories = prd['pm_data'].get('user_stories', [])
        if not stories:
            st.write("No user stories generated.")
        else:
            for idx, story in enumerate(stories, 1):
                with st.container():
                    st.markdown(f"""
                    <div class="us-card">
                        <h4>US-{idx:03d}: {story.get('title', 'N/A')}</h4>
                        <p><strong>As a</strong> {story.get('role', 'N/A')},</p>
                        <p><strong>I want to</strong> {story.get('want', 'N/A')},</p>
                        <p><strong>So that</strong> {story.get('benefit', 'N/A')}.</p>
                    </div>
                    """, unsafe_allow_html=True)
                    with st.expander(f"View US-{idx:03d} Acceptance Criteria"):
                        ac = story.get('acceptance_criteria', '')
                        if isinstance(ac, str):
                            st.text(ac)
                        elif isinstance(ac, list):
                            for item in ac:
                                st.write(f"- {item}")

    # 4. Functional Requirements
    with tab_functional:
        st.subheader("4. Functional Specs Table")
        func_reqs = prd['pm_data'].get('functional_requirements', [])
        if not func_reqs:
            st.write("No functional specs generated.")
        else:
            # We can format it nicely into a pandas dataframe or custom table
            cols = st.columns([2, 2, 5, 2])
            cols[0].write("**Module**")
            cols[1].write("**Feature**")
            cols[2].write("**Description**")
            cols[3].write("**Priority**")
            st.markdown("---")
            for req in func_reqs:
                cols = st.columns([2, 2, 5, 2])
                cols[0].write(req.get('module', 'N/A'))
                cols[1].write(req.get('feature', 'N/A'))
                cols[2].write(req.get('description', 'N/A'))
                
                # Priority badge
                prio = req.get('priority', 'Medium')
                badge_class = f"badge-{prio.lower()}" if prio.lower() in ['high', 'medium', 'low'] else "badge-medium"
                cols[3].markdown(f'<span class="{badge_class}">{prio}</span>', unsafe_allow_html=True)

    # 5. Risks & Non-Functional
    with tab_risks:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("5. Key Project Risks & Mitigations")
            risks = prd['ba_data'].get('risks', [])
            if not risks:
                st.write("No risks identified.")
            else:
                for idx, r in enumerate(risks, 1):
                    st.markdown(f"**Risk {idx}:** {r.get('risk', 'N/A')}")
                    st.success(f"**Mitigation:** {r.get('mitigation', 'N/A')}")
                    st.markdown("---")
                    
        with col2:
            st.subheader("6. Non-Functional Requirements")
            nf_reqs = prd['pm_data'].get('non_functional_requirements', [])
            if not nf_reqs:
                st.write("No non-functional requirements generated.")
            else:
                for idx, req in enumerate(nf_reqs, 1):
                    st.markdown(f"**[{req.get('category', 'General')}]** {req.get('description', 'N/A')}")
                    st.markdown("---")

else:
    # Form for new PRD generation
    st.subheader("💡 Submit a New Product Idea")
    
    with st.form("prd_input_form"):
        idea_input = st.text_area(
            "What product idea do you want to analyze?",
            placeholder="e.g., Build a mobile healthcare platform for remote consultations, medicine orders and tracking.",
            height=120
        )
        
        col1, col2 = st.columns(2)
        with col1:
            audience_input = st.text_input(
                "Target Audience (Optional)",
                placeholder="e.g., Working professionals, senior citizens who need regular checkups"
            )
        with col2:
            constraints_input = st.text_input(
                "Technical constraints / platform (Optional)",
                placeholder="e.g., HIPAA compliance, iOS and Android platforms, scalable backend"
            )
            
        submit_btn = st.form_submit_button("Generate PRD Specifications", type="primary")

    if submit_btn:
        if not idea_input.strip():
            st.error("Please enter a valid product idea to proceed!")
        else:
            # Running visual agent workflow
            with st.status("Executing Agentic Workflow...", expanded=True) as status:
                st.write("🔄 Initializing core pipelines and models...")
                time.sleep(1)
                
                # Run Business Analyst Agent
                st.write("🧠 **Business Analyst Agent** is analyzing the idea, target audience, and risks...")
                ba_data = ba_agent.analyze(
                    idea=idea_input, 
                    target_audience=audience_input if audience_input else "General", 
                    constraints=constraints_input if constraints_input else "None"
                )
                time.sleep(1.5)
                
                # Run Product Manager Agent
                st.write("📋 **Product Manager Agent** is constructing user stories and functional specifications...")
                pm_data = pm_agent.analyze(idea=idea_input, ba_analysis=ba_data)
                time.sleep(1.5)
                
                # Run database saving
                st.write("💾 **Database Manager** is compiling final PRD and storing in MongoDB...")
                new_id = db_manager.save_prd(
                    idea=idea_input,
                    target_audience=audience_input if audience_input else "General",
                    constraints=constraints_input if constraints_input else "None",
                    ba_data=ba_data,
                    pm_data=pm_data
                )
                time.sleep(1)
                
                status.update(label="PRD successfully generated and saved to MongoDB!", state="complete", expanded=False)
                
            # Load newly created PRD to show output
            st.session_state.selected_prd_id = new_id
            st.session_state.current_prd = db_manager.get_prd_by_id(new_id)
            st.rerun()
