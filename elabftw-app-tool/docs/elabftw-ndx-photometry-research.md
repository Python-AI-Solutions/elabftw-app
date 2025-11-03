# eLabFTW Template Structure & ndx-fiber-photometry Field Mapping Research

**Research Date**: 2025-11-03
**Duration**: 3 hours (Task 1.1)
**Purpose**: Understand eLabFTW metadata template structure and map to ndx-fiber-photometry NWB extension requirements

---

## Executive Summary

This document provides comprehensive research on:
1. **eLabFTW metadata template structure** - JSON-based custom field system with 10+ field types
2. **ndx-fiber-photometry NWB extension** - 11 neurodata types for storing fiber photometry experimental metadata
3. **elabapi-python library** - Python REST API client (v5.3.0) for programmatic eLabFTW interaction
4. **Field mapping strategy** - How to map fiber photometry experimental metadata from eLabFTW to NWB format

---

## 1. eLabFTW Metadata Template Structure

### 1.1 Overview

eLabFTW (version 4.0.0+) supports custom metadata attachment to experiments, items, and templates via a JSON-based field system. This enables researchers to define structured data collection forms.

### 1.2 JSON Structure

The metadata JSON follows a specific two-section format:

```json
{
  "extra_fields": {
    "Field Name": {
      "type": "text",
      "value": "some value",
      "description": "Help text shown below field",
      "required": true,
      "position": 1,
      "group_id": 1
    }
  },
  "elabftw": {
    "display_main_text": false,
    "extra_fields_groups": [
      {
        "id": 1,
        "name": "Group Name"
      }
    ]
  }
}
```

**Key sections:**
- `extra_fields` - Contains all custom field definitions (field name as object key)
- `elabftw` - Configuration object for groups and display settings

### 1.3 Available Field Types

eLabFTW supports 10 input types:

| Type | Description | Use Case |
|------|-------------|----------|
| `text` | Short text input (default) | Names, IDs, labels |
| `number` | Numeric-only input | Measurements, counts |
| `date` | Date picker | Experiment dates, surgery dates |
| `datetime-local` | Combined date and time | Precise timestamps |
| `time` | Time picker | Duration, time of day |
| `email` | Validated email input | Contact information |
| `url` | Validated URL with clickable link | References, data links |
| `checkbox` | Boolean selection box | Yes/No flags |
| `select` | Dropdown menu | Predefined options |
| `radio` | Visible option selection | Small option sets |

### 1.4 Field Properties

**Required attribute:**
- `value` - Stores the field's input or selected value

**Optional attributes:**
- `type` - Specifies input type (defaults to text)
- `description` - Help text displayed beneath field name
- `required` - Boolean indicating mandatory field (true/false)
- `position` - Numeric ordering (lowest displays first)
- `blank_value_on_duplicate` - Clears value when entity duplicates
- `group_id` - Associates field with defined group
- `options` - Array of choices for select/radio types (e.g., `["Option 1", "Option 2"]`)
- `allow_multi_values` - Enables multiple selection in dropdowns (boolean)
- `units` - Array of unit options for numeric fields (e.g., `["mg/mL", "μg/mL"]`)
- `unit` - Stores selected unit value

### 1.5 Grouping and Organization

Fields can be organized into groups using the `elabftw.extra_fields_groups` array:

```json
"elabftw": {
  "extra_fields_groups": [
    {"id": 1, "name": "Subject Information"},
    {"id": 2, "name": "Surgery Details"},
    {"id": 3, "name": "Device Configuration"}
  ]
}
```

Then assign fields to groups via `group_id`:

```json
"Subject ID": {
  "type": "text",
  "value": "",
  "required": true,
  "group_id": 1,
  "position": 1
}
```

### 1.6 Best Practices

1. **Use templates** - Most useful place to define extra fields so new entries have required inputs
2. **Set position values** - Control display order (lowest position displays first)
3. **Mark required fields** - Use `"required": true` for mandatory inputs
4. **Group related fields** - Organize by subject, surgery, session, device, etc.
5. **Provide descriptions** - Add help text for complex fields
6. **Use appropriate types** - Match field type to data (date for dates, number for numeric values)

---

## 2. ndx-fiber-photometry NWB Extension

