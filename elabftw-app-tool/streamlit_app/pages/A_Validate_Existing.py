"""
User Journey A: Validate Existing eLabFTW Entry

This app allows users to:
1. Connect to an existing eLabFTW experiment
2. Validate if it fits the ndx-fiber-photometry schema
3. Identify missing required fields
4. Fill in missing fields via form
5. Update the experiment

Author: elabftw-app
Created: 2025-11-03
License: MIT
"""

import os
import json
import streamlit as st
from pathlib import Path
import sys

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    # Load .env from project root (three levels up from this file)
    env_path = Path(__file__).parent.parent.parent.parent / '.env'
    load_dotenv(env_path)
except ImportError:
    pass  # dotenv not installed, will use system env vars

# Add parent directory to path for imports
streamlit_app_dir = Path(__file__).parent.parent  # elabftw-app-tool/streamlit_app
elabftw_tool_dir = streamlit_app_dir.parent  # elabftw-app-tool
sys.path.append(str(elabftw_tool_dir))

try:
    import elabapi_python
    from elabapi_python.rest import ApiException
    ELABAPI_AVAILABLE = True
except ImportError:
    ELABAPI_AVAILABLE = False

try:
    from scripts.parse_elabftw_metadata import ELabFTWMetadataParser
    PARSER_AVAILABLE = True
    print(f"✓ Parser imported successfully from: {elabftw_tool_dir / 'scripts' / 'parse_elabftw_metadata.py'}")
except ImportError as e:
    PARSER_AVAILABLE = False
    print(f"❌ Failed to import parser: {e}")
    print(f"   Tried to import from: {elabftw_tool_dir}")
    print(f"   sys.path: {sys.path}")


# Page configuration
st.set_page_config(
    page_title="Validate Existing Entry - User Journey A",
    page_icon="✅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #27ae60;
        margin-bottom: 1rem;
    }
    .section-header {
        font-size: 1.8rem;
        font-weight: bold;
        color: #2c3e50;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .success-box {
        padding: 1.5rem;
        background-color: #d4edda;
        border: 2px solid #c3e6cb;
        border-radius: 8px;
        color: #155724;
        margin: 1rem 0;
    }
    .error-box {
        padding: 1.5rem;
        background-color: #f8d7da;
        border: 2px solid #f5c6cb;
        border-radius: 8px;
        color: #721c24;
        margin: 1rem 0;
    }
    .warning-box {
        padding: 1.5rem;
        background-color: #fff3cd;
        border: 2px solid #ffeaa7;
        border-radius: 8px;
        color: #856404;
        margin: 1rem 0;
    }
    .info-box {
        padding: 1.5rem;
        background-color: #d1ecf1;
        border: 2px solid #bee5eb;
        border-radius: 8px;
        color: #0c5460;
        margin: 1rem 0;
    }
    .field-missing {
        color: #e74c3c;
        font-weight: bold;
    }
    .field-present {
        color: #27ae60;
    }
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """Initialize session state variables."""
    if 'experiment_loaded' not in st.session_state:
        st.session_state.experiment_loaded = False
    if 'experiment_data' not in st.session_state:
        st.session_state.experiment_data = None
    if 'validation_errors' not in st.session_state:
        st.session_state.validation_errors = []
    if 'validation_warnings' not in st.session_state:
        st.session_state.validation_warnings = []
    if 'missing_fields' not in st.session_state:
        st.session_state.missing_fields = []
    if 'nwb_metadata' not in st.session_state:
        st.session_state.nwb_metadata = None
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
        configuration.host = f"{elabftw_url}/api/v2"
        configuration.verify_ssl = os.environ.get('ELABFTW_VERIFY_SSL', 'true').lower() == 'true'

        # Create API client
        api_client = elabapi_python.ApiClient(configuration)

        # Set Authorization header directly (this is the correct way for eLabFTW)
        api_client.default_headers['Authorization'] = api_key

        return elabapi_python.ExperimentsApi(api_client)
    except Exception as e:
        st.error(f"❌ Failed to create eLabFTW client: {e}")
        return None


