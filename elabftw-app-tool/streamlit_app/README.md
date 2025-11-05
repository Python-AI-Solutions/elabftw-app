# Fiber Photometry Metadata Tool - Streamlit App Suite

A comprehensive web interface for managing fiber photometry experiment metadata in eLabFTW with three distinct user journeys.

## Overview

This tool suite provides **three user journeys** for different workflows:

### 🔍 Journey A: Validate & Fix Existing Entry
**Use when**: You have an existing eLabFTW entry with some metadata
- Load experiment by ID
- Validate against ndx-fiber-photometry schema
- Identify missing required fields
- Fill missing fields via smart form
- Update experiment with validated metadata

### 📝 Journey B: Create New Entry from Form
**Use when**: You have experiment data and want to enter it fresh
- Comprehensive form with 45 fields in 6 groups
- Real-time validation of 18 required fields
- Smart defaults and dropdowns
- Import/export JSON for data portability
- Submit directly to eLabFTW or save locally

### 📋 Journey C: Add Template to Blank Entry
**Use when**: You have a blank eLabFTW entry and want the full template structure
- Preview template (45 fields, 6 groups, 18 required)
- Enter blank experiment ID
- One-click template injection
- Full NWB-compliant structure instantly added

## Common Features

✅ **NWB Compliance** - Full ndx-fiber-photometry extension support
✅ **Validation** - 18 required fields + data range checks
✅ **Smart Inputs** - Date pickers, number validation, dropdowns
✅ **eLabFTW Integration** - Direct API access via elabapi-python
✅ **Session State** - Progress saved during form filling
✅ **Error Handling** - Clear messages and guided fixes

## Installation

```bash
# Install dependencies
pip install streamlit elabapi-python

# Or using pixi (project standard)
pixi add streamlit elabapi-python
```

## Configuration

### Set Environment Variables

```bash
# Required for eLabFTW submission
export ELABFTW_API_KEY="your_api_key_here"
export ELABFTW_URL="https://your-elabftw.com"

# Optional
export ELABFTW_VERIFY_SSL="true"  # Set to false for self-signed certs
```

### Get eLabFTW API Key

1. Log into eLabFTW
2. Go to **User Panel** → **API Keys**
3. Click **"Generate API Key"**
4. Copy and save to environment variable

## Usage

### Run the App

```bash
# Run from streamlit_app directory
streamlit run Home.py
```

The app will open in your browser at `http://localhost:8501`

### Choose Your Journey

The **Home page** presents all three user journeys. Select the one that matches your workflow:

**Journey A** (`pages/A_Validate_Existing.py`):
1. Enter existing experiment ID
2. Review validation results
3. Fill missing required fields
4. Update experiment

**Journey B** (`pages/Metadata_Entry.py`):
1. Fill comprehensive form (45 fields in 6 groups)
2. Export/import JSON if needed
3. Submit to eLabFTW or save locally
4. View created experiment

**Journey C** (`pages/C_Add_Template.py`):
1. Preview template structure
2. Enter blank experiment ID
3. Click to apply template
4. Access updated experiment in eLabFTW

Required fields are marked with **\*** in all journeys.

## Features in Detail

### Sidebar Features

**Configuration Status**
- Shows if eLabFTW API is configured
- Displays connection status

**Template Settings**
- Option to use existing eLabFTW template
- Enter template ID if available

**Import/Export**
- **Load from JSON**: Upload previously saved metadata
- **Save to JSON**: Download current form data

### Form Features

**Smart Input Types**
- Text inputs for IDs, names, descriptions
- Number inputs with min/max validation
- Date/time pickers for temporal data
- Dropdowns for predefined options (sex, indicator, behavioral task)
- Text areas for notes

**Validation**
- Required fields checked before submission
- Number ranges validated (coordinates, wavelengths, NA)
- Clear error messages for missing fields

**Auto-Save**
- Metadata saved to session state
- Can save to JSON file for later use
- Can load from JSON to pre-fill form

