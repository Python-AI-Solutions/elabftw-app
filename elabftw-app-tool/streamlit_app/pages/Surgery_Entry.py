"""
Surgery Data Entry Form

Dynamic form for recording surgical procedures with support for:
- Multiple viral vectors (add/remove rows)
- Multiple injection sites (add/remove rows)
- Multiple implant sites (add/remove rows)
- Multiple subjects/mice (add/remove rows)

Exports in eLabFTW-compatible JSON format for direct upload to notebooks.
Based on the Tejeda Lab surgery form (docs/surgery.html)
"""

import streamlit as st
import json
import os
from datetime import date
from typing import Any
from pathlib import Path

# Try to load environment variables
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent.parent.parent / '.env'
    load_dotenv(env_path)
except ImportError:
    pass

# Try to import elabapi
try:
    import elabapi_python
    from elabapi_python.rest import ApiException
    ELABAPI_AVAILABLE = True
except ImportError:
    ELABAPI_AVAILABLE = False

st.set_page_config(
    page_title="Surgery Data Entry",
    page_icon="🔬",
    layout="wide"
)

# Custom CSS for polished UI
st.markdown("""
<style>
    /* Main container styling */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    /* Header styling */
    .main-header {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 15px rgba(17, 153, 142, 0.3);
    }

    .main-header h1 {
        color: white;
        margin: 0;
        font-size: 2.5rem;
    }

    .main-header p {
        color: rgba(255, 255, 255, 0.9);
        margin: 0.5rem 0 0 0;
        font-size: 1.1rem;
    }

    /* Section headers */
    .section-header {
        display: flex;
        align-items: center;
        margin-bottom: 1rem;
        padding-bottom: 0.75rem;
        border-bottom: 2px solid #11998e;
    }

    .section-header h3 {
        margin: 0;
        color: #333;
        font-weight: 600;
    }

    /* Card styling for dynamic sections */
    .dynamic-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #e4e8ec 100%);
        border-radius: 10px;
        padding: 1.25rem;
        margin-bottom: 1rem;
        border-left: 4px solid #11998e;
    }

    /* Button styling */
    .stButton > button {
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.2s ease;
    }

    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    }

    /* Primary button */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        border: none;
    }

    /* Input field styling */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > div,
    .stNumberInput > div > div > input {
        border-radius: 8px;
        border: 1px solid #ddd;
        transition: all 0.2s ease;
    }

    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #11998e;
        box-shadow: 0 0 0 2px rgba(17, 153, 142, 0.2);
    }

    /* Metric styling */
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        color: white;
        margin-bottom: 0.5rem;
    }

    .metric-value {
        font-size: 2rem;
        font-weight: bold;
    }

    .metric-label {
        font-size: 0.9rem;
        opacity: 0.9;
    }

    /* Expander styling */
    .streamlit-expanderHeader {
        background: linear-gradient(135deg, #f5f7fa 0%, #e4e8ec 100%);
        border-radius: 8px;
        font-weight: 600;
    }

    /* Divider styling */
    hr {
        border: none;
        height: 2px;
        background: linear-gradient(90deg, transparent, #ddd, transparent);
        margin: 2rem 0;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


def upload_to_elabftw(metadata: dict, title: str, elabftw_url: str, api_key: str, verify_ssl: bool = False) -> tuple[bool, str, int | None]:
    """
    Upload experiment data to eLabFTW.

    Returns:
        Tuple of (success, message, experiment_id)
    """
    if not ELABAPI_AVAILABLE:
        return False, "elabapi-python not installed. Run: pip install elabapi-python", None

    try:
        # Initialize the API client
        configuration = elabapi_python.Configuration()
        configuration.host = f"{elabftw_url}/api/v2"
        configuration.verify_ssl = verify_ssl

        api_client = elabapi_python.ApiClient(configuration)
        api_client.set_default_header(header_name='Authorization', header_value=api_key)

        # Create the Experiments API client
        exp_client = elabapi_python.ExperimentsApi(api_client)

        # Test connection
        info_client = elabapi_python.InfoApi(api_client)
        info = info_client.get_info()

        # Create a new experiment
        response = exp_client.post_experiment_with_http_info()
        location_header = response[2].get('Location')
        experiment_id = int(location_header.split('/').pop())

        # Build patch body
        patch_body = {
            'title': title,
            'metadata': json.dumps(metadata)
        }

        # Update the experiment
        exp_client.patch_experiment(experiment_id, body=patch_body)

        return True, f"Successfully created experiment (ID: {experiment_id})", experiment_id

    except ApiException as e:
        return False, f"API Error: {e.reason} - {e.body}", None
    except Exception as e:
        return False, f"Error: {str(e)}", None

# Initialize session state for dynamic rows
if "num_viruses" not in st.session_state:
    st.session_state.num_viruses = 1
if "num_injections" not in st.session_state:
    st.session_state.num_injections = 1
if "num_implants" not in st.session_state:
    st.session_state.num_implants = 1
if "num_subjects" not in st.session_state:
    st.session_state.num_subjects = 1


def generate_elabftw_metadata() -> dict[str, Any]:
    """Generate eLabFTW-compatible metadata JSON from form data."""
    extra_fields = {}
    extra_fields_groups = []
    position = 1
    group_id = 1

    # Group 1: General Info
    extra_fields_groups.append({"id": group_id, "name": "General Info"})
    extra_fields["Date of Surgery"] = {
        "type": "date",
        "value": st.session_state.get("surgery_date", ""),
        "required": True,
        "position": position,
        "group_id": group_id
    }
    position += 1
    extra_fields["Experiment Description"] = {
        "type": "text",
        "value": st.session_state.get("experiment_desc", ""),
        "position": position,
        "group_id": group_id
    }
    position += 1
    extra_fields["Stereotax Number"] = {
        "type": "radio",
        "value": st.session_state.get("stereotax", ""),
        "options": ["1", "2", "3"],
        "position": position,
        "group_id": group_id
    }
    position += 1
    group_id += 1

    # Group 2: Surgery Type
    extra_fields_groups.append({"id": group_id, "name": "Surgery Type"})
    extra_fields["Intracranial Injection"] = {
        "type": "checkbox",
        "value": "on" if st.session_state.get("intracranial_injection", False) else "",
        "position": position,
        "group_id": group_id
    }
    position += 1
    extra_fields["Implant"] = {
        "type": "checkbox",
        "value": "on" if st.session_state.get("implant_checkbox", False) else "",
        "position": position,
        "group_id": group_id
    }
    position += 1
    extra_fields["Other Surgery Type"] = {
        "type": "text",
        "value": st.session_state.get("other_surgery_notes", ""),
        "position": position,
        "group_id": group_id
    }
    position += 1
    group_id += 1

    # Group 3: Injection Method
    extra_fields_groups.append({"id": group_id, "name": "Injection Method"})
    extra_fields["Glass Pipette"] = {
        "type": "checkbox",
        "value": "on" if st.session_state.get("glass_pipette", False) else "",
        "position": position,
        "group_id": group_id
    }
    position += 1
    extra_fields["Syringe Needle"] = {
        "type": "checkbox",
        "value": "on" if st.session_state.get("syringe_needle", False) else "",
        "position": position,
        "group_id": group_id
    }
    position += 1
    extra_fields["Other Injection Method"] = {
        "type": "text",
        "value": st.session_state.get("other_method_notes", ""),
        "position": position,
        "group_id": group_id
    }
    position += 1
    group_id += 1

    # Viral Vectors (dynamic groups)
    for i in range(st.session_state.num_viruses):
        extra_fields_groups.append({"id": group_id, "name": f"Viral Vector {i+1}"})
        prefix = f"virus_{i}_"
        extra_fields[f"Virus {i+1} Name"] = {
            "type": "text",
            "value": st.session_state.get(f"{prefix}name", ""),
            "position": position,
            "group_id": group_id
        }
        position += 1
        extra_fields[f"Virus {i+1} Source"] = {
            "type": "text",
            "value": st.session_state.get(f"{prefix}source", ""),
            "position": position,
            "group_id": group_id
        }
        position += 1
        extra_fields[f"Virus {i+1} Cat#"] = {
            "type": "text",
            "value": st.session_state.get(f"{prefix}cat", ""),
            "position": position,
            "group_id": group_id
        }
        position += 1
        extra_fields[f"Virus {i+1} Lot#"] = {
            "type": "text",
            "value": st.session_state.get(f"{prefix}lot", ""),
            "position": position,
            "group_id": group_id
        }
        position += 1
        extra_fields[f"Virus {i+1} Titer"] = {
            "type": "number",
            "value": str(st.session_state.get(f"{prefix}titer", "")),
            "units": ["vg/ml"],
            "position": position,
            "group_id": group_id
        }
        position += 1
        extra_fields[f"Virus {i+1} Dilution"] = {
            "type": "text",
            "value": st.session_state.get(f"{prefix}dilution", ""),
            "position": position,
            "group_id": group_id
        }
        position += 1
        group_id += 1

    # Injection Sites (dynamic groups)
    for i in range(st.session_state.num_injections):
        extra_fields_groups.append({"id": group_id, "name": f"Injection {i+1}"})
        prefix = f"inj_{i}_"
        extra_fields[f"Inj {i+1} Brain Area"] = {
            "type": "text",
            "value": st.session_state.get(f"{prefix}area", ""),
            "position": position,
            "group_id": group_id
        }
        position += 1
        extra_fields[f"Inj {i+1} Hemisphere"] = {
            "type": "radio",
            "value": st.session_state.get(f"{prefix}hemi", ""),
            "options": ["L", "R"],
            "position": position,
            "group_id": group_id
        }
        position += 1
        extra_fields[f"Inj {i+1} AP"] = {
            "type": "number",
            "value": str(st.session_state.get(f"{prefix}ap", "")),
            "units": ["mm"],
            "position": position,
            "group_id": group_id
        }
        position += 1
        extra_fields[f"Inj {i+1} ML"] = {
            "type": "number",
            "value": str(st.session_state.get(f"{prefix}ml", "")),
            "units": ["mm"],
            "position": position,
            "group_id": group_id
        }
        position += 1
        extra_fields[f"Inj {i+1} DV"] = {
            "type": "number",
            "value": str(st.session_state.get(f"{prefix}dv", "")),
            "units": ["mm"],
            "position": position,
            "group_id": group_id
        }
        position += 1
        extra_fields[f"Inj {i+1} Virus"] = {
            "type": "text",
            "value": st.session_state.get(f"{prefix}virus", ""),
            "position": position,
            "group_id": group_id
        }
        position += 1
        extra_fields[f"Inj {i+1} Volume"] = {
            "type": "number",
            "value": str(st.session_state.get(f"{prefix}vol", "")),
            "units": ["nl"],
            "position": position,
            "group_id": group_id
        }
        position += 1
        extra_fields[f"Inj {i+1} Speed"] = {
            "type": "number",
            "value": str(st.session_state.get(f"{prefix}speed", 100)),
            "units": ["nl/min"],
            "position": position,
            "group_id": group_id
        }
        position += 1
        group_id += 1

    # Implant Type group
    extra_fields_groups.append({"id": group_id, "name": "Implant Type"})
    extra_fields["Implant Type"] = {
        "type": "select",
        "value": st.session_state.get("implant_type", ""),
        "options": ["Cannula", "Fiber Optic", "GRIN Lens", "Prism Lens", "Other"],
        "position": position,
        "group_id": group_id
    }
    position += 1
    extra_fields["Other Implant Type"] = {
        "type": "text",
        "value": st.session_state.get("other_implant_type", ""),
        "position": position,
        "group_id": group_id
    }
    position += 1
    group_id += 1

    # Implant Sites (dynamic groups)
    for i in range(st.session_state.num_implants):
        extra_fields_groups.append({"id": group_id, "name": f"Implant {i+1}"})
        prefix = f"impl_{i}_"
        extra_fields[f"Implant {i+1} Brain Area"] = {
            "type": "text",
            "value": st.session_state.get(f"{prefix}area", ""),
            "position": position,
            "group_id": group_id
        }
        position += 1
        extra_fields[f"Implant {i+1} Hemisphere"] = {
            "type": "radio",
            "value": st.session_state.get(f"{prefix}hemi", ""),
            "options": ["L", "R"],
            "position": position,
            "group_id": group_id
        }
        position += 1
        extra_fields[f"Implant {i+1} AP"] = {
            "type": "number",
            "value": str(st.session_state.get(f"{prefix}ap", "")),
            "units": ["mm"],
            "position": position,
            "group_id": group_id
        }
        position += 1
        extra_fields[f"Implant {i+1} ML"] = {
            "type": "number",
            "value": str(st.session_state.get(f"{prefix}ml", "")),
            "units": ["mm"],
            "position": position,
            "group_id": group_id
        }
        position += 1
        extra_fields[f"Implant {i+1} DV"] = {
            "type": "number",
            "value": str(st.session_state.get(f"{prefix}dv", "")),
            "units": ["mm"],
            "position": position,
            "group_id": group_id
        }
        position += 1
        group_id += 1

    # Subjects (dynamic groups)
    for i in range(st.session_state.num_subjects):
        extra_fields_groups.append({"id": group_id, "name": f"Subject {i+1}"})
        prefix = f"subj_{i}_"
        extra_fields[f"Subject {i+1} ID"] = {
            "type": "text",
            "value": st.session_state.get(f"{prefix}id", ""),
            "position": position,
            "group_id": group_id
        }
        position += 1
        extra_fields[f"Subject {i+1} Strain"] = {
            "type": "text",
            "value": st.session_state.get(f"{prefix}strain", ""),
            "position": position,
            "group_id": group_id
        }
        position += 1
        extra_fields[f"Subject {i+1} Cage ID"] = {
            "type": "text",
            "value": st.session_state.get(f"{prefix}cage", ""),
            "position": position,
            "group_id": group_id
        }
        position += 1
        extra_fields[f"Subject {i+1} Genotype"] = {
            "type": "text",
            "value": st.session_state.get(f"{prefix}geno", ""),
            "position": position,
            "group_id": group_id
        }
        position += 1
        extra_fields[f"Subject {i+1} Sex"] = {
            "type": "radio",
            "value": st.session_state.get(f"{prefix}sex", ""),
            "options": ["M", "F"],
            "position": position,
            "group_id": group_id
        }
        position += 1
        extra_fields[f"Subject {i+1} DOB"] = {
            "type": "date",
            "value": st.session_state.get(f"{prefix}dob", ""),
            "position": position,
            "group_id": group_id
        }
        position += 1
        extra_fields[f"Subject {i+1} Weight"] = {
            "type": "number",
            "value": str(st.session_state.get(f"{prefix}weight", "")),
            "units": ["g"],
            "position": position,
            "group_id": group_id
        }
        position += 1
        extra_fields[f"Subject {i+1} Negate ML"] = {
            "type": "checkbox",
            "value": "on" if st.session_state.get(f"{prefix}negate", False) else "",
            "position": position,
            "group_id": group_id
        }
        position += 1
        extra_fields[f"Subject {i+1} Notes"] = {
            "type": "text",
            "value": st.session_state.get(f"{prefix}notes", ""),
            "position": position,
            "group_id": group_id
        }
        position += 1
        group_id += 1

    # Notes group
    extra_fields_groups.append({"id": group_id, "name": "Notes"})
    extra_fields["Injection Notes"] = {
        "type": "text",
        "value": st.session_state.get("injection_notes", ""),
        "position": position,
        "group_id": group_id
    }
    position += 1
    extra_fields["Implant Notes"] = {
        "type": "text",
        "value": st.session_state.get("implant_notes", ""),
        "position": position,
        "group_id": group_id
    }
    position += 1
    extra_fields["Surgery Notes"] = {
        "type": "text",
        "value": st.session_state.get("surgery_notes", ""),
        "position": position,
        "group_id": group_id
    }

    return {
        "extra_fields": extra_fields,
        "elabftw": {
            "display_main_text": False,
            "extra_fields_groups": extra_fields_groups
        }
    }


# Page Header with gradient styling
st.markdown("""
<div class="main-header">
    <h1>🔬 Surgery Data Entry</h1>
    <p>Record surgical procedures with dynamic tables. Add viruses, injections, implants, and subjects as needed.</p>
</div>
""", unsafe_allow_html=True)

# ============== General Info ==============
st.markdown('<div class="section-header"><h3>📋 General Information</h3></div>', unsafe_allow_html=True)
col1, col2, col3 = st.columns(3)

with col1:
    surgery_date = st.date_input("Date of Surgery *", value=date.today(), key="surgery_date_input")
    st.session_state.surgery_date = str(surgery_date)
with col2:
    stereotax = st.radio("Stereotax #", options=["1", "2", "3"], horizontal=True, key="stereotax")
with col3:
    pass

experiment_desc = st.text_area("Describe the experiments these surgeries are for", key="experiment_desc")

st.divider()

# ============== Surgery Type ==============
st.markdown('<div class="section-header"><h3>🏥 Surgery Type</h3></div>', unsafe_allow_html=True)
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.checkbox("Intracranial Injection", key="intracranial_injection")
with col2:
    st.checkbox("Implant", key="implant_checkbox")
with col3:
    other_surgery = st.checkbox("Other", key="other_surgery")
with col4:
    st.text_input("Other surgery notes", key="other_surgery_notes", disabled=not other_surgery)

st.divider()

# ============== Injection Method ==============
st.markdown('<div class="section-header"><h3>💉 Injection Method</h3></div>', unsafe_allow_html=True)
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.checkbox("Glass pipette", key="glass_pipette")
with col2:
    st.checkbox("Syringe needle", key="syringe_needle")
with col3:
    other_method = st.checkbox("Other method", key="other_method")
with col4:
    st.text_input("Other method notes", key="other_method_notes", disabled=not other_method)

st.divider()

# ============== Viral Vectors ==============
st.markdown('<div class="section-header"><h3>🧬 Viral Vectors</h3></div>', unsafe_allow_html=True)
col_add, col_remove, col_spacer = st.columns([1, 1, 4])
with col_add:
    if st.button("➕ Add Virus", use_container_width=True):
        st.session_state.num_viruses += 1
        st.rerun()
with col_remove:
    if st.session_state.num_viruses > 1:
        if st.button("➖ Remove Virus", use_container_width=True):
            st.session_state.num_viruses -= 1
            st.rerun()

for i in range(st.session_state.num_viruses):
    with st.expander(f"**Virus {i + 1}**", expanded=True):
        cols = st.columns([2, 1, 1, 1, 1, 1])
        with cols[0]:
            st.text_input("Viral Vector", key=f"virus_{i}_name")
        with cols[1]:
            st.text_input("Source", key=f"virus_{i}_source")
        with cols[2]:
            st.text_input("Cat#", key=f"virus_{i}_cat")
        with cols[3]:
            st.text_input("Lot#", key=f"virus_{i}_lot")
        with cols[4]:
            st.text_input("Titer (vg/ml)", key=f"virus_{i}_titer")
        with cols[5]:
            st.text_input("Dilution", key=f"virus_{i}_dilution")

st.divider()

# ============== Injection Sites ==============
st.markdown('<div class="section-header"><h3>📍 Injection Sites</h3></div>', unsafe_allow_html=True)
col_add, col_remove, col_spacer = st.columns([1, 1, 4])
with col_add:
    if st.button("➕ Add Injection", use_container_width=True):
        st.session_state.num_injections += 1
        st.rerun()
with col_remove:
    if st.session_state.num_injections > 1:
        if st.button("➖ Remove Injection", use_container_width=True):
            st.session_state.num_injections -= 1
            st.rerun()

for i in range(st.session_state.num_injections):
    with st.expander(f"**Injection {i + 1}**", expanded=True):
        cols = st.columns([1.5, 1, 1, 1, 1, 1, 1, 1])
        with cols[0]:
            st.text_input("Brain Area", key=f"inj_{i}_area")
        with cols[1]:
            st.radio("Hemi", options=["L", "R"], horizontal=True, key=f"inj_{i}_hemi")
        with cols[2]:
            st.number_input("A/P (mm)", step=0.1, format="%.2f", key=f"inj_{i}_ap")
        with cols[3]:
            st.number_input("M/L (mm)", step=0.1, format="%.2f", key=f"inj_{i}_ml")
        with cols[4]:
            st.number_input("D/V (mm)", step=0.1, format="%.2f", key=f"inj_{i}_dv")
        with cols[5]:
            st.text_input("Virus", key=f"inj_{i}_virus")
        with cols[6]:
            st.number_input("Vol (nl)", step=10.0, key=f"inj_{i}_vol")
        with cols[7]:
            st.number_input("Speed", value=100.0, step=10.0, key=f"inj_{i}_speed")

st.divider()

# ============== Implant Sites ==============
st.markdown('<div class="section-header"><h3>🔧 Implant Sites</h3></div>', unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    st.selectbox(
        "Implant Type",
        options=["", "Cannula", "Fiber Optic", "GRIN Lens", "Prism Lens", "Other"],
        key="implant_type"
    )
with col2:
    st.text_input("Other implant type", key="other_implant_type")

col_add, col_remove, col_spacer = st.columns([1, 1, 4])
with col_add:
    if st.button("➕ Add Implant", use_container_width=True):
        st.session_state.num_implants += 1
        st.rerun()
with col_remove:
    if st.session_state.num_implants > 1:
        if st.button("➖ Remove Implant", use_container_width=True):
            st.session_state.num_implants -= 1
            st.rerun()

for i in range(st.session_state.num_implants):
    with st.expander(f"**Implant {i + 1}**", expanded=True):
        cols = st.columns([2, 1, 1, 1, 1])
        with cols[0]:
            st.text_input("Brain Area", key=f"impl_{i}_area")
        with cols[1]:
            st.radio("Hemi", options=["L", "R"], horizontal=True, key=f"impl_{i}_hemi")
        with cols[2]:
            st.number_input("A/P (mm)", step=0.1, format="%.2f", key=f"impl_{i}_ap")
        with cols[3]:
            st.number_input("M/L (mm)", step=0.1, format="%.2f", key=f"impl_{i}_ml")
        with cols[4]:
            st.number_input("D/V (mm)", step=0.1, format="%.2f", key=f"impl_{i}_dv")

st.divider()

# ============== Subjects/Mice ==============
st.markdown('<div class="section-header"><h3>🐭 Subjects / Mice</h3></div>', unsafe_allow_html=True)
col_add, col_remove, col_spacer = st.columns([1, 1, 4])
with col_add:
    if st.button("➕ Add Subject", use_container_width=True):
        st.session_state.num_subjects += 1
        st.rerun()
with col_remove:
    if st.session_state.num_subjects > 1:
        if st.button("➖ Remove Subject", use_container_width=True):
            st.session_state.num_subjects -= 1
            st.rerun()

for i in range(st.session_state.num_subjects):
    with st.expander(f"**Subject {i + 1}**", expanded=True):
        cols = st.columns([1.5, 1.5, 1, 1, 0.8, 1, 1, 0.5, 2])
        with cols[0]:
            st.text_input("Subject ID", key=f"subj_{i}_id")
        with cols[1]:
            st.text_input("Strain", key=f"subj_{i}_strain")
        with cols[2]:
            st.text_input("Cage ID", key=f"subj_{i}_cage")
        with cols[3]:
            st.text_input("Genotype", key=f"subj_{i}_geno")
        with cols[4]:
            st.radio("Sex", options=["M", "F"], horizontal=True, key=f"subj_{i}_sex")
        with cols[5]:
            dob = st.date_input("DOB", value=None, key=f"subj_{i}_dob_input")
            st.session_state[f"subj_{i}_dob"] = str(dob) if dob else ""
        with cols[6]:
            st.number_input("Weight (g)", step=0.1, key=f"subj_{i}_weight")
        with cols[7]:
            st.checkbox("Neg ML", key=f"subj_{i}_negate")
        with cols[8]:
            st.text_input("Notes", key=f"subj_{i}_notes")

st.divider()

# ============== Notes ==============
st.markdown('<div class="section-header"><h3>📝 Notes</h3></div>', unsafe_allow_html=True)
col1, col2 = st.columns(2)
with col1:
    st.text_area("Notes for injection", key="injection_notes")
with col2:
    st.text_area("Notes for implant", key="implant_notes")

st.text_area("Surgery notes", key="surgery_notes")

st.divider()

# ============== Export ==============
st.markdown('<div class="section-header"><h3>💾 Export & Upload</h3></div>', unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📋 Generate eLabFTW JSON", type="primary", use_container_width=True):
        metadata = generate_elabftw_metadata()
        st.session_state.generated_metadata = metadata
        st.success("✅ eLabFTW metadata generated!")

with col2:
    if "generated_metadata" in st.session_state:
        json_str = json.dumps(st.session_state.generated_metadata, indent=2)
        st.download_button(
            label="⬇️ Download JSON",
            data=json_str,
            file_name="surgery_metadata.json",
            mime="application/json",
            use_container_width=True
        )

with col3:
    total_fields = len(st.session_state.get("generated_metadata", {}).get("extra_fields", {}))
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{total_fields}</div>
        <div class="metric-label">Total Fields</div>
    </div>
    """, unsafe_allow_html=True)

