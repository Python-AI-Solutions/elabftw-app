"""
Fiber Photometry Metadata Entry - Streamlit Application

This Streamlit page provides a user-friendly form for entering fiber photometry
experiment metadata that will be submitted to eLabFTW.

Author: elabftw-app
Created: 2025-11-03
License: MIT
"""

import os
import json
import streamlit as st
from datetime import datetime, date, time
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

try:
    import elabapi_python
    from elabapi_python.rest import ApiException
    ELABAPI_AVAILABLE = True
except ImportError:
    ELABAPI_AVAILABLE = False


# Page configuration
st.set_page_config(
    page_title="Fiber Photometry Metadata Entry",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .group-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #2c3e50;
        margin-top: 2rem;
        margin-bottom: 1rem;
        padding: 0.5rem;
        background-color: #ecf0f1;
        border-left: 5px solid #3498db;
    }
    .required-field {
        color: #e74c3c;
        font-weight: bold;
    }
    .help-text {
        font-size: 0.85rem;
        color: #7f8c8d;
        font-style: italic;
    }
    .success-box {
        padding: 1rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        color: #155724;
    }
    .error-box {
        padding: 1rem;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 5px;
        color: #721c24;
    }
    .warning-box {
        padding: 1rem;
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 5px;
        color: #856404;
    }
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """Initialize session state variables."""
    if 'metadata' not in st.session_state:
        st.session_state.metadata = {}
    if 'submission_success' not in st.session_state:
        st.session_state.submission_success = False
    if 'experiment_id' not in st.session_state:
        st.session_state.experiment_id = None
    if 'api_configured' not in st.session_state:
        st.session_state.api_configured = False


def check_api_configuration():
    """Check if eLabFTW API is configured."""
    api_key = os.environ.get('ELABFTW_API_KEY')
    elabftw_url = os.environ.get('ELABFTW_URL')

    if api_key and elabftw_url and ELABAPI_AVAILABLE:
        st.session_state.api_configured = True
        return True
    return False


def create_elabftw_client():
    """Create and return eLabFTW API client."""
    if not ELABAPI_AVAILABLE:
        st.error("⚠️ elabapi-python not installed. Install with: `pip install elabapi-python`")
        return None

    api_key = os.environ.get('ELABFTW_API_KEY')
    elabftw_url = os.environ.get('ELABFTW_URL')

    if not api_key or not elabftw_url:
        st.error("⚠️ eLabFTW credentials not configured. Set ELABFTW_API_KEY and ELABFTW_URL environment variables.")
        return None

    try:
        configuration = elabapi_python.Configuration()
        configuration.api_key['api_key'] = api_key
        configuration.api_key_prefix['api_key'] = 'Authorization'
        configuration.host = f"{elabftw_url}/api/v2"
        configuration.verify_ssl = os.environ.get('ELABFTW_VERIFY_SSL', 'true').lower() == 'true'

        api_client = elabapi_python.ApiClient(configuration)
        return elabapi_python.ExperimentsApi(api_client)
    except Exception as e:
        st.error(f"❌ Failed to create eLabFTW client: {e}")
        return None


def validate_required_fields(metadata):
    """Validate that all required fields are filled."""
    required_fields = [
        'subject_id', 'species', 'sex',
        'surgery_date', 'indicator_label', 'injection_location',
        'injection_ap', 'injection_ml', 'injection_dv',
        'session_id', 'session_date', 'session_time', 'experimenter',
        'fiber_core_diameter', 'fiber_na', 'excitation_wavelength',
        'emission_wavelength', 'recording_location'
    ]

    missing = []
    for field in required_fields:
        if field not in metadata or metadata[field] in [None, '', []]:
            missing.append(field.replace('_', ' ').title())

    return missing