def load_experiment(experiment_id):
    """Load experiment from eLabFTW using raw API call to handle metadata correctly."""
    import requests
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    api_key = os.environ.get('ELABFTW_API_KEY')
    elabftw_url = os.environ.get('ELABFTW_URL')
    verify_ssl = os.environ.get('ELABFTW_VERIFY_SSL', 'true').lower() == 'true'

    if not api_key or not elabftw_url:
        return False, "API credentials not configured"

    try:
        # Make raw API call to get proper metadata
        response = requests.get(
            f"{elabftw_url}/api/v2/experiments/{experiment_id}",
            headers={'Authorization': api_key},
            verify=verify_ssl
        )

        if response.status_code == 200:
            data = response.json()

            # Parse metadata if it's a JSON string (double-encoded)
            metadata = data.get('metadata', {})
            if isinstance(metadata, str):
                metadata = json.loads(metadata)

            # Further parse if metadata itself contains a JSON string
            if isinstance(metadata, str):
                metadata = json.loads(metadata)

            # Extract the actual metadata if it's nested (eLabFTW returns nested structure)
            if isinstance(metadata, dict) and 'metadata' in metadata:
                metadata = metadata['metadata']

            return True, {
                'id': data.get('id'),
                'title': data.get('title'),
                'body': data.get('body'),
                'metadata': metadata,
                'created_at': data.get('created_at'),
                'modified_at': data.get('modified_at')
            }
        else:
            return False, f"API Error: {response.status_code} - {response.text}"

    except json.JSONDecodeError as e:
        return False, f"JSON decode error: {e}"
    except Exception as e:
        return False, f"Error: {e}"


def validate_experiment(experiment_data):
    """Validate experiment against ndx-fiber-photometry schema."""
    if not PARSER_AVAILABLE:
        print("❌ Parser not available")
        return [], [], {}, "Parser not available"

    try:
        print("\n" + "=" * 70)
        print("VALIDATION DEBUG")
        print("=" * 70)

        # Create parser
        parser = ELabFTWMetadataParser(
            api_key=os.environ.get('ELABFTW_API_KEY', 'mock'),
            elabftw_url=os.environ.get('ELABFTW_URL', 'https://mock.com'),
            verify_ssl=os.environ.get('ELABFTW_VERIFY_SSL', 'true').lower() == 'true'
        )
        print("✓ Parser created")

        # Get metadata
        metadata = experiment_data.get('metadata', {})

        # Debug: Check metadata structure
        print(f"\nMetadata type: {type(metadata)}")
        print(f"Metadata is dict: {isinstance(metadata, dict)}")
        if isinstance(metadata, dict):
            print(f"Metadata keys: {list(metadata.keys())}")
            if 'extra_fields' in metadata:
                print(f"Extra fields count: {len(metadata['extra_fields'])}")
                print(f"Extra fields type: {type(metadata['extra_fields'])}")
                # Show first few field names
                field_names = list(metadata['extra_fields'].keys())[:5]
                print(f"First 5 fields: {field_names}")
        else:
            print(f"⚠️ Metadata is not a dict! Value: {metadata}")

        # Validate
        print("\nCalling validate_required_fields()...")
        errors = parser.validate_required_fields(metadata)
        print(f"✓ Validation completed. Errors found: {len(errors)}")

        if errors:
            print("\nValidation errors:")
            for i, error in enumerate(errors, 1):
                print(f"  {i}. {error}")
        else:
            print("  No errors - validation passed!")

        print("\nCalling validate_data_ranges()...")
        warnings = parser.validate_data_ranges(metadata)
        print(f"✓ Data range validation completed. Warnings: {len(warnings)}")

        # Map to NWB
        print("\nCalling map_to_nwb_metadata()...")
        nwb_metadata = parser.map_to_nwb_metadata(metadata)
        print(f"✓ NWB mapping completed. Keys: {list(nwb_metadata.keys())}")

        print("\n" + "=" * 70)
        print(f"VALIDATION COMPLETE: {len(errors)} errors, {len(warnings)} warnings")
        print("=" * 70 + "\n")

        return errors, warnings, nwb_metadata, None

    except Exception as e:
        # Print the actual error to terminal
        print("\n" + "!" * 70)
        print("EXCEPTION DURING VALIDATION")
        print("!" * 70)
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        print("!" * 70 + "\n")

        # Also show in Streamlit
        st.error(f"⚠️ Exception during validation: {e}")
        return [], [], {}, f"Validation error: {e}"


def get_field_value_from_metadata(metadata, field_name):
    """Get field value from eLabFTW metadata."""
    extra_fields = metadata.get('extra_fields', {})
    field_data = extra_fields.get(field_name, {})
    return field_data.get('value', '')


