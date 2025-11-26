"""
Behavior Session Data Entry Form

Dynamic form for recording behavior experiment sessions with support for:
- Session information
- Dynamic outcome columns (add/remove columns)
- Dynamic subject rows (add/remove mice)

Exports in eLabFTW-compatible JSON format for direct upload to notebooks.
Based on the Tejeda Lab behavior form (docs/behavior.html)
"""

import streamlit as st
import json
import pandas as pd
from datetime import date, time
from typing import Any

# Try to import elabapi_python for upload functionality
try:
    import elabapi_python
    from elabapi_python.rest import ApiException
    ELABAPI_AVAILABLE = True
except ImportError:
    ELABAPI_AVAILABLE = False

st.set_page_config(
    page_title="Behavior Session Entry",
    page_icon="🐭",
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
        background: linear-gradient(135deg, #ff9966 0%, #ff5e62 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 15px rgba(255, 94, 98, 0.3);
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

    /* Section cards */
    .section-card {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        border: 1px solid #e0e0e0;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
    }

    .section-header {
        display: flex;
        align-items: center;
        margin-bottom: 1rem;
        padding-bottom: 0.75rem;
        border-bottom: 2px solid #ff9966;
    }

    .section-header h3 {
        margin: 0;
        color: #333;
        font-weight: 600;
    }

    /* Subject card styling */
    .subject-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #e4e8ec 100%);
        border-radius: 10px;
        padding: 1.25rem;
        margin-bottom: 1rem;
        border-left: 4px solid #ff9966;
    }

    .subject-header {
        font-weight: 600;
        color: #ff5e62;
        font-size: 1.1rem;
        margin-bottom: 0.75rem;
    }

    /* Column tag styling */
    .column-tag {
        display: inline-flex;
        align-items: center;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 0.4rem 0.8rem;
        border-radius: 20px;
        margin: 0.25rem;
        font-size: 0.85rem;
        font-weight: 500;
        box-shadow: 0 2px 5px rgba(102, 126, 234, 0.3);
    }

    .column-tag-remove {
        margin-left: 0.5rem;
        cursor: pointer;
        opacity: 0.8;
    }

    .column-tag-remove:hover {
        opacity: 1;
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
        background: linear-gradient(135deg, #ff9966 0%, #ff5e62 100%);
        border: none;
    }

    /* Add/Remove button styling */
    .add-btn {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%) !important;
        color: white !important;
        border: none !important;
    }

    .remove-btn {
        background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%) !important;
        color: white !important;
        border: none !important;
    }

    /* Input field styling */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > div {
        border-radius: 8px;
        border: 1px solid #ddd;
        transition: all 0.2s ease;
    }

    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #ff9966;
        box-shadow: 0 0 0 2px rgba(255, 153, 102, 0.2);
    }

    /* Metric styling */
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        color: white;
    }

    .metric-value {
        font-size: 2rem;
        font-weight: bold;
    }

    .metric-label {
        font-size: 0.9rem;
        opacity: 0.9;
    }

    /* Upload section styling */
    .upload-section {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 1.5rem;
        border-radius: 12px;
        margin-top: 1rem;
    }

    /* Sidebar styling */
    .css-1d391kg {
        background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%);
    }

    /* Expander styling */
    .streamlit-expanderHeader {
        background: linear-gradient(135deg, #f5f7fa 0%, #e4e8ec 100%);
        border-radius: 8px;
        font-weight: 600;
    }

    /* Success/Error message styling */
    .stSuccess {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        color: white;
        border-radius: 8px;
    }

    .stError {
        background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%);
        color: white;
        border-radius: 8px;
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

# Default outcome columns from the original form
DEFAULT_COLUMNS = [
    "Weight",
    "Reward Consumed",
    "Shock Intensity",
    "Box #",
    "Novel Object Side",
    "Sucrose Side"
]

# Initialize session state
if "num_behavior_subjects" not in st.session_state:
    st.session_state.num_behavior_subjects = 1

if "outcome_columns" not in st.session_state:
    st.session_state.outcome_columns = DEFAULT_COLUMNS.copy()


def generate_elabftw_metadata() -> dict[str, Any]:
    """Generate eLabFTW-compatible metadata JSON from form data."""
    extra_fields = {}
    extra_fields_groups = []
    position = 1
    group_id = 1

    # Group 1: Session Info
    extra_fields_groups.append({"id": group_id, "name": "Session Info"})

    extra_fields["Date"] = {
        "type": "date",
        "value": st.session_state.get("session_date", ""),
        "required": True,
        "position": position,
        "group_id": group_id
    }
    position += 1

    extra_fields["Start Time"] = {
        "type": "time",
        "value": st.session_state.get("start_time", ""),
        "position": position,
        "group_id": group_id
    }
    position += 1

    extra_fields["Personnel"] = {
        "type": "text",
        "value": st.session_state.get("personnel", ""),
        "position": position,
        "group_id": group_id
    }
    position += 1

    extra_fields["Behavior Room"] = {
        "type": "select",
        "value": st.session_state.get("behavior_room", ""),
        "options": ["2D-717", "2D-715", "RBC BD825", "RBC BD836", "2D-711"],
        "position": position,
        "group_id": group_id
    }
    position += 1

    extra_fields["Experiment"] = {
        "type": "text",
        "value": st.session_state.get("experiment", ""),
        "position": position,
        "group_id": group_id
    }
    position += 1

    extra_fields["Subjects Summary"] = {
        "type": "text",
        "value": st.session_state.get("subjects_summary", ""),
        "position": position,
        "group_id": group_id
    }
    position += 1

    extra_fields["Manipulation"] = {
        "type": "text",
        "value": st.session_state.get("manipulation", ""),
        "position": position,
        "group_id": group_id
    }
    position += 1

    extra_fields["Video File Path"] = {
        "type": "text",
        "value": st.session_state.get("video_file_path", ""),
        "position": position,
        "group_id": group_id
    }
    position += 1

    extra_fields["AnyMaze Protocol"] = {
        "type": "text",
        "value": st.session_state.get("anymaze_protocol", ""),
        "position": position,
        "group_id": group_id
    }
    position += 1

    extra_fields["Cue Information"] = {
        "type": "text",
        "value": st.session_state.get("cue_info", ""),
        "position": position,
        "group_id": group_id
    }
    position += 1

    extra_fields["Reward Information"] = {
        "type": "text",
        "value": st.session_state.get("reward_info", ""),
        "position": position,
        "group_id": group_id
    }
    position += 1
    group_id += 1

    # Dynamic subject groups with outcome columns
    for i in range(st.session_state.num_behavior_subjects):
        extra_fields_groups.append({"id": group_id, "name": f"Subject {i+1}"})
        prefix = f"beh_subj_{i}_"

        extra_fields[f"Subject {i+1} ID"] = {
            "type": "text",
            "value": st.session_state.get(f"{prefix}id", ""),
            "position": position,
            "group_id": group_id
        }
        position += 1

        # Add each outcome column as a field
        for col_name in st.session_state.outcome_columns:
            field_name = f"Subject {i+1} {col_name}"
            extra_fields[field_name] = {
                "type": "text",
                "value": st.session_state.get(f"{prefix}{col_name.lower().replace(' ', '_').replace('#', '')}", ""),
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
    extra_fields_groups.append({"id": group_id, "name": "Session Notes"})
    extra_fields["Session Notes"] = {
        "type": "text",
        "value": st.session_state.get("session_notes", ""),
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


def upload_to_elabftw(
    metadata: dict,
    title: str,
    elabftw_url: str,
    api_key: str,
    verify_ssl: bool = False
) -> tuple[bool, str, int | None]:
    """
    Upload metadata to eLabFTW as a new experiment.

    Args:
        metadata: The eLabFTW-compatible metadata dict
        title: Title for the experiment
        elabftw_url: Base URL of eLabFTW instance (e.g., https://localhost:3148)
        api_key: API key for authentication
        verify_ssl: Whether to verify SSL certificates

    Returns:
        Tuple of (success, message, experiment_id or None)
    """
    if not ELABAPI_AVAILABLE:
        return False, "elabapi-python not installed. Run: pip install elabapi-python", None

    try:
        # Configure API client
        configuration = elabapi_python.Configuration()
        configuration.host = f"{elabftw_url}/api/v2"
        configuration.verify_ssl = verify_ssl

        api_client = elabapi_python.ApiClient(configuration)
        api_client.set_default_header(header_name='Authorization', header_value=api_key)

        # Create API instances
        exp_client = elabapi_python.ExperimentsApi(api_client)
        info_client = elabapi_python.InfoApi(api_client)

        # Test connection
        info_client.get_info()

        # Create new experiment
        response = exp_client.post_experiment_with_http_info()
        location_header = response[2].get('Location')

        if not location_header:
            return False, "Failed to get experiment ID from response", None

        experiment_id = int(location_header.split('/').pop())

        # Update experiment with title and metadata
        patch_body = {
            'title': title,
            'metadata': json.dumps(metadata)
        }
        exp_client.patch_experiment(experiment_id, body=patch_body)

        return True, f"Successfully created experiment (ID: {experiment_id})", experiment_id

    except ApiException as e:
        return False, f"API Error: {e.reason} - {e.body}", None
    except Exception as e:
        return False, f"Error: {str(e)}", None


# Page Header with gradient styling
st.markdown("""
<div class="main-header">
    <h1>🐭 Behavior Session Data Entry</h1>
    <p>Record behavior experiment sessions with dynamic tables. Add subjects and customize outcome columns as needed.</p>
</div>
""", unsafe_allow_html=True)

# ============== Session Information ==============
st.markdown('<div class="section-header"><h3>📋 Session Information</h3></div>', unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    session_date = st.date_input("Date *", value=date.today(), key="session_date_input")
    st.session_state.session_date = str(session_date)

    start_time = st.time_input("Start Time", value=time(9, 0), key="start_time_input")
    st.session_state.start_time = str(start_time)

    st.text_input("Personnel Running Task", key="personnel")

with col2:
    st.selectbox(
        "Behavior Room",
        options=["2D-717", "2D-715", "RBC BD825", "RBC BD836", "2D-711"],
        key="behavior_room"
    )
    st.text_input("Experiment", key="experiment")
    st.text_input("Manipulation", key="manipulation")

with col3:
    st.text_input("Video File Path", key="video_file_path")
    st.text_input("AnyMaze Protocol", key="anymaze_protocol")
    st.text_input("Cue Information", key="cue_info")

col4, col5 = st.columns(2)
with col4:
    st.text_input("Reward Information", key="reward_info")
with col5:
    st.text_area("Subjects (summary)", key="subjects_summary", height=68)

st.divider()

# ============== Outcome Columns Management ==============
st.markdown('<div class="section-header"><h3>📊 Outcome Columns</h3></div>', unsafe_allow_html=True)
st.markdown("Customize the columns for your behavior outcomes table.")

col_add, col_input, col_spacer = st.columns([1, 2, 3])

with col_input:
    new_col_name = st.text_input("New column name", key="new_column_name", label_visibility="collapsed", placeholder="Enter new column name...")

with col_add:
    if st.button("➕ Add Column", use_container_width=True):
        if new_col_name and new_col_name.strip() and new_col_name.strip() not in st.session_state.outcome_columns:
            st.session_state.outcome_columns.append(new_col_name.strip())
            st.rerun()

# Display current columns as styled tags
st.markdown("**Current columns:**")

# Build column tags HTML
tags_html = '<div style="display: flex; flex-wrap: wrap; gap: 0.5rem; margin: 1rem 0;">'
for col_name in st.session_state.outcome_columns:
    tags_html += f'<span class="column-tag">{col_name}</span>'
tags_html += '</div>'
st.markdown(tags_html, unsafe_allow_html=True)

# Column removal buttons in a compact row
st.markdown("**Remove columns:**")
cols_per_row = 6
col_chunks = [st.session_state.outcome_columns[i:i+cols_per_row] for i in range(0, len(st.session_state.outcome_columns), cols_per_row)]

for chunk in col_chunks:
    cols = st.columns(cols_per_row)
    for idx, col_name in enumerate(chunk):
        with cols[idx]:
            if len(st.session_state.outcome_columns) > 1:
                if st.button(f"❌ {col_name[:8]}...", key=f"del_col_{col_name}", help=f"Remove {col_name}", use_container_width=True):
                    st.session_state.outcome_columns.remove(col_name)
                    st.rerun()

# Reset columns button
if st.button("🔄 Reset to Default Columns"):
    st.session_state.outcome_columns = DEFAULT_COLUMNS.copy()
    st.rerun()

st.divider()

# ============== Subjects Table ==============
st.markdown('<div class="section-header"><h3>🐭 Subject Outcomes</h3></div>', unsafe_allow_html=True)

col_add, col_remove, col_spacer = st.columns([1, 1, 4])
with col_add:
    if st.button("➕ Add Subject", use_container_width=True, key="add_subject_btn"):
        st.session_state.num_behavior_subjects += 1
        st.rerun()
with col_remove:
    if st.session_state.num_behavior_subjects > 1:
        if st.button("➖ Remove Subject", use_container_width=True, key="remove_subject_btn"):
            st.session_state.num_behavior_subjects -= 1
            st.rerun()

# Create subject entries
for i in range(st.session_state.num_behavior_subjects):
    with st.expander(f"**Subject {i + 1}**", expanded=True):
        prefix = f"beh_subj_{i}_"

        # First row: Mouse ID
        st.text_input("Mouse ID", key=f"{prefix}id", placeholder=f"Mouse {i+1}")

        # Create columns for outcomes
        num_cols = len(st.session_state.outcome_columns)
        cols_per_row = min(4, num_cols)

        for row_start in range(0, num_cols, cols_per_row):
            row_cols = st.session_state.outcome_columns[row_start:row_start + cols_per_row]
            cols = st.columns(len(row_cols))

            for col_idx, col_name in enumerate(row_cols):
                with cols[col_idx]:
                    field_key = f"{prefix}{col_name.lower().replace(' ', '_').replace('#', '')}"
                    st.text_input(col_name, key=field_key)

        # Notes at the end
        st.text_input("Notes", key=f"{prefix}notes")

st.divider()

# ============== Session Notes ==============
st.markdown('<div class="section-header"><h3>📝 Session Notes</h3></div>', unsafe_allow_html=True)
st.text_area("Additional notes about this session", key="session_notes", height=100)

st.divider()

# ============== Export ==============
st.markdown('<div class="section-header"><h3>💾 Export Data</h3></div>', unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("📋 Generate eLabFTW JSON", type="primary", use_container_width=True):
        metadata = generate_elabftw_metadata()
        st.session_state.generated_behavior_metadata = metadata
        st.success("✅ eLabFTW metadata generated!")

with col2:
    if "generated_behavior_metadata" in st.session_state:
        json_str = json.dumps(st.session_state.generated_behavior_metadata, indent=2)
        st.download_button(
            label="⬇️ Download JSON",
            data=json_str,
            file_name="behavior_metadata.json",
            mime="application/json",
            use_container_width=True
        )

with col3:
    # Export as CSV table
    if st.button("📊 Export as CSV", use_container_width=True):
        # Build table data
        table_data = []
        for i in range(st.session_state.num_behavior_subjects):
            prefix = f"beh_subj_{i}_"
            row = {"Mouse ID": st.session_state.get(f"{prefix}id", "")}
            for col_name in st.session_state.outcome_columns:
                field_key = f"{prefix}{col_name.lower().replace(' ', '_').replace('#', '')}"
                row[col_name] = st.session_state.get(field_key, "")
            row["Notes"] = st.session_state.get(f"{prefix}notes", "")
            table_data.append(row)

        if table_data:
            df = pd.DataFrame(table_data)
            st.session_state.behavior_csv = df.to_csv(index=False)
            st.success("✅ CSV generated!")

with col4:
    if "behavior_csv" in st.session_state:
        st.download_button(
            label="⬇️ Download CSV",
            data=st.session_state.behavior_csv,
            file_name="behavior_outcomes.csv",
            mime="text/csv",
            use_container_width=True
        )

# Stats with styled metric cards
col_stat1, col_stat2, col_stat3 = st.columns(3)
with col_stat1:
    total_fields = len(st.session_state.get("generated_behavior_metadata", {}).get("extra_fields", {}))
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{total_fields}</div>
        <div class="metric-label">Total Fields</div>
    </div>
    """, unsafe_allow_html=True)
with col_stat2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{st.session_state.num_behavior_subjects}</div>
        <div class="metric-label">Total Subjects</div>
    </div>
    """, unsafe_allow_html=True)
with col_stat3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{len(st.session_state.outcome_columns)}</div>
        <div class="metric-label">Outcome Columns</div>
    </div>
    """, unsafe_allow_html=True)

# Show preview
if "generated_behavior_metadata" in st.session_state:
    with st.expander("📄 Preview eLabFTW JSON", expanded=False):
        st.json(st.session_state.generated_behavior_metadata)

st.divider()

# ============== Upload to eLabFTW ==============
st.markdown('<div class="section-header"><h3>☁️ Upload to eLabFTW</h3></div>', unsafe_allow_html=True)

if not ELABAPI_AVAILABLE:
    st.warning("elabapi-python is not installed. Install it with: `pip install elabapi-python`")
else:
    st.markdown("Upload this behavior session directly to your eLabFTW instance.")

    col_url, col_key = st.columns(2)
    with col_url:
        elabftw_url = st.text_input(
            "eLabFTW URL",
            value="https://localhost:3148",
            key="elabftw_url",
            help="Base URL of your eLabFTW instance"
        )
    with col_key:
        api_key = st.text_input(
            "API Key",
            type="password",
            key="api_key",
            help="Your eLabFTW API key (User Panel -> API Keys)"
        )

    experiment_title = st.text_input(
        "Experiment Title",
        value=f"Behavior Session - {st.session_state.get('session_date', date.today())}",
        key="experiment_title",
        help="Title for the new experiment entry"
    )

    verify_ssl = st.checkbox("Verify SSL Certificate", value=False, key="verify_ssl")

    col_upload, col_status = st.columns([1, 3])

    with col_upload:
        if st.button("🚀 Upload to eLabFTW", type="primary", use_container_width=True):
            if not api_key:
                st.error("Please enter your API key")
            elif not elabftw_url:
                st.error("Please enter the eLabFTW URL")
            elif not experiment_title:
                st.error("Please enter an experiment title")
            else:
                # Generate metadata if not already done
                metadata = generate_elabftw_metadata()

                with st.spinner("Uploading to eLabFTW..."):
                    success, message, exp_id = upload_to_elabftw(
                        metadata=metadata,
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

st.divider()

# Sidebar with styled summary
st.sidebar.markdown("""
<div style="background: linear-gradient(135deg, #ff9966 0%, #ff5e62 100%); padding: 1rem; border-radius: 10px; margin-bottom: 1rem;">
    <h3 style="color: white; margin: 0;">📊 Form Summary</h3>
</div>
""", unsafe_allow_html=True)

# Summary metrics
st.sidebar.markdown(f"""
<div style="background: #f8f9fa; padding: 1rem; border-radius: 8px; margin-bottom: 0.5rem;">
    <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
        <span>🐭 Subjects</span>
        <strong>{st.session_state.num_behavior_subjects}</strong>
    </div>
    <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
        <span>📊 Columns</span>
        <strong>{len(st.session_state.outcome_columns)}</strong>
    </div>
    <div style="display: flex; justify-content: space-between;">
        <span>📋 Total Cells</span>
        <strong>{st.session_state.num_behavior_subjects * len(st.session_state.outcome_columns)}</strong>
    </div>
</div>
""", unsafe_allow_html=True)

st.sidebar.divider()

st.sidebar.markdown("### 📋 Current Columns")
# Display columns as mini tags
cols_html = '<div style="display: flex; flex-wrap: wrap; gap: 0.3rem;">'
for col in st.session_state.outcome_columns:
    cols_html += f'<span style="background: #667eea; color: white; padding: 0.2rem 0.5rem; border-radius: 12px; font-size: 0.75rem;">{col}</span>'
cols_html += '</div>'
st.sidebar.markdown(cols_html, unsafe_allow_html=True)

st.sidebar.divider()

st.sidebar.markdown("### 💡 Tips")
st.sidebar.markdown("""
<div style="background: #e3f2fd; padding: 0.75rem; border-radius: 8px; font-size: 0.85rem;">
• <strong>+ Add Subject</strong> for more mice<br>
• <strong>+ Add Column</strong> for custom outcomes<br>
• <strong>❌</strong> to remove columns<br>
• <strong>Generate JSON</strong> for eLabFTW<br>
• <strong>Export CSV</strong> for spreadsheets
</div>
""", unsafe_allow_html=True)

st.sidebar.divider()

# Reset button with styling
if st.sidebar.button("🔄 Reset Form", use_container_width=True, type="secondary"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()