def convert_to_elabftw_metadata(metadata):
    """Convert form data to eLabFTW extra_fields format."""
    extra_fields = {}

    # Subject Information
    if metadata.get('subject_id'):
        extra_fields['Subject ID'] = {'value': metadata['subject_id']}
    if metadata.get('species'):
        extra_fields['Species'] = {'value': metadata['species']}
    if metadata.get('sex'):
        extra_fields['Sex'] = {'value': metadata['sex']}
    if metadata.get('age_days'):
        extra_fields['Age (days)'] = {'value': str(metadata['age_days'])}
    if metadata.get('strain'):
        extra_fields['Strain'] = {'value': metadata['strain']}
    if metadata.get('genotype'):
        extra_fields['Genotype'] = {'value': metadata['genotype']}
    if metadata.get('weight'):
        extra_fields['Weight (grams)'] = {'value': str(metadata['weight'])}

    # Surgery & Injection
    if metadata.get('surgery_date'):
        extra_fields['Surgery Date'] = {'value': str(metadata['surgery_date'])}
    if metadata.get('indicator_label'):
        extra_fields['Indicator Label'] = {'value': metadata['indicator_label']}
    if metadata.get('injection_location'):
        extra_fields['Injection Location'] = {'value': metadata['injection_location']}
    if metadata.get('injection_ap') is not None:
        extra_fields['Injection AP (mm)'] = {'value': str(metadata['injection_ap'])}
    if metadata.get('injection_ml') is not None:
        extra_fields['Injection ML (mm)'] = {'value': str(metadata['injection_ml'])}
    if metadata.get('injection_dv') is not None:
        extra_fields['Injection DV (mm)'] = {'value': str(metadata['injection_dv'])}
    if metadata.get('viral_vector'):
        extra_fields['Viral Vector Name'] = {'value': metadata['viral_vector']}
    if metadata.get('viral_titer'):
        extra_fields['Viral Titer'] = {'value': metadata['viral_titer']}
    if metadata.get('injection_volume'):
        extra_fields['Injection Volume (nL)'] = {'value': str(metadata['injection_volume'])}
    if metadata.get('fiber_depth'):
        extra_fields['Fiber Implant Depth (mm)'] = {'value': str(metadata['fiber_depth'])}

    # Session Information
    if metadata.get('session_id'):
        extra_fields['Session ID'] = {'value': metadata['session_id']}
    if metadata.get('session_date'):
        extra_fields['Session Date'] = {'value': str(metadata['session_date'])}
    if metadata.get('session_time'):
        extra_fields['Session Time'] = {'value': str(metadata['session_time'])}
    if metadata.get('session_description'):
        extra_fields['Session Description'] = {'value': metadata['session_description']}
    if metadata.get('experimenter'):
        extra_fields['Experimenter'] = {'value': metadata['experimenter']}
    if metadata.get('laboratory'):
        extra_fields['Laboratory'] = {'value': metadata['laboratory']}
    if metadata.get('institution'):
        extra_fields['Institution'] = {'value': metadata['institution']}

    # Device Configuration
    if metadata.get('fiber_model'):
        extra_fields['Optical Fiber Model'] = {'value': metadata['fiber_model']}
    if metadata.get('fiber_core_diameter'):
        extra_fields['Fiber Core Diameter (μm)'] = {'value': str(metadata['fiber_core_diameter'])}
    if metadata.get('fiber_na') is not None:
        extra_fields['Fiber Numerical Aperture'] = {'value': str(metadata['fiber_na'])}
    if metadata.get('excitation_wavelength'):
        extra_fields['Excitation Wavelength (nm)'] = {'value': str(metadata['excitation_wavelength'])}
    if metadata.get('emission_wavelength'):
        extra_fields['Emission Wavelength (nm)'] = {'value': str(metadata['emission_wavelength'])}
    if metadata.get('dichroic_cutoff'):
        extra_fields['Dichroic Mirror Cut-on (nm)'] = {'value': str(metadata['dichroic_cutoff'])}
    if metadata.get('emission_filter_center'):
        extra_fields['Emission Filter Center (nm)'] = {'value': str(metadata['emission_filter_center'])}
    if metadata.get('emission_filter_bandwidth'):
        extra_fields['Emission Filter Bandwidth (nm)'] = {'value': str(metadata['emission_filter_bandwidth'])}
    if metadata.get('led_power'):
        extra_fields['LED Power (mW)'] = {'value': str(metadata['led_power'])}
    if metadata.get('pmt_gain'):
        extra_fields['PMT Gain'] = {'value': str(metadata['pmt_gain'])}

    # Recording Channel
    if metadata.get('recording_location'):
        extra_fields['Recording Location'] = {'value': metadata['recording_location']}
    if metadata.get('channel_name'):
        extra_fields['Channel Name'] = {'value': metadata['channel_name']}
    if metadata.get('sampling_rate'):
        extra_fields['Sampling Rate (Hz)'] = {'value': str(metadata['sampling_rate'])}

    # Provenance & Notes
    if metadata.get('protocol_name'):
        extra_fields['Protocol Name'] = {'value': metadata['protocol_name']}
    if metadata.get('data_file_path'):
        extra_fields['Data File Path'] = {'value': metadata['data_file_path']}
    if metadata.get('behavioral_task'):
        extra_fields['Behavioral Task'] = {'value': metadata['behavioral_task']}
    if metadata.get('drug_treatment'):
        extra_fields['Drug Treatment'] = {'value': metadata['drug_treatment']}
    if metadata.get('notes'):
        extra_fields['Notes'] = {'value': metadata['notes']}
    if metadata.get('analysis_status'):
        extra_fields['Analysis Status'] = {'value': metadata['analysis_status']}
    if metadata.get('quality_control'):
        extra_fields['Quality Control'] = {'value': metadata['quality_control']}

    return {'extra_fields': extra_fields}