def update_experiment_metadata(experiment_id, new_fields):
    """Update experiment with missing fields using raw API call."""
    import requests
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    api_key = os.environ.get('ELABFTW_API_KEY')
    elabftw_url = os.environ.get('ELABFTW_URL')
    verify_ssl = os.environ.get('ELABFTW_VERIFY_SSL', 'true').lower() == 'true'

    if not api_key or not elabftw_url:
        return False, "API credentials not configured"

    try:
        # Get current experiment metadata
        success, exp_data = load_experiment(experiment_id)
        if not success:
            return False, f"Failed to load experiment: {exp_data}"

        current_metadata = exp_data.get('metadata', {})
        current_extra_fields = current_metadata.get('extra_fields', {})

        # Merge new fields
        for field_name, value in new_fields.items():
            if field_name not in current_extra_fields or not current_extra_fields[field_name].get('value'):
                current_extra_fields[field_name] = {
                    'type': 'text',
                    'value': str(value)
                }

        # Update metadata
        updated_metadata = {
            'extra_fields': current_extra_fields,
            'elabftw': current_metadata.get('elabftw', {})
        }

        # Patch experiment using raw API
        response = requests.patch(
            f"{elabftw_url}/api/v2/experiments/{experiment_id}",
            headers={
                'Authorization': api_key,
                'Content-Type': 'application/json'
            },
            json={'metadata': json.dumps(updated_metadata)},  # Encode as JSON string
            verify=verify_ssl
        )

        if response.status_code == 200:
            return True, "Experiment updated successfully"
        else:
            return False, f"API Error: {response.status_code} - {response.text}"

    except Exception as e:
        return False, f"Error: {e}"


