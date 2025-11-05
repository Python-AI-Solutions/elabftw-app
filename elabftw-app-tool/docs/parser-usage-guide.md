# eLabFTW Metadata Parser - Usage Guide

**Script**: `scripts/parse_elabftw_metadata.py`
**Purpose**: Extract and map fiber photometry metadata from eLabFTW to NWB format
**Last Updated**: 2025-11-03

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Usage Examples](#usage-examples)
5. [API Reference](#api-reference)
6. [Output Format](#output-format)
7. [Validation](#validation)
8. [Troubleshooting](#troubleshooting)

---

## Quick Start

### Prerequisites

```bash
# Install elabapi-python
pip install elabapi-python
```

### Basic Usage

```bash
# Set environment variables
export ELABFTW_API_KEY="your_api_key_here"
export ELABFTW_URL="https://your-elabftw.com"

# Parse experiment
python scripts/parse_elabftw_metadata.py 123
```

**Output:**
```
Fetching experiment 123 from https://your-elabftw.com...

✅ Validation passed!

Parsed metadata for experiment: FP Recording - M001 - 2024-01-15
Subject: M001
Session: session_20240115_M001
Indicator: GCaMP6f @ VTA

📄 Metadata saved to: experiment_123_nwb_metadata.json
```

---

## Installation

### Option 1: Using pip

```bash
pip install elabapi-python
```

### Option 2: Using pixi (project standard)

```bash
pixi add elabapi-python
```

### Verify Installation

```python
python -c "import elabapi_python; print(elabapi_python.__version__)"
```

Expected output: `5.3.0` (or later)

---

## Configuration

### Environment Variables

Create a `.env` file (NEVER commit this file!):

```bash
# eLabFTW Configuration
ELABFTW_API_KEY=your_api_key_here
ELABFTW_URL=https://your-elabftw.com
ELABFTW_VERIFY_SSL=true  # Set to false for self-signed certificates
```

### Getting Your API Key

1. Log into eLabFTW
2. Go to **User Panel** (top right) → **API Keys**
3. Click **"Generate API Key"**
4. Copy the key (shown only once!)
5. Save to `.env` file or export as environment variable

### Loading Environment Variables

**Option A: Manual export (Linux/Mac)**
```bash
export ELABFTW_API_KEY="your_key"
export ELABFTW_URL="https://your-elabftw.com"
```

**Option B: Manual export (Windows)**
```cmd
set ELABFTW_API_KEY=your_key
set ELABFTW_URL=https://your-elabftw.com
```

**Option C: Using python-dotenv**
```python
from dotenv import load_dotenv
load_dotenv()  # Loads from .env file
```

---

## Usage Examples

### Example 1: Command-Line Usage

```bash
# Parse single experiment
python scripts/parse_elabftw_metadata.py 123

# With custom SSL settings (self-signed cert)
export ELABFTW_VERIFY_SSL=false
python scripts/parse_elabftw_metadata.py 123
```

### Example 2: Python Script Usage

```python
import os
from scripts.parse_elabftw_metadata import ELabFTWMetadataParser

# Initialize parser
parser = ELabFTWMetadataParser(
    api_key=os.environ['ELABFTW_API_KEY'],
    elabftw_url=os.environ['ELABFTW_URL'],
    verify_ssl=True,
    debug=False
)

# Parse experiment
experiment_id = 123
nwb_metadata, errors, warnings = parser.parse_experiment(experiment_id)

# Check for errors
if errors:
    print("❌ Validation errors:")
    for error in errors:
        print(f"  - {error}")
    exit(1)

# Check for warnings
if warnings:
    print("⚠️  Warnings:")
    for warning in warnings:
        print(f"  - {warning}")

# Use metadata
print(f"Subject: {nwb_metadata['subject']['subject_id']}")
print(f"Session: {nwb_metadata['session']['session_id']}")
print(f"Indicator: {nwb_metadata['indicator']['label']}")
```

### Example 3: Batch Processing

```python
import os
import json
from scripts.parse_elabftw_metadata import ELabFTWMetadataParser

# Initialize parser
parser = ELabFTWMetadataParser(
    api_key=os.environ['ELABFTW_API_KEY'],
    elabftw_url=os.environ['ELABFTW_URL']
)

# List of experiment IDs to process
experiment_ids = [123, 124, 125, 126]

results = []
for exp_id in experiment_ids:
    try:
        nwb_metadata, errors, warnings = parser.parse_experiment(exp_id)

        if errors:
            print(f"❌ Experiment {exp_id}: {len(errors)} errors")
            continue

        if warnings:
            print(f"⚠️  Experiment {exp_id}: {len(warnings)} warnings")

        results.append(nwb_metadata)
        print(f"✅ Experiment {exp_id}: parsed successfully")

    except Exception as e:
        print(f"❌ Experiment {exp_id}: {e}")

# Save all results
with open('batch_results.json', 'w') as f:
    json.dump(results, f, indent=2, default=str)

print(f"\n✅ Processed {len(results)}/{len(experiment_ids)} experiments")
```

### Example 4: Direct Metadata Mapping (No API)

If you already have metadata JSON:

```python
from scripts.parse_elabftw_metadata import ELabFTWMetadataParser

# Create parser (API credentials not needed for mapping only)
parser = ELabFTWMetadataParser(
    api_key="mock",
    elabftw_url="https://mock.com"
)

# Load metadata from file
with open('experiment_metadata.json', 'r') as f:
    elabftw_metadata = json.load(f)

# Map to NWB format
nwb_metadata = parser.map_to_nwb_metadata(elabftw_metadata)

# Validate
errors = parser.validate_required_fields(elabftw_metadata)
warnings = parser.validate_data_ranges(elabftw_metadata)

print(f"Errors: {len(errors)}, Warnings: {len(warnings)}")
```

---

## API Reference

### Class: `ELabFTWMetadataParser`

#### Constructor

```python
parser = ELabFTWMetadataParser(
    api_key: str,
    elabftw_url: str,
    verify_ssl: bool = True,
    debug: bool = False
)
```

**Parameters:**
- `api_key`: eLabFTW API key (required)
- `elabftw_url`: Base URL of eLabFTW instance (required)
- `verify_ssl`: Verify SSL certificates (default: True)
- `debug`: Enable debug logging (default: False)

#### Methods

##### `get_experiment_metadata(experiment_id: int) -> Dict`

Fetch experiment data from eLabFTW API.

```python
experiment_data = parser.get_experiment_metadata(123)
print(experiment_data['title'])
print(experiment_data['metadata'])
```

**Returns:** Dictionary with experiment data

**Raises:** `ApiException` if API call fails

---

##### `validate_required_fields(metadata: Dict) -> List[str]`

Check that all required fields are present and non-empty.

```python
errors = parser.validate_required_fields(metadata)
if errors:
    for error in errors:
        print(f"Error: {error}")
```

**Returns:** List of error messages (empty if valid)

---

##### `validate_data_ranges(metadata: Dict) -> List[str]`

Check that numeric fields are within reasonable ranges.

```python
warnings = parser.validate_data_ranges(metadata)
if warnings:
    for warning in warnings:
        print(f"Warning: {warning}")
```

**Returns:** List of warning messages

**Validated ranges:**
- Stereotactic coordinates: -10 to 10 mm (AP, ML), 0 to 15 mm (DV, depth)
- Wavelengths: 300-800 nm (excitation), 400-900 nm (emission)
- Numerical aperture: 0.1 to 1.0

---

##### `map_to_nwb_metadata(metadata: Dict) -> Dict`

Map eLabFTW metadata to NWB format.

```python
nwb_metadata = parser.map_to_nwb_metadata(elabftw_metadata)
print(nwb_metadata['subject'])
print(nwb_metadata['indicator'])
print(nwb_metadata['session'])
```

**Returns:** Dictionary with NWB-formatted metadata

**Structure:**
```python
{
    'subject': {...},
    'indicator': {...},
    'viral_vector': {...},
    'fiber_insertion': {...},
    'session': {...},
    'optical_fiber': {...},
    'excitation_source': {...},
    'photodetector': {...},
    'dichroic_mirror': {...},  # or None
    'emission_filter': {...},  # or None
    'fiber_photometry_table': {...},
    'provenance': {...}
}
```

---

##### `parse_experiment(experiment_id: int, validate: bool = True) -> Tuple`

Complete parsing workflow: fetch, validate, and map.

```python
nwb_metadata, errors, warnings = parser.parse_experiment(123)

if errors:
    print("Cannot generate NWB file")
    for error in errors:
        print(f"  - {error}")
else:
    print("✅ Ready for NWB generation")
```

**Returns:** Tuple of `(nwb_metadata, errors, warnings)`
- `nwb_metadata`: Dictionary with NWB-formatted metadata
- `errors`: List of validation errors
- `warnings`: List of validation warnings

---

## Output Format

### Complete Output Structure

```json
{
  "subject": {
    "subject_id": "M001",
    "species": "Mus musculus",
    "sex": "M",
    "age": "P90D",
    "strain": "C57BL/6J",
    "genotype": "Th-Cre+/-",
    "weight": "25.3"
  },
  "indicator": {
    "name": "GCaMP6f_VTA",
    "label": "GCaMP6f",
    "injection_location": "VTA",
    "injection_coordinates_in_mm": [3.0, 2.0, 4.5],
    "description": "GCaMP6f injected in VTA"
  },
  "viral_vector": {
    "name": "AAV9-hSyn-GCaMP6f",
    "titer": "1e13 GC/mL",
    "injection_volume_nl": "500"
  },
  "fiber_insertion": {
    "depth_mm": "4.2",
    "location": "VTA"
  },
  "session": {
    "session_id": "session_20240115_M001",
    "session_start_time": "2024-01-15T14:30:00",
    "session_description": "Baseline recording",
    "experimenter": ["John Doe"],
    "lab": "Neuroscience Lab",
    "institution": "NIH NIMH"
  },
  "optical_fiber": {
    "name": "Fiber_400um",
    "model": "Doric MFC_400/430-0.48",
    "numerical_aperture": 0.39,
    "core_diameter_in_um": 400.0
  },
  "excitation_source": {
    "name": "LED_470nm",
    "excitation_wavelength_in_nm": 470.0,
    "power_mw": "5.0"
  },
  "photodetector": {
    "name": "PMT_520nm",
    "detected_wavelength_in_nm": 520.0,
    "gain": "1000"
  },
  "dichroic_mirror": {
    "name": "Dichroic_495nm",
    "cut_on_wavelength_in_nm": 495.0
  },
  "emission_filter": {
    "name": "Filter_525nm",
    "center_wavelength_in_nm": 525.0,
    "bandwidth_in_nm": "50"
  },
  "fiber_photometry_table": {
    "location": "VTA",
    "excitation_wavelength_in_nm": 470.0,
    "emission_wavelength_in_nm": 520.0,
    "channel_name": "GCaMP6f_470nm",
    "sampling_rate_hz": "1000"
  },
  "provenance": {
    "surgery_date": "2024-01-10",
    "protocol_name": "Standard FP Protocol v2",
    "data_file_path": "/data/photometry/M001/",
    "behavioral_task": "Freely moving",
    "drug_treatment": "",
    "notes": "Animal behaving normally",
    "analysis_status": "Pending",
    "quality_control": "Pass"
  },
  "elabftw": {
    "experiment_id": 123,
    "title": "FP Recording - M001 - 2024-01-15",
    "created_at": "2024-01-15T10:00:00",
    "modified_at": "2024-01-15T14:00:00"
  }
}
```

### Field Type Conversions

| eLabFTW Type | NWB Type | Example |
|--------------|----------|---------|
| text | string | "M001" |
| number | float | 470.0 |
| date | string | "2024-01-15" |
| time | string (part of timestamp) | "14:30" → "2024-01-15T14:30:00" |
| select | string | "M" |
| Age (days) | ISO 8601 duration | 90 → "P90D" |
| Coordinates (3 numbers) | tuple of floats | (3.0, 2.0, 4.5) |

---

## Validation

### Required Fields

The parser validates **18 required fields**:

**Subject** (3 fields):
- Subject ID
- Species
- Sex

**Surgery** (6 fields):
- Surgery Date
- Indicator Label
- Injection Location
- Injection AP (mm)
- Injection ML (mm)
- Injection DV (mm)

**Session** (5 fields):
- Session ID
- Session Date
- Session Time
- Experimenter

**Device** (4 fields):
- Fiber Core Diameter (μm)
- Fiber Numerical Aperture
- Excitation Wavelength (nm)
- Emission Wavelength (nm)
- Recording Location

### Range Validation

**Stereotactic Coordinates:**
- AP: -10 to 10 mm
- ML: -10 to 10 mm
- DV: 0 to 15 mm
- Fiber depth: 0 to 15 mm

**Wavelengths:**
- Excitation: 300 to 800 nm
- Emission: 400 to 900 nm
- Dichroic cut-on: 300 to 800 nm
- Filter center: 400 to 900 nm

**Numerical Aperture:**
- Range: 0.1 to 1.0

### Validation Examples

**Valid:**
```python
✅ All required fields present
✅ Injection AP = 3.0 mm (within -10 to 10)
✅ Excitation wavelength = 470 nm (within 300 to 800)
✅ Numerical aperture = 0.39 (within 0.1 to 1.0)
```

**Errors (will fail):**
```python
❌ Required field missing: Subject ID
❌ Required field missing or empty: Sex
```

**Warnings (will pass, but flagged):**
```python
⚠️  Injection AP (mm) value 15.0 outside typical range (-10 to 10 mm)
⚠️  Excitation Wavelength (nm) value 1000 outside typical range (300 to 800 nm)
⚠️  Fiber Numerical Aperture 1.5 outside typical range (0.1 to 1.0)
```

---

## Troubleshooting

### Problem: ApiException: Unauthorized (401)

**Cause:** Invalid or expired API key

**Solution:**
```bash
# Regenerate API key in eLabFTW
# Update environment variable
export ELABFTW_API_KEY="new_key_here"
```

---

### Problem: ApiException: Not Found (404)

**Cause:** Experiment ID doesn't exist or no access permission

**Solution:**
```python
# Check experiment ID in eLabFTW URL
# Verify you have read access to the experiment
# Try with a different experiment ID
```

---

### Problem: SSL Certificate Verification Failed

**Cause:** Self-signed certificate or local development instance

**Solution:**
```bash
# Disable SSL verification (use with caution!)
export ELABFTW_VERIFY_SSL=false
python scripts/parse_elabftw_metadata.py 123
```

---

### Problem: Required field missing errors

**Cause:** Experiment metadata incomplete

**Solution:**
1. Open experiment in eLabFTW web UI
2. Check which fields are empty
3. Fill in all fields marked with asterisk (*)
4. Save experiment
5. Re-run parser

---

### Problem: "list indices must be integers" error

**Cause:** Accessing wrong field structure

**Solution:**
```python
# Check metadata structure
print(json.dumps(metadata, indent=2))

# Ensure extra_fields exists
if 'extra_fields' in metadata:
    print("Metadata has extra_fields")
else:
    print("Metadata missing extra_fields - wrong template?")
```

---

### Problem: Output JSON has "None" values

**Cause:** Optional fields not filled in eLabFTW

**Solution:** This is expected behavior. Optional fields return `None` if not provided. You can filter these out:

```python
# Remove None values
def remove_none(d):
    return {k: v for k, v in d.items() if v is not None}

clean_metadata = {k: remove_none(v) if isinstance(v, dict) else v
                  for k, v in nwb_metadata.items()}
```

---

## Testing

### Run Test Suite

```bash
# Run all tests with mock data (no eLabFTW instance needed)
python scripts/test_parser.py
```

**Expected output:**
```
============================================================
eLabFTW Metadata Parser - Test Suite
============================================================

============================================================
Test 1: Field Extraction
============================================================
✅ Subject metadata: PASS
✅ Indicator metadata: PASS
✅ Session metadata: PASS
✅ Device metadata: PASS
✅ FiberPhotometryTable metadata: PASS

✅ ALL FIELD EXTRACTION TESTS PASSED

...

============================================================
🎉 ALL TESTS PASSED!
============================================================

The parser is ready to use with real eLabFTW data.
```

---

## Next Steps

After successfully parsing metadata:

1. **Generate NWB file**: Use `nwb_metadata` to populate ndx-fiber-photometry objects
2. **Validate NWB file**: Run `pynwb.validate()` on generated NWB file
3. **Upload to DANDI**: Use DANDI CLI/SDK with generated NWB file
4. **Log to ELN**: Update eLabFTW experiment with NWB file path and DANDI asset ID

---

## Related Documentation

- **Template Creation**: `docs/elabftw-template-creation-guide.md`
- **Research Document**: `docs/elabftw-ndx-photometry-research.md`
- **Template JSON**: `templates/fiber_photometry_template.json`
- **eLabFTW API Docs**: https://doc.elabftw.net/api/elabapi-html/
- **ndx-fiber-photometry**: https://github.com/catalystneuro/ndx-fiber-photometry

---

**Document Version**: 1.0
**Created**: 2025-11-03
**Author**: Claude (AI Assistant)
**Project**: elabftw-app