def submit_to_elabftw(metadata, template_id=None):
    """Submit metadata to eLabFTW."""
    experiments_api = create_elabftw_client()
    if not experiments_api:
        return False, "API client not configured"

    try:
        # Convert metadata
        elabftw_metadata = convert_to_elabftw_metadata(metadata)

        # Create experiment title
        subject_id = metadata.get('subject_id', 'Unknown')
        session_date = metadata.get('session_date', date.today())
        title = f"FP Recording - {subject_id} - {session_date}"

        # Create experiment body
        body_text = f"""# Fiber Photometry Recording Session

**Subject**: {metadata.get('subject_id', 'N/A')}
**Session**: {metadata.get('session_id', 'N/A')}
**Date**: {metadata.get('session_date', 'N/A')} at {metadata.get('session_time', 'N/A')}
**Experimenter**: {metadata.get('experimenter', 'N/A')}

**Indicator**: {metadata.get('indicator_label', 'N/A')} @ {metadata.get('injection_location', 'N/A')}
**Recording Location**: {metadata.get('recording_location', 'N/A')}

---
*Created via Streamlit Metadata Entry App*
"""

        # Create experiment
        experiment_body = {
            'title': title,
            'body': body_text,
            'metadata': elabftw_metadata
        }

        if template_id:
            experiment_body['template_id'] = template_id

        result = experiments_api.post_experiment(body=experiment_body)

        return True, result.id

    except ApiException as e:
        return False, f"API Error: {e}"
    except Exception as e:
        return False, f"Error: {e}"


def save_to_json(metadata, filename=None):
    """Save metadata to JSON file."""
    if filename is None:
        subject_id = metadata.get('subject_id', 'unknown')
        session_date = metadata.get('session_date', date.today())
        filename = f"metadata_{subject_id}_{session_date}.json"

    try:
        with open(filename, 'w') as f:
            json.dump(metadata, f, indent=2, default=str)
        return True, filename
    except Exception as e:
        return False, str(e)


def load_from_json(uploaded_file):
    """Load metadata from JSON file."""
    try:
        content = uploaded_file.read()
        metadata = json.loads(content)
        return True, metadata
    except Exception as e:
        return False, str(e)