def main():
    """Main Streamlit application."""
    initialize_session_state()

    # Header
    st.markdown('<div class="main-header">✅ User Journey A: Validate Existing Entry</div>', unsafe_allow_html=True)

    st.markdown("""
    This tool helps you validate an existing eLabFTW experiment entry against the
    **ndx-fiber-photometry** NWB schema and fill in any missing required fields.
    """)

    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuration")

        # Check API status
        api_configured = check_api_configuration()
        if api_configured:
            st.success("✅ eLabFTW API Configured")
        else:
            st.error("❌ eLabFTW API Not Configured")
            st.info("Set environment variables:\n- ELABFTW_API_KEY\n- ELABFTW_URL")
            st.stop()

        st.divider()

        # Statistics
        if st.session_state.experiment_loaded:
            st.subheader("📊 Validation Status")
            st.metric("Errors", len(st.session_state.validation_errors))
            st.metric("Warnings", len(st.session_state.validation_warnings))
            st.metric("Missing Fields", len(st.session_state.missing_fields))

    # Step 1: Load Experiment
    st.markdown('<div class="section-header">Step 1: Load Experiment</div>', unsafe_allow_html=True)

    col1, col2 = st.columns([3, 1])

    with col1:
        experiment_id = st.number_input(
            "Enter eLabFTW Experiment ID",
            min_value=1,
            value=1,
            help="The ID of the experiment you want to validate (found in the URL)"
        )

    with col2:
        st.write("")  # Spacing
        st.write("")  # Spacing
        load_button = st.button("🔍 Load Experiment", type="primary", use_container_width=True)

    if load_button:
        with st.spinner(f"Loading experiment #{experiment_id}..."):
            success, result = load_experiment(experiment_id)

        if success:
            st.session_state.experiment_data = result
            st.session_state.experiment_loaded = True

            # Validate immediately
            errors, warnings, nwb_metadata, error_msg = validate_experiment(result)

            if error_msg:
                st.error(f"❌ Validation failed: {error_msg}")
            else:
                st.session_state.validation_errors = errors
                st.session_state.validation_warnings = warnings
                st.session_state.nwb_metadata = nwb_metadata
                st.session_state.missing_fields = [e.replace('Required field missing or empty: ', '') for e in errors]

            st.rerun()
        else:
            st.error(f"❌ Failed to load experiment: {result}")

    # Step 2: Display Experiment Info
    if st.session_state.experiment_loaded:
        st.markdown('<div class="section-header">Step 2: Experiment Information</div>', unsafe_allow_html=True)

        exp_data = st.session_state.experiment_data

        col3, col4 = st.columns(2)

        with col3:
            st.markdown(f"**Experiment ID:** {exp_data['id']}")
            st.markdown(f"**Title:** {exp_data['title']}")

        with col4:
            st.markdown(f"**Created:** {exp_data.get('created_at', 'N/A')}")
            st.markdown(f"**Modified:** {exp_data.get('modified_at', 'N/A')}")

        # Show metadata preview
        with st.expander("📄 View Raw Metadata", expanded=False):
            st.json(exp_data.get('metadata', {}))

    # Step 3: Validation Results
    if st.session_state.experiment_loaded:
        st.markdown('<div class="section-header">Step 3: Validation Results</div>', unsafe_allow_html=True)

        if not st.session_state.validation_errors and not st.session_state.validation_warnings:
            st.markdown('<div class="success-box">✅ <b>Perfect!</b> This experiment meets all ndx-fiber-photometry schema requirements.</div>', unsafe_allow_html=True)

            # Show NWB metadata preview
            with st.expander("🔬 View NWB Metadata Preview", expanded=False):
                st.json(st.session_state.nwb_metadata)

            st.info("This experiment is ready for NWB file generation!")

        else:
            # Show errors
            if st.session_state.validation_errors:
                st.markdown(f'<div class="error-box"><b>❌ {len(st.session_state.validation_errors)} Required Fields Missing</b></div>', unsafe_allow_html=True)

                st.markdown("**Missing Required Fields:**")
                for error in st.session_state.validation_errors:
                    field_name = error.replace('Required field missing or empty: ', '')
                    st.markdown(f"- <span class='field-missing'>{field_name}</span>", unsafe_allow_html=True)

            # Show warnings
            if st.session_state.validation_warnings:
                st.markdown(f'<div class="warning-box"><b>⚠️ {len(st.session_state.validation_warnings)} Warnings</b></div>', unsafe_allow_html=True)

                with st.expander("View Warnings", expanded=False):
                    for warning in st.session_state.validation_warnings:
                        st.warning(warning)

    # Step 4: Fill Missing Fields
    if st.session_state.experiment_loaded and st.session_state.validation_errors:
        st.markdown('<div class="section-header">Step 4: Fill Missing Fields</div>', unsafe_allow_html=True)

        st.info(f"Please provide values for the {len(st.session_state.missing_fields)} missing required fields below.")

        with st.form("missing_fields_form"):
            new_fields = {}
            metadata = st.session_state.experiment_data.get('metadata', {})

            for field_name in st.session_state.missing_fields:
                current_value = get_field_value_from_metadata(metadata, field_name)

                # Determine input type based on field name
                if 'Date' in field_name:
                    new_fields[field_name] = st.date_input(
                        f"{field_name} *",
                        help=f"Enter {field_name}"
                    )
                elif 'Time' in field_name:
                    new_fields[field_name] = st.time_input(
                        f"{field_name} *",
                        help=f"Enter {field_name}"
                    )
                elif any(x in field_name for x in ['(mm)', '(nm)', '(μm)', '(Hz)', '(nL)', '(mW)', 'Gain', 'Aperture', 'days']):
                    new_fields[field_name] = st.number_input(
                        f"{field_name} *",
                        value=0.0,
                        step=0.1,
                        help=f"Enter {field_name}"
                    )
                elif field_name == 'Sex':
                    new_fields[field_name] = st.selectbox(
                        "Sex *",
                        options=["M", "F", "U"],
                        help="M=Male, F=Female, U=Unknown"
                    )
                elif field_name == 'Species':
                    new_fields[field_name] = st.selectbox(
                        "Species *",
                        options=["Mus musculus", "Rattus norvegicus", "Other"],
                        help="Animal species"
                    )
                elif field_name == 'Indicator Label':
                    new_fields[field_name] = st.selectbox(
                        "Indicator Label *",
                        options=["GCaMP6f", "GCaMP6s", "GCaMP7s", "GCaMP8", "jRGECO1a", "jRCaMP1a", "tdTomato", "mCherry", "Other"],
                        help="Fluorescent indicator type"
                    )
                else:
                    new_fields[field_name] = st.text_input(
                        f"{field_name} *",
                        value=current_value,
                        help=f"Enter {field_name}"
                    )

            st.divider()
            submitted = st.form_submit_button("💾 Update Experiment", type="primary", use_container_width=True)

            if submitted:
                # Validate all fields are filled
                empty_fields = [k for k, v in new_fields.items() if v in [None, '', 0, 0.0]]

                if empty_fields:
                    st.error(f"❌ Please fill in all fields: {', '.join(empty_fields)}")
                else:
                    with st.spinner("Updating experiment..."):
                        success, result = update_experiment_metadata(
                            st.session_state.experiment_data['id'],
                            new_fields
                        )

                    if success:
                        st.success(f"✅ {result}")
                        st.balloons()
                        st.info("🔄 Reload the experiment to see updated validation status.")

                        # Clear loaded state to force reload
                        st.session_state.experiment_loaded = False
                        st.session_state.validation_errors = []
                        st.session_state.validation_warnings = []

                    else:
                        st.error(f"❌ Update failed: {result}")

    # Footer
    st.divider()
    st.markdown("""
    **Next Steps:**
    - ✅ Validate your experiment meets all requirements
    - 📝 Fill in any missing fields
    - 🔬 Generate NWB file using the parser script
    - 📤 Upload to DANDI archive
    """)


if __name__ == "__main__":
    main()
