"""
eLabFTW Fiber Photometry Metadata Tool
Home Page - User Journey Navigation

This is the main landing page for the eLabFTW integration tool suite.
Choose your workflow based on your starting point:
- Journey A: Validate and fix existing eLabFTW entries
- Journey B: Create new entries from scratch
- Journey C: Add NWB template to blank entries

Author: elabftw-app
Created: 2025-11-04
License: MIT
"""

import streamlit as st
from pathlib import Path

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    # Load .env from project root (three levels up from this file)
    env_path = Path(__file__).parent.parent.parent / '.env'
    load_dotenv(env_path)
except ImportError:
    pass  # dotenv not installed, will use system env vars

# Page configuration
st.set_page_config(
    page_title="eLabFTW Fiber Photometry Tool",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS with enhanced styling
st.markdown("""
<style>
    /* Main container */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    /* Hero header */
    .hero-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 3rem 2rem;
        border-radius: 20px;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 10px 40px rgba(102, 126, 234, 0.3);
    }

    .hero-header h1 {
        color: white;
        font-size: 3rem;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.2);
    }

    .hero-header p {
        color: rgba(255, 255, 255, 0.9);
        font-size: 1.2rem;
        margin-top: 1rem;
    }

    .main-title {
        font-size: 3rem;
        font-weight: bold;
        color: #2c3e50;
        text-align: center;
        margin-bottom: 1rem;
    }
    .subtitle {
        font-size: 1.2rem;
        color: #7f8c8d;
        text-align: center;
        margin-bottom: 3rem;
    }

    /* Journey cards */
    .journey-card {
        padding: 2rem;
        border-radius: 15px;
        margin: 1rem 0;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        transition: all 0.3s ease;
    }
    .journey-card:hover {
        transform: translateY(-8px);
        box-shadow: 0 12px 30px rgba(0, 0, 0, 0.2);
    }
    .journey-a {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    .journey-b {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
    }
    .journey-c {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        color: white;
    }
    .journey-title {
        font-size: 1.8rem;
        font-weight: bold;
        margin-bottom: 1rem;
    }
    .journey-desc {
        font-size: 1rem;
        margin-bottom: 1.5rem;
        line-height: 1.6;
    }
    .journey-steps {
        font-size: 0.9rem;
        margin-bottom: 1rem;
    }
    .journey-time {
        font-size: 0.85rem;
        opacity: 0.9;
        font-style: italic;
    }

    /* Info section */
    .info-section {
        background: linear-gradient(135deg, #f5f7fa 0%, #e4e8ec 100%);
        padding: 2rem;
        border-radius: 15px;
        margin: 2rem 0;
    }

    /* Feature cards */
    .feature-list {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 1rem;
        margin: 2rem 0;
    }
    .feature-item {
        background-color: white;
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 4px solid #667eea;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
        transition: all 0.2s ease;
    }
    .feature-item:hover {
        transform: translateX(5px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    }

    /* Button styling */
    .stButton > button {
        border-radius: 10px;
        font-weight: 600;
        padding: 0.75rem 2rem;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15);
    }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border: none;
    }

    /* Section titles */
    .section-title {
        font-size: 1.8rem;
        font-weight: 700;
        color: #2c3e50;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 3px solid #667eea;
        display: inline-block;
    }

    /* Divider styling */
    hr {
        border: none;
        height: 2px;
        background: linear-gradient(90deg, transparent, #667eea, transparent);
        margin: 2.5rem 0;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# Hero Header
st.markdown("""
<div class="hero-header">
    <h1>🧪 eLabFTW Fiber Photometry Tool</h1>
    <p>NWB-Compliant Metadata Management for ndx-fiber-photometry</p>
</div>
""", unsafe_allow_html=True)

# Introduction
st.markdown("""
<div style="text-align: center; padding: 1rem 0; font-size: 1.1rem; color: #555;">
    This tool suite helps you manage fiber photometry experiment metadata in eLabFTW
    with full compliance to the <strong>ndx-fiber-photometry</strong> NWB extension standard.
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# Journey Selection Section
st.markdown("## 🗺️ Choose Your User Journey")

st.markdown("""
Select the workflow that matches your current situation. Each journey is designed
for a specific starting point and goal.
""")

# Journey A
st.markdown("""
<div class="journey-card journey-a">
    <div class="journey-title">🔍 Journey A: Validate & Fix Existing Entry</div>
    <div class="journey-desc">
    <strong>Starting Point:</strong> You already have an eLabFTW experiment entry with some metadata.<br>
    <strong>Goal:</strong> Validate it against ndx-fiber-photometry schema and fill in missing required fields.
    </div>
    <div class="journey-steps">
    <strong>Workflow:</strong><br>
    1️⃣ Load your existing eLabFTW experiment by ID<br>
    2️⃣ Automatic validation against 18 required fields<br>
    3️⃣ See which fields are missing or have invalid data<br>
    4️⃣ Fill in missing fields using a smart form<br>
    5️⃣ Update your experiment with validated metadata
    </div>
    <div class="journey-time">⏱️ Estimated time: 5-10 minutes per experiment</div>
</div>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if st.button("🚀 Start Journey A", type="primary", use_container_width=True, key="journey_a"):
        st.switch_page("pages/A_Validate_Existing.py")

st.markdown("<br>", unsafe_allow_html=True)

# Journey B
st.markdown("""
<div class="journey-card journey-b">
    <div class="journey-title">📝 Journey B: Create New Entry from Form</div>
    <div class="journey-desc">
    <strong>Starting Point:</strong> You have experiment data and want to enter it fresh.<br>
    <strong>Goal:</strong> Fill out a comprehensive form and push metadata to a new or existing eLabFTW entry.
    </div>
    <div class="journey-steps">
    <strong>Workflow:</strong><br>
    1️⃣ Fill out comprehensive metadata form (45 fields in 6 groups)<br>
    2️⃣ Required fields validated in real-time<br>
    3️⃣ Smart defaults and dropdown options provided<br>
    4️⃣ Save/load progress as JSON for later<br>
    5️⃣ Submit directly to eLabFTW or save locally
    </div>
    <div class="journey-time">⏱️ Estimated time: 15-20 minutes per experiment</div>
</div>
""", unsafe_allow_html=True)

col4, col5, col6 = st.columns([1, 2, 1])
with col5:
    if st.button("🚀 Start Journey B", type="primary", use_container_width=True, key="journey_b"):
        st.switch_page("pages/Metadata_Entry.py")

st.markdown("<br>", unsafe_allow_html=True)

# Journey C
st.markdown("""
<div class="journey-card journey-c">
    <div class="journey-title">📋 Journey C: Add Template to Blank Entry</div>
    <div class="journey-desc">
    <strong>Starting Point:</strong> You have a blank eLabFTW experiment entry.<br>
    <strong>Goal:</strong> Inject the full ndx-fiber-photometry template structure into your entry.
    </div>
    <div class="journey-steps">
    <strong>Workflow:</strong><br>
    1️⃣ Preview the template (45 fields, 6 groups, 18 required)<br>
    2️⃣ Enter your blank eLabFTW experiment ID<br>
    3️⃣ App loads experiment info and checks current state<br>
    4️⃣ Click to apply full template to your entry<br>
    5️⃣ Template structure instantly added to eLabFTW
    </div>
    <div class="journey-time">⏱️ Estimated time: 2-3 minutes per experiment</div>
</div>
""", unsafe_allow_html=True)

col7, col8, col9 = st.columns([1, 2, 1])
with col8:
    if st.button("🚀 Start Journey C", type="primary", use_container_width=True, key="journey_c"):
        st.switch_page("pages/C_Add_Template.py")

st.markdown("---")

# Data Entry Forms Section
st.markdown("## 📝 Data Entry Forms")

st.markdown("""
These dynamic forms allow you to record experiment data with flexible tables.
Add or remove rows/columns as needed for your specific protocol.
""")

col_form1, col_form2 = st.columns(2)

with col_form1:
    st.markdown("""
    <div class="journey-card" style="background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); color: white; padding: 1.5rem; border-radius: 10px;">
        <div class="journey-title" style="font-size: 1.5rem; font-weight: bold;">🔬 Surgery Data Entry</div>
        <div class="journey-desc" style="margin: 1rem 0;">
        Record surgical procedures with dynamic tables for:<br>
        • Viral vectors (add as many as needed)<br>
        • Injection sites<br>
        • Implant sites<br>
        • Subjects/mice
        </div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("🚀 Open Surgery Form", type="primary", use_container_width=True, key="surgery_form"):
        st.switch_page("pages/Surgery_Entry.py")

with col_form2:
    st.markdown("""
    <div class="journey-card" style="background: linear-gradient(135deg, #ff9966 0%, #ff5e62 100%); color: white; padding: 1.5rem; border-radius: 10px;">
        <div class="journey-title" style="font-size: 1.5rem; font-weight: bold;">🐭 Behavior Session</div>
        <div class="journey-desc" style="margin: 1rem 0;">
        Record behavior experiments with:<br>
        • Session information<br>
        • Dynamic outcome columns<br>
        • Multiple subjects per session<br>
        • Export to CSV/JSON
        </div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("🚀 Open Behavior Form", type="primary", use_container_width=True, key="behavior_form"):
        st.switch_page("pages/Behavior_Entry.py")

st.markdown("---")

# Key Features Section
st.markdown("""
<div class="info-section">
    <h2>✨ Key Features</h2>
</div>
""", unsafe_allow_html=True)

col10, col11, col12 = st.columns(3)

with col10:
    st.markdown("""
    **📊 NWB Compliance**
    - 45 fields covering all ndx-fiber-photometry requirements
    - 18 required fields for NWB file generation
    - 6 organized groups matching NWB structure
    - Validation against data ranges (coordinates, wavelengths)
    """)

with col11:
    st.markdown("""
    **🔗 eLabFTW Integration**
    - Direct API connection via elabapi-python
    - Read existing experiments
    - Create new experiments
    - Update metadata on existing entries
    - Merge templates with existing data
    """)

with col12:
    st.markdown("""
    **🛠️ User-Friendly Interface**
    - Smart input types (dates, numbers, dropdowns)
    - Real-time validation feedback
    - Import/export JSON for data portability
    - Clear error messages and guidance
    - Progress tracking and session state
    """)

st.markdown("---")

# Template Information
st.markdown("## 📋 About the Template")

col13, col14 = st.columns(2)

with col13:
    st.markdown("""
    **Template Structure:**
    - **Total Fields:** 45
    - **Required Fields:** 18 (marked with *)
    - **Optional Fields:** 27
    - **Field Groups:** 6

    **Groups:**
    1. Subject Information (7 fields)
    2. Surgery & Injection (10 fields)
    3. Session Information (7 fields)
    4. Device Configuration (10 fields)
    5. Recording Channel (3 fields)
    6. Notes & Provenance (8 fields)
    """)

with col14:
    st.markdown("""
    **NWB Mapping:**

    The template maps to 12 NWB object types:
    - Subject (animal metadata)
    - Indicator (fluorescent indicator)
    - Viral Vector (injection details)
    - Fiber Insertion (surgical details)
    - Session (recording session)
    - Optical Fiber (hardware)
    - Excitation Source (laser/LED)
    - Photodetector (sensor)
    - Dichroic Mirror (optics)
    - Emission Filter (optics)
    - Fiber Photometry Table (data structure)
    - Provenance (tracking info)
    """)

# Configuration Check
st.markdown("---")
st.markdown("## ⚙️ Configuration Status")

with st.sidebar:
    st.header("📚 Documentation")

    st.markdown("""
    **Quick Links:**
    - [Template JSON](../templates/fiber_photometry_template.json)
    - [Parser Script](../scripts/parse_elabftw_metadata.py)
    - [Template Creation Guide](../docs/elabftw-template-creation-guide.md)
    - [Parser Usage Guide](../docs/parser-usage-guide.md)
    - [Research Document](../docs/elabftw-ndx-photometry-research.md)
    """)

    st.divider()

    st.markdown("""
    **Need Help?**

    - Check the README.md in each directory
    - Review the template JSON for field definitions
    - Consult the research document for technical details
    - Test with Journey B (form entry) first if new
    """)

    st.divider()

    st.markdown("""
    **Version:** 1.0.0
    **Updated:** 2025-11-04
    **License:** MIT
    """)

# Check API configuration
import os
try:
    import elabapi_python
    ELABAPI_AVAILABLE = True
except ImportError:
    ELABAPI_AVAILABLE = False

api_key = os.environ.get('ELABFTW_API_KEY')
elabftw_url = os.environ.get('ELABFTW_URL')

col15, col16 = st.columns(2)

with col15:
    if api_key and elabftw_url and ELABAPI_AVAILABLE:
        st.success("✅ eLabFTW API is configured and ready")
        st.markdown(f"**Server:** {elabftw_url}")
    elif not ELABAPI_AVAILABLE:
        st.warning("⚠️ elabapi-python not installed")
        st.markdown("Install with: `pip install elabapi-python`")
    else:
        st.error("❌ eLabFTW API not configured")
        st.markdown("""
        Set environment variables:
        ```bash
        export ELABFTW_API_KEY="your_key"
        export ELABFTW_URL="https://your-elabftw.com"
        ```
        """)

with col16:
    st.info("""
    **What you need:**
    - eLabFTW instance with API access
    - API key from User Panel → API Keys
    - Python 3.13 with required packages
    - Internet connection for API calls
    """)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #7f8c8d; padding: 2rem;">
    <p><strong>elabftw-app</strong> | eLabFTW Integration Tool Suite</p>
    <p>Built for ndx-fiber-photometry NWB extension compliance</p>
    <p>Supporting reproducible neuroscience research workflows</p>
</div>
""", unsafe_allow_html=True)