# Show preview
if "generated_metadata" in st.session_state:
    with st.expander("📄 Preview eLabFTW JSON", expanded=False):
        st.json(st.session_state.generated_metadata)

st.divider()

# ============== Upload to eLabFTW ==============
st.markdown('<div class="section-header"><h3>☁️ Upload to eLabFTW</h3></div>', unsafe_allow_html=True)

# Get API config from environment or session state
default_url = os.environ.get('ELABFTW_URL', 'https://localhost:3148')
default_api_key = os.environ.get('ELABFTW_API_KEY', '')

col_url, col_key = st.columns(2)
with col_url:
    elabftw_url = st.text_input("eLabFTW URL", value=default_url, key="elabftw_url")
with col_key:
    api_key = st.text_input("API Key", value=default_api_key, type="password", key="elabftw_api_key")

col_title, col_verify = st.columns([3, 1])
with col_title:
    experiment_title = st.text_input(
        "Experiment Title",
        value=f"Surgery - {st.session_state.get('surgery_date', date.today())}",
        key="experiment_title"
    )
with col_verify:
    verify_ssl = st.checkbox("Verify SSL", value=False, key="verify_ssl",
                            help="Disable for self-signed certificates")

# Upload button
if st.button("🚀 Upload to eLabFTW", type="primary", use_container_width=True):
    if not elabftw_url or not api_key:
        st.error("❌ Please provide eLabFTW URL and API Key")
    elif "generated_metadata" not in st.session_state:
        st.warning("⚠️ Please generate the JSON first by clicking 'Generate eLabFTW JSON'")
    else:
        with st.spinner("Uploading to eLabFTW..."):
            success, message, exp_id = upload_to_elabftw(
                metadata=st.session_state.generated_metadata,
                title=experiment_title,
                elabftw_url=elabftw_url,
                api_key=api_key,
                verify_ssl=verify_ssl
            )

        if success:
            st.success(f"✅ {message}")
            st.markdown(f"**View experiment:** [{elabftw_url}/experiments.php?mode=view&id={exp_id}]({elabftw_url}/experiments.php?mode=view&id={exp_id})")
        else:
            st.error(f"❌ {message}")

