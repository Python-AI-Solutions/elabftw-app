"""
User Journey C: Add NWB Template to Blank eLabFTW Entry

This app allows users to:
1. Connect to a blank eLabFTW experiment
2. Inject the full ndx-fiber-photometry compliant template
3. Preview the template structure
4. Apply the template to the experiment

Author: elabftw-app
Created: 2025-11-03
License: MIT
"""

import os
import json
import streamlit as st
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
    page_title="Add NWB Template - User Journey C",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #8e44ad;
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
    .info-box {
        padding: 1.5rem;
        background-color: #d1ecf1;
        border: 2px solid #bee5eb;
        border-radius: 8px;
        color: #0c5460;
        margin: 1rem 0;
    }
    .template-stats {
        display: flex;
        justify-content: space-around;
        padding: 1rem;
        background-color: #f8f9fa;
        border-radius: 8px;
        margin: 1rem 0;
    }
    .stat-box {
        text-align: center;
    }
    .stat-number {
        font-size: 2rem;
        font-weight: bold;
        color: #8e44ad;
    }
    .stat-label {
        font-size: 0.9rem;
        color: #7f8c8d;
    }
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """Initialize session state variables."""
    if 'experiment_loaded' not in st.session_state:
        st.session_state.experiment_loaded = False
    if 'experiment_data' not in st.session_state:
        st.session_state.experiment_data = None
    if 'template_data' not in st.session_state:
        st.session_state.template_data = None
    if 'template_applied' not in st.session_state:
        st.session_state.template_applied = False
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


def load_template():
    """Load the fiber photometry template from JSON file."""
    template_path = Path(__file__).parent.parent / 'templates' / 'fiber_photometry_template.json'

    try:
        with open(template_path, 'r') as f:
            template = json.load(f)
        return True, template
    except FileNotFoundError:
        return False, "Template file not found. Expected at: templates/fiber_photometry_template.json"
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON in template file: {e}"
    except Exception as e:
        return False, f"Error loading template: {e}"


def load_experiment(experiment_id):
    """Load experiment from eLabFTW."""
    experiments_api = create_elabftw_client()
    if not experiments_api:
        return False, "API client not configured"

    try:
        experiment = experiments_api.read_experiment(id=experiment_id)
        return True, {
            'id': experiment.id,
            'title': experiment.title,
            'body': experiment.body,
            'metadata': experiment.metadata,
            'created_at': experiment.created_at,
            'modified_at': experiment.modified_at
        }
    except ApiException as e:
        return False, f"API Error: {e}"
    except Exception as e:
        return False, f"Error: {e}"


def apply_template_to_experiment(experiment_id, template_data):
    """Apply template to experiment."""
    experiments_api = create_elabftw_client()
    if not experiments_api:
        return False, "API client not configured"

    try:
        # Patch experiment with template metadata
        result = experiments_api.patch_experiment(
            id=experiment_id,
            body={'metadata': template_data}
        )

        return True, "Template applied successfully"

    except ApiException as e:
        return False, f"API Error: {e}"
    except Exception as e:
        return False, f"Error: {e}"


def count_template_fields(template_data):
    """Count fields in template."""
    extra_fields = template_data.get('extra_fields', {})
    total_fields = len(extra_fields)
    required_fields = sum(1 for field in extra_fields.values() if field.get('required', False))
    optional_fields = total_fields - required_fields

    groups = template_data.get('elabftw', {}).get('extra_fields_groups', [])
    num_groups = len(groups)

    return {
        'total': total_fields,
        'required': required_fields,
        'optional': optional_fields,
        'groups': num_groups,
        'group_names': [g['name'] for g in groups]
    }