def main():
    """Main Streamlit application."""
    initialize_session_state()

    # Header
    st.markdown('<div class="main-header">🔬 Fiber Photometry Metadata Entry</div>', unsafe_allow_html=True)

    st.markdown("""
    Fill in the metadata for your fiber photometry experiment. Fields marked with
    <span class="required-field">*</span> are required.
    """, unsafe_allow_html=True)

    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Configuration")

        # Check API status
        api_configured = check_api_configuration()
        if api_configured:
            st.success("✅ eLabFTW API Configured")
        else:
            st.warning("⚠️ eLabFTW API Not Configured")
            st.info("Set environment variables:\n- ELABFTW_API_KEY\n- ELABFTW_URL")

        st.divider()

        # Template ID (optional)
        st.subheader("Template Settings")
        use_template = st.checkbox("Use existing template", value=False)
        template_id = None
        if use_template:
            template_id = st.number_input(
                "Template ID",
                min_value=1,
                value=5,
                help="ID of the fiber photometry template in eLabFTW"
            )

        st.divider()

        # Import/Export
        st.subheader("Import/Export")

        uploaded_file = st.file_uploader(
            "Load from JSON",
            type=['json'],
            help="Upload a previously saved metadata JSON file"
        )

        if uploaded_file is not None:
            success, result = load_from_json(uploaded_file)
            if success:
                st.session_state.metadata = result
                st.success("✅ Metadata loaded!")
                st.rerun()
            else:
                st.error(f"❌ Failed to load: {result}")

        if st.button("💾 Save to JSON"):
            if st.session_state.metadata:
                success, result = save_to_json(st.session_state.metadata)
                if success:
                    st.success(f"✅ Saved to {result}")
                else:
                    st.error(f"❌ Failed to save: {result}")
            else:
                st.warning("No metadata to save yet")

    # Main form
    with st.form("metadata_form"):

        # Group 1: Subject Information
        st.markdown('<div class="group-header">👤 Subject Information</div>', unsafe_allow_html=True)

        col1, col2, col3 = st.columns(3)

        with col1:
            subject_id = st.text_input(
                "Subject ID *",
                value=st.session_state.metadata.get('subject_id', ''),
                help="Unique subject identifier (e.g., M001, F023)",
                placeholder="M001"
            )

        with col2:
            species = st.selectbox(
                "Species *",
                options=["Mus musculus", "Rattus norvegicus", "Other"],
                index=0 if not st.session_state.metadata.get('species') else
                      ["Mus musculus", "Rattus norvegicus", "Other"].index(st.session_state.metadata.get('species')),
                help="Animal species"
            )

        with col3:
            sex = st.selectbox(
                "Sex *",
                options=["M", "F", "U"],
                index=None if not st.session_state.metadata.get('sex') else
                      ["M", "F", "U"].index(st.session_state.metadata.get('sex')),
                help="M=Male, F=Female, U=Unknown"
            )

        col4, col5, col6 = st.columns(3)

        with col4:
            age_days = st.number_input(
                "Age (days)",
                min_value=0,
                max_value=1000,
                value=st.session_state.metadata.get('age_days', 90),
                help="Age in days at time of session"
            )

        with col5:
            strain = st.text_input(
                "Strain",
                value=st.session_state.metadata.get('strain', ''),
                help="Genetic strain (e.g., C57BL/6J)",
                placeholder="C57BL/6J"
            )

        with col6:
            genotype = st.text_input(
                "Genotype",
                value=st.session_state.metadata.get('genotype', ''),
                help="Genetic modifications (e.g., Th-Cre+/-)",
                placeholder="Th-Cre+/-"
            )

        weight = st.number_input(
            "Weight (grams)",
            min_value=0.0,
            max_value=1000.0,
            value=st.session_state.metadata.get('weight', 25.0),
            step=0.1,
            help="Body weight in grams"
        )

        # Group 2: Surgery & Injection
        st.markdown('<div class="group-header">💉 Surgery & Injection</div>', unsafe_allow_html=True)

        col7, col8, col9 = st.columns(3)

        with col7:
            surgery_date = st.date_input(
                "Surgery Date *",
                value=st.session_state.metadata.get('surgery_date', date.today()),
                help="Date of viral injection and/or fiber implantation surgery"
            )

        with col8:
            indicator_label = st.selectbox(
                "Indicator Label *",
                options=["GCaMP6f", "GCaMP6s", "GCaMP7s", "GCaMP8", "jRGECO1a", "jRCaMP1a", "tdTomato", "mCherry", "Other"],
                index=0 if not st.session_state.metadata.get('indicator_label') else
                      ["GCaMP6f", "GCaMP6s", "GCaMP7s", "GCaMP8", "jRGECO1a", "jRCaMP1a", "tdTomato", "mCherry", "Other"].index(
                          st.session_state.metadata.get('indicator_label')),
                help="Fluorescent indicator type"
            )

        with col9:
            injection_location = st.text_input(
                "Injection Location *",
                value=st.session_state.metadata.get('injection_location', ''),
                help="Brain region or anatomical location (e.g., VTA, NAc, mPFC)",
                placeholder="VTA"
            )

        st.markdown("**Stereotactic Coordinates (mm from bregma/midline/surface)**")
        col10, col11, col12 = st.columns(3)

        with col10:
            injection_ap = st.number_input(
                "AP (Anterior-Posterior) *",
                min_value=-10.0,
                max_value=10.0,
                value=st.session_state.metadata.get('injection_ap', 0.0),
                step=0.1,
                help="Anterior-posterior coordinate in mm from bregma"
            )

        with col11:
            injection_ml = st.number_input(
                "ML (Medial-Lateral) *",
                min_value=-10.0,
                max_value=10.0,
                value=st.session_state.metadata.get('injection_ml', 0.0),
                step=0.1,
                help="Medial-lateral coordinate in mm from midline"
            )

        with col12:
            injection_dv = st.number_input(
                "DV (Dorsal-Ventral) *",
                min_value=0.0,
                max_value=15.0,
                value=st.session_state.metadata.get('injection_dv', 0.0),
                step=0.1,
                help="Dorsal-ventral coordinate in mm from brain surface"
            )

        col13, col14, col15 = st.columns(3)

        with col13:
            viral_vector = st.text_input(
                "Viral Vector Name",
                value=st.session_state.metadata.get('viral_vector', ''),
                help="Full viral construct name (e.g., AAV9-hSyn-GCaMP6f)",
                placeholder="AAV9-hSyn-GCaMP6f"
            )

        with col14:
            viral_titer = st.text_input(
                "Viral Titer",
                value=st.session_state.metadata.get('viral_titer', ''),
                help="Viral titer (e.g., 1e13 GC/mL, 1x10^12 vg/mL)",
                placeholder="1e13 GC/mL"
            )

        with col15:
            injection_volume = st.number_input(
                "Injection Volume (nL)",
                min_value=0.0,
                max_value=10000.0,
                value=st.session_state.metadata.get('injection_volume', 500.0),
                step=10.0,
                help="Volume injected in nanoliters"
            )

        fiber_depth = st.number_input(
            "Fiber Implant Depth (mm)",
            min_value=0.0,
            max_value=15.0,
            value=st.session_state.metadata.get('fiber_depth', 0.0),
            step=0.1,
            help="Depth of fiber tip from brain surface in mm"
        )

        # Group 3: Session Information
        st.markdown('<div class="group-header">📅 Session Information</div>', unsafe_allow_html=True)

        col16, col17, col18 = st.columns(3)

        with col16:
            session_id = st.text_input(
                "Session ID *",
                value=st.session_state.metadata.get('session_id', ''),
                help="Unique session identifier (e.g., session_20240115_M001)",
                placeholder="session_20240115_M001"
            )

        with col17:
            session_date = st.date_input(
                "Session Date *",
                value=st.session_state.metadata.get('session_date', date.today()),
                help="Date of recording session"
            )

        with col18:
            session_time = st.time_input(
                "Session Time *",
                value=st.session_state.metadata.get('session_time', time(14, 30)),
                help="Start time of recording session"
            )

        session_description = st.text_area(
            "Session Description",
            value=st.session_state.metadata.get('session_description', ''),
            help="Brief description (e.g., Baseline, Post-training, Drug administration)",
            placeholder="Baseline recording"
        )

        col19, col20, col21 = st.columns(3)

        with col19:
            experimenter = st.text_input(
                "Experimenter *",
                value=st.session_state.metadata.get('experimenter', ''),
                help="Name(s) of experimenter(s)",
                placeholder="John Doe"
            )

        with col20:
            laboratory = st.text_input(
                "Laboratory",
                value=st.session_state.metadata.get('laboratory', ''),
                help="Laboratory name",
                placeholder="Neuroscience Lab"
            )

        with col21:
            institution = st.text_input(
                "Institution",
                value=st.session_state.metadata.get('institution', 'NIH NIMH'),
                help="Institution name"
            )

        # Group 4: Device Configuration
        st.markdown('<div class="group-header">🔧 Device Configuration</div>', unsafe_allow_html=True)

        col22, col23, col24 = st.columns(3)

        with col22:
            fiber_model = st.text_input(
                "Optical Fiber Model",
                value=st.session_state.metadata.get('fiber_model', ''),
                help="Manufacturer and model (e.g., Doric MFC_400/430-0.48)",
                placeholder="Doric MFC_400/430-0.48"
            )

        with col23:
            fiber_core_diameter = st.number_input(
                "Fiber Core Diameter (μm) *",
                min_value=50.0,
                max_value=1000.0,
                value=st.session_state.metadata.get('fiber_core_diameter', 400.0),
                step=50.0,
                help="Core diameter in micrometers (common: 200, 400, 600)"
            )

        with col24:
            fiber_na = st.number_input(
                "Fiber Numerical Aperture *",
                min_value=0.1,
                max_value=1.0,
                value=st.session_state.metadata.get('fiber_na', 0.39),
                step=0.01,
                help="NA value (common: 0.22, 0.37, 0.39, 0.48)",
                format="%.2f"
            )

        col25, col26 = st.columns(2)

        with col25:
            excitation_wavelength = st.number_input(
                "Excitation Wavelength (nm) *",
                min_value=300.0,
                max_value=800.0,
                value=st.session_state.metadata.get('excitation_wavelength', 470.0),
                step=5.0,
                help="Excitation light wavelength in nanometers (e.g., 405, 470, 560)"
            )

        with col26:
            emission_wavelength = st.number_input(
                "Emission Wavelength (nm) *",
                min_value=400.0,
                max_value=900.0,
                value=st.session_state.metadata.get('emission_wavelength', 520.0),
                step=5.0,
                help="Detected emission wavelength in nanometers"
            )

        st.markdown("**Optional Filter Specifications**")
        col27, col28, col29 = st.columns(3)

        with col27:
            dichroic_cutoff = st.number_input(
                "Dichroic Mirror Cut-on (nm)",
                min_value=0.0,
                max_value=800.0,
                value=st.session_state.metadata.get('dichroic_cutoff', 0.0),
                step=5.0,
                help="Dichroic mirror cut-on wavelength in nm (optional)"
            )

        with col28:
            emission_filter_center = st.number_input(
                "Emission Filter Center (nm)",
                min_value=0.0,
                max_value=900.0,
                value=st.session_state.metadata.get('emission_filter_center', 0.0),
                step=5.0,
                help="Bandpass filter center wavelength in nm (optional)"
            )

        with col29:
            emission_filter_bandwidth = st.number_input(
                "Emission Filter Bandwidth (nm)",
                min_value=0.0,
                max_value=200.0,
                value=st.session_state.metadata.get('emission_filter_bandwidth', 0.0),
                step=5.0,
                help="Bandpass filter bandwidth in nm (optional)"
            )

        col30, col31 = st.columns(2)

        with col30:
            led_power = st.number_input(
                "LED Power (mW)",
                min_value=0.0,
                max_value=100.0,
                value=st.session_state.metadata.get('led_power', 0.0),
                step=0.1,
                help="LED output power in milliwatts"
            )

        with col31:
            pmt_gain = st.number_input(
                "PMT Gain",
                min_value=0.0,
                max_value=10000.0,
                value=st.session_state.metadata.get('pmt_gain', 0.0),
                step=10.0,
                help="Photomultiplier tube gain setting"
            )

        # Group 5: Recording Channel
        st.markdown('<div class="group-header">📡 Recording Channel</div>', unsafe_allow_html=True)

        col32, col33, col34 = st.columns(3)

        with col32:
            recording_location = st.text_input(
                "Recording Location *",
                value=st.session_state.metadata.get('recording_location', ''),
                help="Brain region for this recording channel (e.g., VTA)",
                placeholder="VTA"
            )

        with col33:
            channel_name = st.text_input(
                "Channel Name",
                value=st.session_state.metadata.get('channel_name', ''),
                help="Descriptive channel name (e.g., GCaMP6f_470nm, Isosbestic_405nm)",
                placeholder="GCaMP6f_470nm"
            )

        with col34:
            sampling_rate = st.number_input(
                "Sampling Rate (Hz)",
                min_value=0.0,
                max_value=10000.0,
                value=st.session_state.metadata.get('sampling_rate', 1000.0),
                step=100.0,
                help="Data acquisition sampling rate in Hz (e.g., 1000)"
            )

        # Group 6: Notes & Provenance
        st.markdown('<div class="group-header">📝 Notes & Provenance</div>', unsafe_allow_html=True)

        col35, col36 = st.columns(2)

        with col35:
            protocol_name = st.text_input(
                "Protocol Name",
                value=st.session_state.metadata.get('protocol_name', ''),
                help="Experimental protocol or SOP identifier",
                placeholder="Standard FP Protocol v2"
            )

        with col36:
            data_file_path = st.text_input(
                "Data File Path",
                value=st.session_state.metadata.get('data_file_path', ''),
                help="Path to raw data files (relative or absolute)",
                placeholder="/data/photometry/M001/"
            )

        col37, col38 = st.columns(2)

        with col37:
            behavioral_task = st.selectbox(
                "Behavioral Task",
                options=["", "Freely moving", "Head-fixed", "Operant conditioning",
                        "Social interaction", "Fear conditioning", "Open field", "Other"],
                index=0 if not st.session_state.metadata.get('behavioral_task') else
                      ["", "Freely moving", "Head-fixed", "Operant conditioning",
                       "Social interaction", "Fear conditioning", "Open field", "Other"].index(
                          st.session_state.metadata.get('behavioral_task')),
                help="Type of behavioral task during recording"
            )

        with col38:
            drug_treatment = st.text_input(
                "Drug Treatment",
                value=st.session_state.metadata.get('drug_treatment', ''),
                help="Any drugs administered (name, dose, route, timing)",
                placeholder="Saline, 1 mL, IP, -30 min"
            )

        notes = st.text_area(
            "Notes",
            value=st.session_state.metadata.get('notes', ''),
            help="Additional observations or comments",
            placeholder="Animal behaving normally..."
        )

        col39, col40 = st.columns(2)

        with col39:
            analysis_status = st.selectbox(
                "Analysis Status",
                options=["Pending", "In Progress", "Complete", "Failed", "Excluded"],
                index=0 if not st.session_state.metadata.get('analysis_status') else
                      ["Pending", "In Progress", "Complete", "Failed", "Excluded"].index(
                          st.session_state.metadata.get('analysis_status')),
                help="Current analysis status for tracking"
            )

        with col40:
            quality_control = st.selectbox(
                "Quality Control",
                options=["", "Pass", "Fail", "Needs Review"],
                index=0 if not st.session_state.metadata.get('quality_control') else
                      ["", "Pass", "Fail", "Needs Review"].index(
                          st.session_state.metadata.get('quality_control')),
                help="Data quality assessment"
            )

        # Submit button
        st.divider()
        submitted = st.form_submit_button("✅ Submit to eLabFTW", type="primary", use_container_width=True)

        if submitted:
            # Collect all metadata
            metadata = {
                'subject_id': subject_id,
                'species': species,
                'sex': sex,
                'age_days': age_days if age_days > 0 else None,
                'strain': strain if strain else None,
                'genotype': genotype if genotype else None,
                'weight': weight if weight > 0 else None,
                'surgery_date': surgery_date,
                'indicator_label': indicator_label,
                'injection_location': injection_location,
                'injection_ap': injection_ap,
                'injection_ml': injection_ml,
                'injection_dv': injection_dv,
                'viral_vector': viral_vector if viral_vector else None,
                'viral_titer': viral_titer if viral_titer else None,
                'injection_volume': injection_volume if injection_volume > 0 else None,
                'fiber_depth': fiber_depth if fiber_depth > 0 else None,
                'session_id': session_id,
                'session_date': session_date,
                'session_time': session_time,
                'session_description': session_description if session_description else None,
                'experimenter': experimenter,
                'laboratory': laboratory if laboratory else None,
                'institution': institution,
                'fiber_model': fiber_model if fiber_model else None,
                'fiber_core_diameter': fiber_core_diameter,
                'fiber_na': fiber_na,
                'excitation_wavelength': excitation_wavelength,
                'emission_wavelength': emission_wavelength,
                'dichroic_cutoff': dichroic_cutoff if dichroic_cutoff > 0 else None,
                'emission_filter_center': emission_filter_center if emission_filter_center > 0 else None,
                'emission_filter_bandwidth': emission_filter_bandwidth if emission_filter_bandwidth > 0 else None,
                'led_power': led_power if led_power > 0 else None,
                'pmt_gain': pmt_gain if pmt_gain > 0 else None,
                'recording_location': recording_location,
                'channel_name': channel_name if channel_name else None,
                'sampling_rate': sampling_rate if sampling_rate > 0 else None,
                'protocol_name': protocol_name if protocol_name else None,
                'data_file_path': data_file_path if data_file_path else None,
                'behavioral_task': behavioral_task if behavioral_task else None,
                'drug_treatment': drug_treatment if drug_treatment else None,
                'notes': notes if notes else None,
                'analysis_status': analysis_status,
                'quality_control': quality_control if quality_control else None
            }

            # Store in session state
            st.session_state.metadata = metadata

            # Validate required fields
            missing_fields = validate_required_fields(metadata)

            if missing_fields:
                st.error(f"❌ Please fill in the following required fields: {', '.join(missing_fields)}")
            else:
                # Submit to eLabFTW
                if api_configured:
                    with st.spinner("Submitting to eLabFTW..."):
                        success, result = submit_to_elabftw(metadata, template_id)

                    if success:
                        st.session_state.submission_success = True
                        st.session_state.experiment_id = result
                        st.success(f"✅ Successfully created experiment #{result} in eLabFTW!")
                        st.balloons()
                    else:
                        st.error(f"❌ Submission failed: {result}")
                else:
                    st.warning("⚠️ eLabFTW API not configured. Metadata saved locally only.")
                    # Auto-save to JSON
                    success, filename = save_to_json(metadata)
                    if success:
                        st.info(f"💾 Metadata saved to {filename}")


if __name__ == "__main__":
    main()