# API status indicator
if ELABAPI_AVAILABLE:
    st.caption("✅ elabapi-python is installed")
else:
    st.caption("⚠️ elabapi-python not installed. Run: `pip install elabapi-python`")

# Sidebar with styled summary
st.sidebar.markdown("""
<div style="background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); padding: 1rem; border-radius: 10px; margin-bottom: 1rem;">
    <h3 style="color: white; margin: 0;">📊 Form Summary</h3>
</div>
""", unsafe_allow_html=True)

# Summary metrics
st.sidebar.markdown(f"""
<div style="background: #f8f9fa; padding: 1rem; border-radius: 8px; margin-bottom: 0.5rem;">
    <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
        <span>🧬 Viruses</span>
        <strong>{st.session_state.num_viruses}</strong>
    </div>
    <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
        <span>📍 Injections</span>
        <strong>{st.session_state.num_injections}</strong>
    </div>
    <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
        <span>🔧 Implants</span>
        <strong>{st.session_state.num_implants}</strong>
    </div>
    <div style="display: flex; justify-content: space-between;">
        <span>🐭 Subjects</span>
        <strong>{st.session_state.num_subjects}</strong>
    </div>
</div>
""", unsafe_allow_html=True)

st.sidebar.divider()

st.sidebar.markdown("### 💡 Tips")
st.sidebar.markdown("""
<div style="background: #e8f5e9; padding: 0.75rem; border-radius: 8px; font-size: 0.85rem;">
• <strong>+ Add</strong> to add more rows<br>
• <strong>- Remove</strong> to delete last row<br>
• <strong>Generate JSON</strong> for export<br>
• <strong>Upload</strong> directly to eLabFTW
</div>
""", unsafe_allow_html=True)

st.sidebar.divider()

# Reset button with styling
if st.sidebar.button("🔄 Reset Form", use_container_width=True, type="secondary"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()