def main():
    """Main Streamlit application."""
    initialize_session_state()

    # Header
    st.markdown('<div class="main-header">📋 User Journey C: Add NWB Template</div>', unsafe_allow_html=True)

    st.markdown("""
    This tool helps you add the full **ndx-fiber-photometry** compliant template
    to a blank eLabFTW experiment entry. The template includes all 45 fields
    organized into 6 groups.
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

        # Load template
        if st.session_state.template_data is None:
            with st.spinner("Loading template..."):
                success, result = load_template()

            if success:
                st.session_state.template_data = result
                st.success("✅ Template Loaded")
            else:
                st.error(f"❌ {result}")
                st.stop()

        # Template stats
        if st.session_state.template_data:
            st.subheader("📊 Template Statistics")
            stats = count_template_fields(st.session_state.template_data)
            st.metric("Total Fields", stats['total'])
            st.metric("Required Fields", stats['required'])
            st.metric("Optional Fields", stats['optional'])
            st.metric("Field Groups", stats['groups'])

    # Step 1: Preview Template
    st.markdown('<div class="section-header">Step 1: Preview Template</div>', unsafe_allow_html=True)

    if st.session_state.template_data:
        stats = count_template_fields(st.session_state.template_data)

        # Display stats
        st.markdown(f"""
        <div class="template-stats">
            <div class="stat-box">
                <div class="stat-number">{stats['total']}</div>
                <div class="stat-label">Total Fields</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">{stats['required']}</div>
                <div class="stat-label">Required</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">{stats['optional']}</div>
                <div class="stat-label">Optional</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">{stats['groups']}</div>
                <div class="stat-label">Groups</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Display groups
        st.markdown("**Field Groups:**")
        for i, group_name in enumerate(stats['group_names'], 1):
            st.markdown(f"{i}. {group_name}")

        # Show template preview
        with st.expander("📄 View Full Template JSON", expanded=False):
            st.json(st.session_state.template_data)

    # Step 2: Load Experiment
    st.markdown('<div class="section-header">Step 2: Select Target Experiment</div>', unsafe_allow_html=True)

    st.info("💡 **Tip**: Create a new blank experiment in eLabFTW first, then enter its ID here.")

    col1, col2 = st.columns([3, 1])

    with col1:
        experiment_id = st.number_input(
            "Enter eLabFTW Experiment ID",
            min_value=1,
            value=1,
            help="The ID of the blank experiment where you want to add the template"
        )

    with col2:
        st.write("")  # Spacing
        st.write("")  # Spacing
        load_button = st.button("🔍 Load Experiment", type="secondary", use_container_width=True)

    if load_button:
        with st.spinner(f"Loading experiment #{experiment_id}..."):
            success, result = load_experiment(experiment_id)

        if success:
            st.session_state.experiment_data = result
            st.session_state.experiment_loaded = True
            st.rerun()
        else:
            st.error(f"❌ Failed to load experiment: {result}")

    # Step 3: Display Experiment Info
    if st.session_state.experiment_loaded:
        st.markdown('<div class="section-header">Step 3: Experiment Information</div>', unsafe_allow_html=True)

        exp_data = st.session_state.experiment_data

        col3, col4 = st.columns(2)

        with col3:
            st.markdown(f"**Experiment ID:** {exp_data['id']}")
            st.markdown(f"**Title:** {exp_data['title']}")

        with col4:
            st.markdown(f"**Created:** {exp_data.get('created_at', 'N/A')}")
            st.markdown(f"**Modified:** {exp_data.get('modified_at', 'N/A')}")

        # Check if experiment already has metadata
        current_metadata = exp_data.get('metadata', {})
        current_fields = current_metadata.get('extra_fields', {})

        if current_fields:
            st.markdown(f'<div class="info-box">ℹ️ <b>Note:</b> This experiment already has {len(current_fields)} fields. Applying the template will merge with existing fields.</div>', unsafe_allow_html=True)

            with st.expander("📄 View Current Metadata", expanded=False):
                st.json(current_metadata)
        else:
            st.markdown('<div class="success-box">✅ This experiment is blank and ready for the template!</div>', unsafe_allow_html=True)

    # Step 4: Apply Template
    if st.session_state.experiment_loaded and not st.session_state.template_applied:
        st.markdown('<div class="section-header">Step 4: Apply Template</div>', unsafe_allow_html=True)

        st.markdown("""
        Click the button below to apply the fiber photometry template to this experiment.
        This will add all 45 fields organized into 6 groups.
        """)

        col5, col6, col7 = st.columns([1, 2, 1])

        with col6:
            apply_button = st.button(
                "✨ Apply Template to Experiment",
                type="primary",
                use_container_width=True
            )

        if apply_button:
            with st.spinner("Applying template to experiment..."):
                success, result = apply_template_to_experiment(
                    st.session_state.experiment_data['id'],
                    st.session_state.template_data
                )

            if success:
                st.session_state.template_applied = True
                st.success(f"✅ {result}")
                st.balloons()

                # Reload experiment to show updated metadata
                with st.spinner("Reloading experiment..."):
                    success, result = load_experiment(st.session_state.experiment_data['id'])
                    if success:
                        st.session_state.experiment_data = result

                st.rerun()
            else:
                st.error(f"❌ Failed to apply template: {result}")

    # Step 5: Success
    if st.session_state.template_applied:
        st.markdown('<div class="section-header">🎉 Template Applied Successfully!</div>', unsafe_allow_html=True)

        st.markdown(f"""
        <div class="success-box">
        <b>✅ Success!</b> The fiber photometry template has been applied to experiment #{st.session_state.experiment_data['id']}.

        <br><br>

        <b>What's next?</b>
        <ul>
        <li>Open the experiment in eLabFTW to see all {count_template_fields(st.session_state.template_data)['total']} fields</li>
        <li>Fill in the required fields (marked with *)</li>
        <li>Add optional fields as needed</li>
        <li>Save your experiment</li>
        <li>Use the validation tool (User Journey A) to ensure all required fields are filled</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)

        # Link to experiment
        elabftw_url = os.environ.get('ELABFTW_URL', '')
        if elabftw_url:
            exp_url = f"{elabftw_url}/experiments.php?mode=view&id={st.session_state.experiment_data['id']}"
            st.markdown(f"**🔗 [Open Experiment in eLabFTW]({exp_url})**")

        # Show updated metadata
        with st.expander("📄 View Updated Metadata", expanded=True):
            st.json(st.session_state.experiment_data.get('metadata', {}))

        # Reset button
        if st.button("🔄 Apply Template to Another Experiment"):
            st.session_state.experiment_loaded = False
            st.session_state.template_applied = False
            st.session_state.experiment_data = None
            st.rerun()

    # Footer
    st.divider()
    st.markdown("""
    **About the Template:**
    - **45 fields** covering all ndx-fiber-photometry metadata requirements
    - **6 groups**: Subject Info, Surgery, Session, Device, Recording Channel, Notes
    - **18 required fields** (marked with *) for NWB compliance
    - **27 optional fields** for complete provenance tracking
    """)


if __name__ == "__main__":
    main()