### 2.1 Overview

`ndx-fiber-photometry` is the current NWB extension for storing fiber photometry recordings and experimental metadata, replacing the deprecated `ndx-photometry` extension. It is developed by CatalystNeuro.

**Installation:**
```bash
pip install ndx-fiber-photometry
```

**Key Dependencies:**
- `pynwb` - NWB file I/O
- `ndx-ophys-devices` - Device specification models

### 2.2 Main Neurodata Types

The extension provides 11+ neurodata types organized into categories:

#### Core Container Types

1. **FiberPhotometry** (extends LabMetaData)
   - Top-level metadata container organizing all experiment information
   - Holds the FiberPhotometryTable

2. **FiberPhotometryTable** (DynamicTable)
   - Documents experimental setup for each fiber channel
   - Each row represents one recording channel

3. **FiberPhotometryResponseSeries** (TimeSeries)
   - Stores recorded fluorescence signals

4. **CommandedVoltageSeries** (TimeSeries)
   - Voltage commands controlling excitation sources

#### Device Models (from ndx-ophys-devices)

Uses **model-instance pattern** where specifications define hardware types and instances represent actual equipment:

5. **ExcitationSource / ExcitationSourceModel**
   - Light sources (LEDs, lasers)
   - Fields: `excitation_wavelength_in_nm`, power specifications, wavelength ranges

6. **OpticalFiber / OpticalFiberModel**
   - Fiber specifications
   - Fields: `numerical_aperture`, `core_diameter_in_um`, ferrule details

7. **Photodetector / PhotodetectorModel**
   - Detection hardware (PMTs, photodiodes)
   - Fields: `detected_wavelength_in_nm`, gain, wavelength sensitivity

8. **DichroicMirror / DichroicMirrorModel**
   - Optical mirrors
   - Fields: `cut_on_wavelength_in_nm`, reflection/transmission bands

9. **BandOpticalFilter / BandOpticalFilterModel**
   - Bandpass/bandstop filters
   - Fields: `center_wavelength_in_nm`, bandwidth

10. **EdgeOpticalFilter / EdgeOpticalFilterModel**
    - Longpass/shortpass filters
    - Fields: cut wavelengths

#### Biological Components

11. **Indicator**
    - Fluorescent reporters (GCaMP6f, tdTomato, etc.)
    - Fields: `label`, `injection_location`, `injection_coordinates_in_mm`

12. **ViralVector**
    - Construct specifications
    - Fields: `name`, `titer`, `manufacturer`

13. **ViralVectorInjection**
    - Injection procedures with stereotactic coordinates

14. **FiberInsertion**
    - Implantation details
    - Fields: depth, position, angles

### 2.3 Required Metadata Fields

#### FiberPhotometryTable (per recording channel)

Each row documents a single recording channel and requires:

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `location` | string | Brain region | "VTA" |
| `excitation_wavelength_in_nm` | float | Excitation light wavelength | 470.0 |
| `emission_wavelength_in_nm` | float | Detected emission wavelength | 520.0 |
| `indicator` | reference | Link to Indicator object | GCaMP6f instance |
| `optical_fiber` | reference | Link to OpticalFiber object | Fiber instance |
| `excitation_source` | reference | Link to ExcitationSource | LED instance |
| `photodetector` | reference | Link to Photodetector | PMT instance |
| `dichroic_mirror` | reference (optional) | Link to DichroicMirror | Mirror instance |
| `emission_filter` | reference (optional) | Link to optical filter | Filter instance |
| `commanded_voltage_series` | reference | Link to CommandedVoltageSeries | Voltage timeseries |

#### Indicator (Fluorescent Reporter)

| Field | Required | Type | Description | Example |
|-------|----------|------|-------------|---------|
| `name` | Yes | string | Indicator name | "GCaMP6f_VTA" |
| `label` | No | string | Indicator type | "GCaMP6f" |
| `injection_location` | No | string | Brain region | "VTA" |
| `injection_coordinates_in_mm` | No | tuple | Stereotactic coords (AP, ML, DV) | (3.0, 2.0, 1.0) |
| `description` | No | string | Additional details | "AAV9-GCaMP6f injection" |

#### OpticalFiber

