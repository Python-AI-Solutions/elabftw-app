# eLabFTW Fiber Photometry Template - Creation Guide

**Purpose**: Step-by-step guide to create and use the fiber photometry experiment template in eLabFTW
**Template File**: `templates/fiber_photometry_template.json`
**Last Updated**: 2025-11-03

---

## Table of Contents

1. [Overview](#overview)
2. [Template Structure](#template-structure)
3. [Method 1: Web UI Creation](#method-1-web-ui-creation)
4. [Method 2: API Creation](#method-2-api-creation)
5. [Method 3: Import from File](#method-3-import-from-file)
6. [Using the Template](#using-the-template)
7. [Field Reference](#field-reference)
8. [Troubleshooting](#troubleshooting)

---

## Overview

This template creates a structured metadata form for fiber photometry experiments with **45 fields** organized into **6 groups**:

| Group | Fields | Purpose |
|-------|--------|---------|
| **Subject Information** | 7 fields | Animal metadata (ID, species, sex, age, strain, genotype, weight) |
| **Surgery & Injection** | 10 fields | Surgical procedure details (dates, coordinates, viral vectors, fiber implant) |
| **Session Information** | 7 fields | Recording session metadata (date, time, experimenter, institution) |
| **Device Configuration** | 10 fields | Hardware specifications (fiber, LED, PMT, filters, wavelengths) |
| **Recording Channel** | 3 fields | Channel-specific metadata (location, name, sampling rate) |
| **Notes & Provenance** | 7 fields | Additional tracking (protocol, files, behavioral task, QC status) |

**Total**: 45 fields (18 required, 27 optional)

---

## Template Structure

The template JSON has two main sections:

```json
{
  "extra_fields": {
    // All 45 custom fields defined here
  },
  "elabftw": {
    // Configuration: groups and display settings
  }
}
```

### Field Anatomy

Each field follows this structure:

```json
"Field Name": {
  "type": "text",           // Field type (text, number, date, select, etc.)
  "value": "",              // Default value
  "required": true,         // Whether field is mandatory (true/false)
  "position": 1,            // Display order (lower numbers appear first)
  "group_id": 1,            // Which group this field belongs to
  "description": "Help text" // Tooltip shown below field
}
```

### Field Types Used

| Type | Count | Example Fields |
|------|-------|----------------|
| `text` | 20 | Subject ID, Injection Location, Experimenter |
| `number` | 17 | Age (days), Injection AP (mm), Excitation Wavelength (nm) |
| `date` | 2 | Surgery Date, Session Date |
| `time` | 1 | Session Time |
| `select` | 5 | Species, Sex, Indicator Label, Behavioral Task, Analysis Status |

---

## Method 1: Web UI Creation (Recommended for First Time)

### Step 1: Access Template Manager

1. Log into your eLabFTW instance
2. Click **"Admin Panel"** (top right menu)
3. Navigate to **"Experiments Templates"** or **"Templates"** section
4. Click **"Create new template"** button

### Step 2: Create Basic Template

1. **Title**: Enter "Fiber Photometry Experiment Template"
2. **Body** (optional): Enter description:
   ```
   Use this template for all fiber photometry recording sessions.

   This template collects metadata required for NWB file generation
   and DANDI archive uploads.
   ```
3. Click **"Save"**

### Step 3: Add Metadata

1. In the newly created template, find the **"Metadata"** section
2. Click **"Edit metadata"** or the **JSON icon**
3. **Delete any existing JSON** in the editor
4. **Copy the entire contents** of `templates/fiber_photometry_template.json`
5. **Paste** into the metadata editor
6. Click **"Save metadata"**

### Step 4: Verify Template

1. The form should now display 6 expandable groups:
   - Subject Information (7 fields)
   - Surgery & Injection (10 fields)
   - Session Information (7 fields)
   - Device Configuration (10 fields)
   - Recording Channel (3 fields)
   - Notes & Provenance (7 fields)

2. Check that:
   - ✅ Required fields show asterisk (*)
   - ✅ Dropdown fields show options
   - ✅ Number fields accept only numbers
   - ✅ Date/time pickers appear for date/time fields
   - ✅ Help text appears below fields

### Step 5: Set Template as Default (Optional)

1. Go to **Admin Panel** → **Team Settings**
2. Under **"Default experiment template"**
3. Select "Fiber Photometry Experiment Template"
4. Save settings

---

## Method 2: API Creation (Programmatic)

### Prerequisites

```bash
pip install elabapi-python
```

### Step 1: Get API Key

1. Log into eLabFTW
2. Go to **User Panel** → **API Keys**
3. Click **"Generate API Key"**
4. Copy the key (shown only once!)

### Step 2: Python Script

```python
import json
import elabapi_python
from elabapi_python.rest import ApiException

# Configure API client
configuration = elabapi_python.Configuration()
configuration.api_key['api_key'] = 'YOUR_API_KEY_HERE'  # Replace with your key
configuration.api_key_prefix['api_key'] = 'Authorization'
configuration.host = 'https://your-elabftw.com/api/v2'  # Replace with your eLabFTW URL
configuration.debug = False
configuration.verify_ssl = True

# Create API client
api_client = elabapi_python.ApiClient(configuration)
templates_api = elabapi_python.ExperimentsTemplatesApi(api_client)

# Load template JSON from file
with open('templates/fiber_photometry_template.json', 'r') as f:
    template_metadata = json.load(f)

# Create template
template_body = {
    "title": "Fiber Photometry Experiment Template",
    "body": "Use this template for all fiber photometry recording sessions.\n\nThis template collects metadata required for NWB file generation and DANDI archive uploads.",
    "metadata": template_metadata
}

try:
    new_template = templates_api.post_experiments_template(body=template_body)
    print(f"✅ Template created successfully!")
    print(f"   Template ID: {new_template.id}")
    print(f"   URL: https://your-elabftw.com/experiments.php?mode=view&id={new_template.id}")
except ApiException as e:
    print(f"❌ Error creating template: {e}")
```

### Step 3: Run Script

```bash
python create_template.py
```

Expected output:
```
✅ Template created successfully!
   Template ID: 5
   URL: https://your-elabftw.com/experiments.php?mode=view&id=5
```

---

## Method 3: Import from File

### Option A: Direct JSON Import (if supported)

1. In eLabFTW, go to template metadata editor
2. Look for **"Import JSON"** button or file upload option
3. Select `templates/fiber_photometry_template.json`
4. Confirm import

### Option B: Copy-Paste (Universal)

1. Open `templates/fiber_photometry_template.json` in a text editor
2. **Select all** (Ctrl+A / Cmd+A)
3. **Copy** (Ctrl+C / Cmd+C)
4. In eLabFTW template metadata editor, **delete existing content**
5. **Paste** (Ctrl+V / Cmd+V)
6. **Save**

---

## Using the Template

### Creating a New Experiment from Template

#### Via Web UI

1. Go to **"Experiments"** tab
2. Click **"Create experiment"**
3. Select **"Fiber Photometry Experiment Template"** from dropdown
4. Click **"Create"**
5. Fill in the metadata form (required fields marked with *)
6. Click **"Save"**

#### Via API

```python
experiments_api = elabapi_python.ExperimentsApi(api_client)

# Create experiment from template
experiment_body = {
    "template_id": 5,  # Use your template ID
    "title": "FP Recording - M001 - 2024-01-15"
}

try:
    experiment = experiments_api.post_experiment(body=experiment_body)
    print(f"Experiment created: {experiment.id}")

    # Now update metadata values
    metadata_update = {
        "extra_fields": {
            "Subject ID": {"value": "M001"},
            "Species": {"value": "Mus musculus"},
            "Sex": {"value": "M"},
            # ... etc
        }
    }

    experiment = experiments_api.patch_experiment(
        id=experiment.id,
        body={"metadata": metadata_update}
    )
    print("Metadata updated!")

except ApiException as e:
    print(f"Error: {e}")
```

### Filling Out the Form

**Tips for efficient data entry:**

1. **Group by group**: Work through one group at a time (Subject → Surgery → Session → Device → Channel → Notes)
2. **Required fields first**: Fields with asterisk (*) must be filled
3. **Use autocomplete**: For repeated values (experimenter name, institution), the form may remember previous entries
4. **Copy from previous**: Duplicate a previous experiment and update only changed values
5. **Save frequently**: Click Save to avoid losing data

---

## Field Reference

### Group 1: Subject Information (7 fields, 3 required)

| Field Name | Type | Required | Example Value | Notes |
|------------|------|----------|---------------|-------|
| Subject ID | text | ✅ Yes | M001 | Unique identifier |
| Species | select | ✅ Yes | Mus musculus | Dropdown: Mus musculus, Rattus norvegicus, Other |
| Sex | select | ✅ Yes | M | Dropdown: M, F, U (Unknown) |
| Age (days) | number | No | 90 | Age at session time |
| Strain | text | No | C57BL/6J | Genetic strain |
| Genotype | text | No | Th-Cre+/- | Genetic modifications |
| Weight (grams) | number | No | 25.3 | Body weight |

### Group 2: Surgery & Injection (10 fields, 6 required)

| Field Name | Type | Required | Example Value | Notes |
|------------|------|----------|---------------|-------|
| Surgery Date | date | ✅ Yes | 2024-01-10 | Date of surgery |
| Indicator Label | select | ✅ Yes | GCaMP6f | Dropdown: GCaMP6f, GCaMP7s, jRGECO1a, etc. |
| Injection Location | text | ✅ Yes | VTA | Brain region |
| Injection AP (mm) | number | ✅ Yes | 3.0 | Anterior-posterior coordinate |
| Injection ML (mm) | number | ✅ Yes | 2.0 | Medial-lateral coordinate |
| Injection DV (mm) | number | ✅ Yes | 4.5 | Dorsal-ventral coordinate |
| Viral Vector Name | text | No | AAV9-hSyn-GCaMP6f | Full construct name |
| Viral Titer | text | No | 1e13 GC/mL | Titer value with units |
| Injection Volume (nL) | number | No | 500 | Volume in nanoliters |
| Fiber Implant Depth (mm) | number | No | 4.2 | Fiber tip depth |

### Group 3: Session Information (7 fields, 5 required)

| Field Name | Type | Required | Example Value | Notes |
|------------|------|----------|---------------|-------|
| Session ID | text | ✅ Yes | session_20240115_M001 | Unique session ID |
| Session Date | date | ✅ Yes | 2024-01-15 | Recording date |
| Session Time | time | ✅ Yes | 14:30 | Recording start time |
| Session Description | text | No | Baseline recording | Brief description |
| Experimenter | text | ✅ Yes | John Doe | Name(s) |
| Laboratory | text | No | Neuroscience Lab | Lab name |
| Institution | text | No | NIH NIMH | Default: NIH NIMH |

### Group 4: Device Configuration (10 fields, 4 required)

| Field Name | Type | Required | Example Value | Notes |
|------------|------|----------|---------------|-------|
| Optical Fiber Model | text | No | Doric MFC_400/430-0.48 | Manufacturer model |
| Fiber Core Diameter (μm) | number | ✅ Yes | 400 | Default: 400 |
| Fiber Numerical Aperture | number | ✅ Yes | 0.39 | Default: 0.39 |
| Excitation Wavelength (nm) | number | ✅ Yes | 470 | Default: 470 |
| Emission Wavelength (nm) | number | ✅ Yes | 520 | Default: 520 |
| Dichroic Mirror Cut-on (nm) | number | No | 495 | Optional filter |
| Emission Filter Center (nm) | number | No | 525 | Optional filter |
| Emission Filter Bandwidth (nm) | number | No | 50 | Optional filter |
| LED Power (mW) | number | No | 5.0 | Power setting |
| PMT Gain | number | No | 1000 | Gain setting |

### Group 5: Recording Channel (3 fields, 1 required)

| Field Name | Type | Required | Example Value | Notes |
|------------|------|----------|---------------|-------|
| Recording Location | text | ✅ Yes | VTA | Brain region |
| Channel Name | text | No | GCaMP6f_470nm | Descriptive name |
| Sampling Rate (Hz) | number | No | 1000 | Acquisition rate |

### Group 6: Notes & Provenance (7 fields, 0 required)

| Field Name | Type | Required | Example Value | Notes |
|------------|------|----------|---------------|-------|
| Protocol Name | text | No | Standard FP Protocol v2 | SOP identifier |
| Data File Path | text | No | /data/photometry/M001/ | File location |
| Behavioral Task | select | No | Freely moving | Dropdown: 7 options |
| Drug Treatment | text | No | Saline, 1 mL, IP, -30 min | Drug details |
| Notes | text | No | Animal behaving normally | Observations |
| Analysis Status | select | No | Pending | Default: Pending |
| Quality Control | select | No | Pass | Dropdown: Pass/Fail/Needs Review |

---

## Validation and Error Checking

### Required Field Validation

eLabFTW will enforce required fields:
- Form shows asterisk (*) for required fields
- Cannot save with required fields empty
- API will return error if required fields missing

### Data Type Validation

- **Number fields**: Only accept numeric input
- **Date fields**: Date picker ensures valid dates
- **Time fields**: Time picker ensures valid format
- **Select fields**: Only allow predefined options

### Custom Validation (in parser script)

The parser script should validate:
```python
def validate_metadata(metadata):
    """Validate eLabFTW metadata before NWB conversion."""
    errors = []
    fields = metadata.get('extra_fields', {})

    # Check required fields
    required = ['Subject ID', 'Sex', 'Species', 'Surgery Date',
                'Indicator Label', 'Injection Location', 'Injection AP (mm)',
                'Injection ML (mm)', 'Injection DV (mm)', 'Session ID',
                'Session Date', 'Session Time', 'Experimenter',
                'Fiber Core Diameter (μm)', 'Fiber Numerical Aperture',
                'Excitation Wavelength (nm)', 'Emission Wavelength (nm)',
                'Recording Location']

    for field in required:
        if field not in fields or not fields[field].get('value'):
            errors.append(f"Required field missing: {field}")

    # Validate coordinate values
    if 'Injection AP (mm)' in fields:
        ap = float(fields['Injection AP (mm)'].get('value', 0))
        if ap < -10 or ap > 10:
            errors.append("Injection AP coordinate out of range (-10 to 10 mm)")

    # Validate wavelengths
    if 'Excitation Wavelength (nm)' in fields:
        ex_wl = float(fields['Excitation Wavelength (nm)'].get('value', 0))
        if ex_wl < 300 or ex_wl > 800:
            errors.append("Excitation wavelength out of range (300-800 nm)")

    return errors
```

---

## Troubleshooting

### Problem: Template not appearing in dropdown

**Solution**:
1. Ensure template is saved successfully
2. Check template category matches experiment category
3. Verify you have permissions to access template
4. Refresh browser page
5. Check template is not archived

### Problem: Metadata JSON not saving

**Solution**:
1. Validate JSON syntax (use JSONLint.com)
2. Ensure all quotes are double quotes (`"` not `'`)
3. Check for trailing commas (not allowed in JSON)
4. Verify bracket matching (`{}` and `[]`)
5. Try pasting in smaller sections

### Problem: Required fields not enforcing

**Solution**:
1. Check `"required": true` (not `"required": "true"` as string)
2. Ensure field has `"required": true` at same level as `"type"`
3. eLabFTW version must support required field enforcement
4. Test by trying to save empty required field

### Problem: Groups not displaying

**Solution**:
1. Verify `elabftw.extra_fields_groups` array has all group IDs referenced
2. Check `group_id` values in fields match group IDs in array
3. Ensure group IDs are integers (1, 2, 3) not strings ("1", "2", "3")
4. eLabFTW version must support field grouping

### Problem: Select dropdowns showing raw values

**Solution**:
1. Check `"options"` is an array: `["Option1", "Option2"]`
2. Ensure options use double quotes
3. Try simpler options first to test (e.g., `["A", "B"]`)

### Problem: API creation failing

**Solution**:
1. Verify API key is correct and active
2. Check API key has template creation permissions
3. Ensure URL includes `/api/v2` endpoint
4. Check eLabFTW version supports API v2
5. Try with `configuration.debug = True` to see full error

---

## Next Steps

After creating the template:

1. **Test with sample data**: Create a test experiment and fill all fields
2. **Export filled template**: Download as JSON to verify structure
3. **Create parser script**: Move to Task 1.3 (write elabapi-python parser)
4. **Validate NWB mapping**: Ensure all NWB required fields can be populated
5. **Document for users**: Create user guide for lab members

---

## Additional Resources

- **eLabFTW Metadata Docs**: https://doc.elabftw.net/metadata.html
- **eLabFTW API Docs**: https://doc.elabftw.net/api/elabapi-html/
- **Template File**: `templates/fiber_photometry_template.json`
- **Research Document**: `docs/elabftw-ndx-photometry-research.md`
- **elabapi-python Examples**: https://github.com/elabftw/elabapi-python/tree/master/examples

---

**Document Version**: 1.0
**Created**: 2025-11-03
**Author**: Claude (AI Assistant)
**Project**: elabftw-app
**Task**: Task 1.2 - Create fiber photometry experiment template