### Submission Workflow

1. Fill in all required fields (marked with *)
2. Optionally fill additional fields
3. Click "Submit to eLabFTW"
4. App validates required fields
5. App converts to eLabFTW metadata format
6. App creates experiment in eLabFTW
7. Success message with experiment ID

If API not configured, metadata is saved locally as JSON.

## Output

### eLabFTW Experiment

The app creates an experiment with:

**Title**: `FP Recording - {Subject ID} - {Date}`

**Body**: Summary of key metadata

**Metadata**: All 45 fields in `extra_fields` format

### JSON Export

```json
{
  "subject_id": "M001",
  "species": "Mus musculus",
  "sex": "M",
  "age_days": 90,
  ...
}
```

## Troubleshooting

### "eLabFTW API Not Configured"

**Solution**: Set environment variables before running:
```bash
export ELABFTW_API_KEY="your_key"
export ELABFTW_URL="https://your-elabftw.com"
```

### "elabapi-python not installed"

**Solution**:
```bash
pip install elabapi-python
```

### "Submission failed: API Error"

**Causes**:
- Invalid API key
- No access to eLabFTW
- Network issue
- Template ID doesn't exist

**Solution**: Check API key, URL, and network connection

### Required Fields Error

**Cause**: Not all required fields filled

**Solution**: Look for fields marked with * and fill them in

## File Structure

```
streamlit_app/
├── Home.py                          # Main landing page with journey selection
├── pages/
│   ├── A_Validate_Existing.py       # Journey A: Validate & fix existing entries
│   ├── Metadata_Entry.py            # Journey B: Create new entry from form
│   └── C_Add_Template.py            # Journey C: Add template to blank entry
├── README.md                        # This file
└── requirements.txt                 # Python dependencies
```

## Related Documentation

- **Template JSON**: `../templates/fiber_photometry_template.json`
- **Parser Script**: `../scripts/parse_elabftw_metadata.py`
- **Template Guide**: `../docs/elabftw-template-creation-guide.md`
- **Parser Guide**: `../docs/parser-usage-guide.md`

## Screenshots

*(Add screenshots here after testing)*

## Development

### Running in Development Mode

```bash
streamlit run Home.py --server.runOnSave true
```

### Testing Locally (No API)

All journeys work without eLabFTW API configured:
- **Journey A**: Will show error when trying to load experiment
- **Journey B**: Can fill form and export to JSON (submission disabled)
- **Journey C**: Will show error when trying to load/apply template

### Testing Each Journey

**Journey A Testing:**
1. Configure API credentials
2. Create test experiment in eLabFTW with partial metadata
3. Load in Journey A
4. Verify validation errors shown correctly
5. Fill missing fields and verify update

**Journey B Testing:**
1. Fill form with test data
2. Export to JSON and verify format
3. Re-import JSON and verify pre-population
4. Submit to eLabFTW (if configured) or save locally

**Journey C Testing:**
1. Create blank experiment in eLabFTW
2. Load in Journey C
3. Verify template preview shows correct stats
4. Apply template
5. Verify experiment in eLabFTW has all 45 fields

### Adding New Fields

If extending the template with additional fields:

1. Update `../templates/fiber_photometry_template.json`
2. Update field in all three journey apps:
   - **Journey A**: Add to validation logic
   - **Journey B**: Add input widget in appropriate group
   - **Journey C**: Template auto-updates from JSON
3. Update `../scripts/parse_elabftw_metadata.py` validation
4. Update required field count if applicable

## License

MIT

## Author

elabftw-app team

## Version

1.0.0 (2025-11-04)

## Changelog

### v1.0.0 (2025-11-04)
- Initial release with three user journeys
- Journey A: Validate & fix existing entries
- Journey B: Create new entries from form
- Journey C: Add template to blank entries
- Full ndx-fiber-photometry compliance (45 fields, 6 groups)
- Home page navigation with journey selection