| Field | Required | Type | Description | Example |
|-------|----------|------|-------------|---------|
| `name` | Yes | string | Fiber identifier | "Fiber_400um_NA039" |
| `model` | No | string | Manufacturer model | "Doric MFC_400/430-0.48" |
| `numerical_aperture` | No | float | NA value | 0.39 |
| `core_diameter_in_um` | No | float | Core diameter | 400.0 |

#### ExcitationSource

| Field | Required | Type | Description | Example |
|-------|----------|------|-------------|---------|
| `excitation_wavelength_in_nm` | Yes | float | Wavelength | 470.0 |
| `name` | Yes | string | Source identifier | "LED_470nm" |

#### Photodetector

| Field | Required | Type | Description | Example |
|-------|----------|------|-------------|---------|
| `detected_wavelength_in_nm` | Yes | float | Detection wavelength | 520.0 |
| `name` | Yes | string | Detector identifier | "PMT_520nm" |

#### NWB Core Metadata (Subject, Session)

Standard NWB file metadata also required:

**Subject Information:**
- `subject_id` - Unique identifier
- `species` - e.g., "Mus musculus"
- `sex` - "M", "F", or "U"
- `age` - ISO 8601 duration (e.g., "P90D" for 90 days)
- `strain` - Genetic strain (optional)
- `genotype` - Genetic modifications (optional)
- `weight` - In grams (optional)

**Session Information:**
- `session_id` - Unique session identifier
- `session_start_time` - ISO 8601 timestamp
- `session_description` - Brief description
- `experimenter` - List of experimenters
- `lab` - Laboratory name
- `institution` - Institution name

---

## 3. elabapi-python Library

### 3.1 Overview

`elabapi-python` is the official Python client library for eLabFTW REST API v2.

**Current Version**: 5.3.0 (released October 20, 2025)
**Repository**: https://github.com/elabftw/elabapi-python
**Documentation**: https://doc.elabftw.net/api/elabapi-html/

### 3.2 Installation

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate

# Install library
pip install elabapi-python
```

### 3.3 Basic Usage Pattern

```python
import elabapi_python
from elabapi_python.rest import ApiException

# 1. Configure API client
configuration = elabapi_python.Configuration()
configuration.api_key['api_key'] = 'YOUR_API_KEY'
configuration.api_key_prefix['api_key'] = 'Authorization'
configuration.host = 'https://your-elabftw-instance.com/api/v2'
configuration.debug = False
configuration.verify_ssl = True

# 2. Create API client
api_client = elabapi_python.ApiClient(configuration)

# 3. Instantiate API objects
experiments_api = elabapi_python.ExperimentsApi(api_client)
items_api = elabapi_python.ItemsApi(api_client)
info_api = elabapi_python.InfoApi(api_client)

# 4. Make API calls
try:
    experiment = experiments_api.read_experiment(experiment_id=123)
    print(experiment.metadata)
except ApiException as e:
    print(f"Exception: {e}")
```

### 3.4 Available Example Scripts

The repository includes 27+ example scripts:

**Metadata & Template Work:**
- `00-getting-started.py` - Recommended starting point
- `001-manipulating-metadata.py` - Manipulating metadata
- `002-extra-field-to-column.py` - Converting extra fields to columns
- `08-create-items-add-metadata.py` - Item creation with metadata
- `09-import-csv.py` - CSV import with metadata
- `15-process-csv-metadata-into-csv-column.py` - Processing CSV metadata
- `17-csv-metadata-as-columns.py` - Managing CSV metadata as columns

**Other Operations:**
- File uploads/downloads
- User management
- Team creation
- Resource management
- Event tracking

### 3.5 Working with Metadata via API

Based on example `09-import-csv.py`, metadata is handled as JSON with `extra_fields`:

```python
# Example metadata structure
metadata = {
    "extra_fields": {
        "URL": {
            "type": "url",
            "value": "https://example.com"
        },
        "Concentration": {
            "type": "number",
            "value": "50",
            "units": ["mg/mL", "μg/mL"],
            "unit": "mg/mL"
        },
        "Status": {
            "type": "select",
            "value": "In Progress",
            "options": ["Planned", "In Progress", "Complete"]
        },
        "Tags": {
            "type": "select",
            "value": ["Tag1", "Tag2"],
            "options": ["Tag1", "Tag2", "Tag3"],
            "allow_multi_values": True
        }
    }
}

