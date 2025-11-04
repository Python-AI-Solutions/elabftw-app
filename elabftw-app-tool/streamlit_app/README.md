# Fiber Photometry Metadata Entry - Streamlit App

A user-friendly web interface for entering fiber photometry experiment metadata and submitting it to eLabFTW.

## Features

✅ **Organized Form** - 45 fields organized into 6 logical groups
✅ **Required Field Validation** - Real-time validation of 18 required fields
✅ **Smart Defaults** - Pre-filled common values (species, wavelengths, etc.)
✅ **Help Text** - Tooltips on every field
✅ **Import/Export** - Save/load metadata as JSON
✅ **eLabFTW Integration** - Direct submission to eLabFTW via API
✅ **Responsive Design** - Works on desktop and tablet

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
streamlit run Metadata_Entry.py
```

The app will open in your browser at `http://localhost:8501`

### Fill Out the Form

1. **Subject Information** (7 fields) - Animal details
2. **Surgery & Injection** (10 fields) - Surgical procedure details
3. **Session Information** (7 fields) - Recording session metadata
4. **Device Configuration** (10 fields) - Hardware specs
5. **Recording Channel** (3 fields) - Channel details
6. **Notes & Provenance** (8 fields) - Additional tracking

### Submit

Click **"✅ Submit to eLabFTW"** at the bottom of the form.

Required fields are marked with **\***. The form will validate before submission.

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
├── Metadata_Entry.py       # Main Streamlit app
├── README.md               # This file
└── requirements.txt        # Python dependencies
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
streamlit run Metadata_Entry.py --server.runOnSave true
```

### Testing Locally (No API)

The app works without eLabFTW API configured:
- Fill in form
- Click Submit
- Metadata saved to JSON instead

### Adding New Fields

1. Add input widget in appropriate group
2. Add field to `metadata` dictionary in submit handler
3. Add field to `convert_to_elabftw_metadata()` function
4. Update validation if required field

## License

MIT

## Author

elabftw-app team

## Version

1.0.0 (2025-11-03)