# Create experiment with metadata
experiment = experiments_api.post_experiment(
    body={
        "title": "My Experiment",
        "metadata": metadata
    }
)
```

### 3.6 Template Operations

Templates can be created, read, updated via the API:

```python
# Create experiment from template
experiment = experiments_api.post_experiment(
    body={
        "template_id": 5,  # Use template ID
        "title": "Fiber Photometry Session 2024-01-15"
    }
)

# Read template metadata structure
template_api = elabapi_python.ExperimentsTemplatesApi(api_client)
template = template_api.read_experiments_template(template_id=5)
print(template.metadata)  # Shows extra_fields structure
```

---

## 4. Field Mapping Strategy: eLabFTW → ndx-fiber-photometry

### 4.1 Mapping Overview

The mapping strategy organizes eLabFTW template fields into **6 logical groups** that correspond to NWB metadata requirements:

1. **Subject Information** (NWB Subject object)
2. **Surgery & Injection Details** (Indicator, ViralVector, FiberInsertion)
3. **Session Information** (NWB Session metadata)
4. **Device Configuration** (OpticalFiber, ExcitationSource, Photodetector, filters)
5. **Recording Channel** (FiberPhotometryTable row)
6. **Provenance & Notes** (Additional metadata)

### 4.2 Detailed Field Mapping

#### Group 1: Subject Information

| eLabFTW Field Name | Type | Required | Maps to NWB | Example Value |
|-------------------|------|----------|-------------|---------------|
| Subject ID | text | Yes | `Subject.subject_id` | "M001" |
| Species | select | Yes | `Subject.species` | "Mus musculus" |
| Sex | select | Yes | `Subject.sex` | "M" / "F" / "U" |
| Age (days) | number | No | `Subject.age` | "90" → "P90D" |
| Strain | text | No | `Subject.strain` | "C57BL/6J" |
| Genotype | text | No | `Subject.genotype` | "Th-Cre+/-" |
| Weight (grams) | number | No | `Subject.weight` | "25.3" |

**eLabFTW Options for Sex:**
```json
"Sex": {
  "type": "select",
  "options": ["M", "F", "U"],
  "required": true
}
```

#### Group 2: Surgery & Injection Details

| eLabFTW Field Name | Type | Required | Maps to NWB | Example Value |
|-------------------|------|----------|-------------|---------------|
| Surgery Date | date | Yes | `ViralVectorInjection` metadata | "2024-01-10" |
| Indicator Label | select | Yes | `Indicator.label` | "GCaMP6f" |
| Injection Location | text | Yes | `Indicator.injection_location` | "VTA" |
| Injection AP (mm) | number | Yes | `Indicator.injection_coordinates_in_mm[0]` | "3.0" |
| Injection ML (mm) | number | Yes | `Indicator.injection_coordinates_in_mm[1]` | "2.0" |
| Injection DV (mm) | number | Yes | `Indicator.injection_coordinates_in_mm[2]` | "4.5" |
| Viral Vector Name | text | No | `ViralVector.name` | "AAV9-GCaMP6f" |
| Viral Titer | text | No | `ViralVector.titer` | "1e13 GC/mL" |
| Fiber Implant Depth (mm) | number | No | `FiberInsertion.depth` | "4.2" |

**eLabFTW Options for Indicator:**
```json
"Indicator Label": {
  "type": "select",
  "options": ["GCaMP6f", "GCaMP7s", "jRGECO1a", "tdTomato"],
  "required": true
}
```

#### Group 3: Session Information

| eLabFTW Field Name | Type | Required | Maps to NWB | Example Value |
|-------------------|------|----------|-------------|---------------|
| Session ID | text | Yes | `session_id` | "session_20240115_001" |
| Session Date | date | Yes | `session_start_time` (date part) | "2024-01-15" |
| Session Time | time | Yes | `session_start_time` (time part) | "14:30" |
| Session Description | text | No | `session_description` | "Baseline recording" |
| Experimenter | text | Yes | `experimenter` | "John Doe" |
| Laboratory | text | No | `lab` | "Neuroscience Lab" |
| Institution | text | No | `institution` | "NIH NIMH" |

**Note:** Combine Session Date + Session Time to create ISO 8601 timestamp:
```python
session_start_time = f"{session_date}T{session_time}:00"  # "2024-01-15T14:30:00"
```

#### Group 4: Device Configuration

| eLabFTW Field Name | Type | Required | Maps to NWB | Example Value |
|-------------------|------|----------|-------------|---------------|
| Optical Fiber Model | text | No | `OpticalFiber.model` | "Doric MFC_400/430-0.48" |
| Fiber Core Diameter (μm) | number | Yes | `OpticalFiber.core_diameter_in_um` | "400" |
| Fiber Numerical Aperture | number | Yes | `OpticalFiber.numerical_aperture` | "0.39" |
| Excitation Wavelength (nm) | number | Yes | `ExcitationSource.excitation_wavelength_in_nm` | "470" |
| Emission Wavelength (nm) | number | Yes | `Photodetector.detected_wavelength_in_nm` | "520" |
| Dichroic Mirror Cut-on (nm) | number | No | `DichroicMirror.cut_on_wavelength_in_nm` | "495" |
| Emission Filter Center (nm) | number | No | `BandOpticalFilter.center_wavelength_in_nm` | "525" |
| Emission Filter Bandwidth (nm) | number | No | `BandOpticalFilter.bandwidth_in_nm` | "50" |

#### Group 5: Recording Channel (FiberPhotometryTable)

| eLabFTW Field Name | Type | Required | Maps to NWB | Example Value |
|-------------------|------|----------|-------------|---------------|
| Recording Location | text | Yes | `FiberPhotometryTable.location` | "VTA" |
| Channel Name | text | No | Metadata / description | "GCaMP6f_470nm" |

**Note:** Other FiberPhotometryTable fields are derived from Groups 2 & 4 (indicators, devices).

#### Group 6: Provenance & Notes

| eLabFTW Field Name | Type | Required | Maps to NWB | Example Value |
|-------------------|------|----------|-------------|---------------|
| Protocol Name | text | No | Custom metadata | "Standard FP Protocol v2" |
| Data File Path | text | No | Custom metadata | "/data/photometry/M001/" |
| Notes | text | No | `session_description` or custom | "Animal behaving normally" |
| Analysis Status | select | No | Custom metadata | "Pending" / "Complete" |

**eLabFTW Options for Analysis Status:**
```json
"Analysis Status": {
  "type": "select",
  "options": ["Pending", "In Progress", "Complete", "Failed"]
}
```

### 4.3 Example Complete eLabFTW Template JSON

```json
{
  "extra_fields": {
    "Subject ID": {
      "type": "text",
      "value": "",
      "required": true,
      "position": 1,
      "group_id": 1,
      "description": "Unique subject identifier (e.g., M001)"
    },
    "Species": {
      "type": "select",
      "value": "Mus musculus",
      "options": ["Mus musculus", "Rattus norvegicus"],
      "required": true,
      "position": 2,
      "group_id": 1
    },
    "Sex": {
      "type": "select",
      "value": "",
      "options": ["M", "F", "U"],
      "required": true,
      "position": 3,
      "group_id": 1
    },
    "Age (days)": {
      "type": "number",
      "value": "",
      "position": 4,
      "group_id": 1,
      "description": "Age in days (e.g., 90)"
    },
    "Surgery Date": {
      "type": "date",
      "value": "",
      "required": true,
      "position": 1,
      "group_id": 2
    },
    "Indicator Label": {
      "type": "select",
      "value": "",
      "options": ["GCaMP6f", "GCaMP7s", "jRGECO1a", "tdTomato"],
      "required": true,
      "position": 2,
      "group_id": 2
    },
    "Injection Location": {
      "type": "text",
      "value": "",
      "required": true,
      "position": 3,
      "group_id": 2,
      "description": "Brain region (e.g., VTA, NAc)"
    },
    "Injection AP (mm)": {
      "type": "number",
      "value": "",
      "required": true,
      "position": 4,
      "group_id": 2,
      "description": "Anterior-posterior coordinate"
    },
    "Session Date": {
      "type": "date",
      "value": "",
      "required": true,
      "position": 1,
      "group_id": 3
    },
    "Session Time": {
      "type": "time",
      "value": "",
      "required": true,
      "position": 2,
      "group_id": 3
    },
    "Experimenter": {
      "type": "text",
      "value": "",
      "required": true,
      "position": 3,
      "group_id": 3
    },
    "Excitation Wavelength (nm)": {
      "type": "number",
      "value": "470",
      "required": true,
      "position": 1,
      "group_id": 4,
      "description": "Excitation light wavelength"
    },
    "Emission Wavelength (nm)": {
      "type": "number",
      "value": "520",
      "required": true,
      "position": 2,
      "group_id": 4,
      "description": "Detected emission wavelength"
    },
    "Fiber Core Diameter (μm)": {
      "type": "number",
      "value": "400",
      "required": true,
      "position": 3,
      "group_id": 4
    },
    "Recording Location": {
      "type": "text",
      "value": "",
      "required": true,
      "position": 1,
      "group_id": 5,
      "description": "Brain region for this recording channel"
    }
  },
  "elabftw": {
    "display_main_text": true,
    "extra_fields_groups": [
      {"id": 1, "name": "Subject Information"},
      {"id": 2, "name": "Surgery & Injection"},
      {"id": 3, "name": "Session Information"},
      {"id": 4, "name": "Device Configuration"},
      {"id": 5, "name": "Recording Channel"},
      {"id": 6, "name": "Notes & Provenance"}
    ]
  }
}
```

### 4.4 Python Mapping Function Pseudocode

```python
def map_elabftw_to_nwb(elabftw_metadata):
    """
    Map eLabFTW extra_fields to ndx-fiber-photometry NWB metadata.

    Args:
        elabftw_metadata: Dict with 'extra_fields' from eLabFTW entry

    Returns:
        Dict with NWB-ready metadata grouped by object type
    """
    fields = elabftw_metadata.get('extra_fields', {})

    # Extract helper function
    def get_value(field_name, default=''):
        return fields.get(field_name, {}).get('value', default)

    # Group 1: Subject
    subject_metadata = {
        'subject_id': get_value('Subject ID'),
        'species': get_value('Species', 'Mus musculus'),
        'sex': get_value('Sex'),
        'age': f"P{get_value('Age (days)')}D" if get_value('Age (days)') else None,
        'strain': get_value('Strain'),
        'genotype': get_value('Genotype'),
        'weight': get_value('Weight (grams)')
    }

    # Group 2: Indicator
    indicator_metadata = {
        'name': f"{get_value('Indicator Label')}_{get_value('Injection Location')}",
        'label': get_value('Indicator Label'),
        'injection_location': get_value('Injection Location'),
        'injection_coordinates_in_mm': (
            float(get_value('Injection AP (mm)', 0)),
            float(get_value('Injection ML (mm)', 0)),
            float(get_value('Injection DV (mm)', 0))
        )
    }

    # Group 3: Session
    session_date = get_value('Session Date')
    session_time = get_value('Session Time')
    session_metadata = {
        'session_id': get_value('Session ID'),
        'session_start_time': f"{session_date}T{session_time}:00",
        'session_description': get_value('Session Description'),
        'experimenter': [get_value('Experimenter')],
        'lab': get_value('Laboratory'),
        'institution': get_value('Institution')
    }

    # Group 4: Devices
    optical_fiber = {
        'name': f"Fiber_{get_value('Fiber Core Diameter (μm)')}um",
        'model': get_value('Optical Fiber Model'),
        'numerical_aperture': float(get_value('Fiber Numerical Aperture', 0)),
        'core_diameter_in_um': float(get_value('Fiber Core Diameter (μm)', 0))
    }

    excitation_source = {
        'name': f"LED_{get_value('Excitation Wavelength (nm)')}nm",
        'excitation_wavelength_in_nm': float(get_value('Excitation Wavelength (nm)', 0))
    }

    photodetector = {
        'name': f"PMT_{get_value('Emission Wavelength (nm)')}nm",
        'detected_wavelength_in_nm': float(get_value('Emission Wavelength (nm)', 0))
    }

    # Group 5: FiberPhotometryTable
    fiber_photometry_table = {
        'location': get_value('Recording Location'),
        'excitation_wavelength_in_nm': float(get_value('Excitation Wavelength (nm)', 0)),
        'emission_wavelength_in_nm': float(get_value('Emission Wavelength (nm)', 0))
    }

    return {
        'subject': subject_metadata,
        'indicator': indicator_metadata,
        'session': session_metadata,
        'optical_fiber': optical_fiber,
        'excitation_source': excitation_source,
        'photodetector': photodetector,
        'fiber_photometry_table': fiber_photometry_table
    }
```

---

## 5. Implementation Recommendations

### 5.1 Template Creation Steps

1. **Create template in eLabFTW UI** (or via API)
2. **Define extra_fields_groups** (6 groups: Subject, Surgery, Session, Device, Channel, Notes)
3. **Add all required fields** with appropriate types (text, number, date, select)
4. **Set position values** to control display order
5. **Mark required fields** (`"required": true`)
6. **Add descriptions** for complex fields
7. **Test template** by creating a sample experiment entry
8. **Export template JSON** for version control

### 5.2 Parser Script Requirements

1. **Authenticate with eLabFTW API** using elabapi-python
2. **Read experiment entry** by ID
3. **Extract metadata.extra_fields** from entry
4. **Validate required fields** are present
5. **Map eLabFTW → NWB** using mapping function
6. **Handle missing/invalid data** gracefully (log warnings)
7. **Return structured dict** ready for NWB file creation

### 5.3 Validation Checklist

- [ ] All required NWB fields can be populated from template
- [ ] Field types match expected data (numbers are numeric, dates are dates)
- [ ] Coordinate values are in correct units (mm for stereotactic, μm for fiber diameter)
- [ ] Wavelengths are in nanometers
- [ ] ISO 8601 timestamp can be constructed from Session Date + Time
- [ ] Age format converts correctly (days → "P90D")
- [ ] Species follows NWB convention ("Mus musculus", not "mouse")

---

## 6. Next Steps

### Task 1.2: Create Fiber Photometry Template (5 hours)
- Use field mapping from Section 4.2
- Create template in eLabFTW with 6 groups
- Add all 30+ fields with proper types
- Test template with sample data

### Task 1.3: Write Parser Script (4 hours)
- Implement elabapi-python client
- Write mapping function from Section 4.4
- Add validation and error handling
- Test with real eLabFTW entries

### Task 1.4: Documentation (3 hours)
- Document template structure
- Create filled example
- Write user guide for template usage

---

## Appendix: Sources & References

### Official Documentation

1. **eLabFTW Metadata Documentation**
   - URL: https://doc.elabftw.net/metadata.html
   - Description: Official documentation for eLabFTW metadata structure and extra_fields
   - Accessed: 2025-11-03

2. **eLabFTW REST API v2 Documentation**
   - URL: https://doc.elabftw.net/api/elabapi-html/
   - Description: Complete API reference for elabapi-python
   - Accessed: 2025-11-03

3. **ndx-fiber-photometry GitHub Repository**
   - URL: https://github.com/catalystneuro/ndx-fiber-photometry
   - Description: Official NWB extension source code, schema definitions, examples
   - Accessed: 2025-11-03

4. **elabapi-python GitHub Repository**
   - URL: https://github.com/elabftw/elabapi-python
   - Description: Python client library source code with 27+ examples
   - Accessed: 2025-11-03

5. **elabapi-python Examples Directory**
   - URL: https://github.com/elabftw/elabapi-python/tree/master/examples
   - Description: 27 example scripts including metadata manipulation (001-manipulating-metadata.py, 08-create-items-add-metadata.py, 09-import-csv.py)
   - Accessed: 2025-11-03

### GitHub Discussions & Issues

6. **eLabFTW Metadata Management Discussion**
   - URL: https://github.com/elabftw/elabftw/discussions/5386
   - Title: "Metadata management with JSON Schema, JSON-LD and ontologies in eLabFTW?"
   - Description: Community discussion on metadata validation and schema management
   - Accessed: 2025-11-03

7. **eLabFTW Machine Readable Custom Fields RFC**
   - URL: https://github.com/elabftw/elabftw/issues/2265
   - Title: "RFC :: Machine readable custom fields"
   - Description: Feature request and design discussion for structured metadata
   - Accessed: 2025-11-03

8. **eLabFTW Machine Readable Fields Discussion**
   - URL: https://github.com/elabftw/elabftw/discussions/2461
   - Title: "RFC :: Machine readable custom fields"
   - Description: Follow-up discussion on metadata field implementation
   - Accessed: 2025-11-03

### Python Package Registries

9. **elabapi-python on PyPI**
   - URL: https://pypi.org/project/elabapi-python/
   - Version: 5.3.0 (released October 20, 2025)
   - Description: Official Python package registry listing
   - Accessed: 2025-11-03

10. **ndx-fiber-photometry on PyPI**
    - URL: https://pypi.org/project/ndx-fiber-photometry/
    - Description: NWB extension package registry listing
    - Accessed: 2025-11-03

11. **ndx-photometry on PyPI**
    - URL: https://pypi.org/project/ndx-photometry/
    - Description: Deprecated predecessor to ndx-fiber-photometry
    - Accessed: 2025-11-03

### Related NWB Extensions

12. **ndx-ophys-devices GitHub Repository**
    - URL: https://github.com/catalystneuro/ndx-ophys-devices
    - Description: Device metadata extension (dependency of ndx-fiber-photometry)
    - Accessed: 2025-11-03

13. **NWB Format Specification**
    - URL: https://nwb-schema.readthedocs.io/en/latest/format_description.html
    - Description: Core NWB format specification for Subject, Session metadata
    - Accessed: 2025-11-03

### Academic Publications

14. **Adamant: JSON Schema-based Metadata Editor**
    - URL: https://pmc.ncbi.nlm.nih.gov/articles/PMC9178528/
    - Title: "Adamant: a JSON schema-based metadata editor for research data management workflows"
    - Description: Research on JSON schema validation for eLabFTW integration
    - Journal: PMC (PubMed Central)
    - Accessed: 2025-11-03

15. **LISTER: Metadata Extraction from eLabFTW**
    - URL: https://pubs.acs.org/doi/abs/10.1021/acs.jcim.3c00744
    - Title: "LISTER: Semiautomatic Metadata Extraction from Annotated Experiment Documentation in eLabFTW"
    - Journal: Journal of Chemical Information and Modeling
    - Description: Automated metadata parsing from eLabFTW entries
    - Accessed: 2025-11-03

### Community Resources

16. **eLabFTW BayernCollab Guide**
    - URL: https://collab.dvb.bayern/spaces/TUMelabftw/pages/1759249241/13.+REST+API+👥🟦
    - Title: "13. REST API 👥🟦"
    - Description: Community guide for eLabFTW REST API usage
    - Accessed: 2025-11-03

17. **eLabFTW Guide (TU Graz)**
    - URL: http://lampx.tugraz.at/~hadley/semi/elabftw/elab.html
    - Title: "elabFTW Guide"
    - Description: University guide for eLabFTW usage
    - Accessed: 2025-11-03

### Fiber Photometry Resources (General)

18. **TDT Fiber Photometry User Guide**
    - URL: https://www.tdt.com/docs/fiber-photometry-user-guide/overview/
    - Description: Commercial vendor guide for fiber photometry hardware and techniques
    - Accessed: 2025-11-03

19. **Mightex Fiber Photometry Guide**
    - URL: https://www.mightexbio.com/fiber-photometry/
    - Description: Fiber photometry methodology overview
    - Accessed: 2025-11-03

20. **RWD Fiber Photometry FAQ**
    - URL: https://www.rwdstco.com/answers-to-12-frequently-asked-questions-about-fiber-photometry-experiments/
    - Title: "Guide to Fiber Photometry|12 FAQs Answered"
    - Description: Common questions about fiber photometry experiments
    - Accessed: 2025-11-03

---

## Document Control

**Author**: Claude (AI Assistant)
**Project**: elabftw-app
**Task**: Task 1.1 - Research eLabFTW template structure and ndx-fiber-photometry field mapping
**Duration**: 3 hours
**Status**: Complete
**Next Task**: Task 1.2 - Create fiber photometry experiment template in eLabFTW (5 hours)

---

**End of Research Document**
