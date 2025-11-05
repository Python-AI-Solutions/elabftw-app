# Complete Deployment and Testing Guide
## eLabFTW Local Instance + Streamlit Validation Workflow

This guide walks you through:
1. Deploying a local eLabFTW instance
2. Creating an experiment with ndx-photometry test data
3. Running Journey A to validate the experiment
4. Running the full pytest suite

---

## Part 1: Deploy Local eLabFTW Instance

### Prerequisites

- Docker and Docker Compose installed
- Python 3.13
- `uv` package manager (or standard Python)

### Step 1: Run Deployment Script

```bash
# Navigate to project root
cd c:\Users\shahh\Projects\elabftw-app

# Run the deployment script
uv run python deploy-local.py
# OR
python deploy-local.py
```

**What happens:**
- Downloads official `docker-compose.yml` from get.elabftw.net
- Configures for HTTPS on `https://localhost:3148`
- Uses Docker volumes for persistent data
- Starts MySQL + eLabFTW containers
- Initializes database on first run
- Creates test admin account:
  - Email: `admin@localhost`
  - Password: `elabftw123` (or set `ELABFTW_TEST_PASSWORD` env var)

**Output you'll see:**
```
🧪 eLabFTW Local Development Deployment
======================================================================

📥 Downloading official docker-compose.yml from get.elabftw.net...
   ✅ Downloaded successfully

🔧 Configuring for local development...
✅ Configuration complete!

📦 Starting Docker containers...
   This may take 2-5 minutes for MySQL first-time initialization...
   ⏳ Waiting for services to be ready...
   ✅ All services ready!

🗄️  Initializing eLabFTW database...
   ✅ Database initialized successfully!

👤 Creating test admin account...
   ✅ Test account ready!
   📧 Email:    admin@localhost
   🔑 Password: elabftw123

======================================================================
✅ eLabFTW Deployment Complete!
======================================================================

🌐 Access URL:
   👉 https://localhost:3148
```

### Step 2: Access eLabFTW Web Interface

1. Open browser and go to: **https://localhost:3148**
2. **Accept the certificate warning** (self-signed cert for local dev):
   - Chrome: Click "Advanced" → "Proceed to localhost (unsafe)"
   - Firefox: Click "Advanced" → "Accept the Risk and Continue"
3. Log in with:
   - Email: `admin@localhost`
   - Password: `elabftw123`

### Step 3: Get Your API Key

1. Once logged in, click your name (top right)
2. Go to **"User Control Panel"**
3. Click **"API KEYS"** tab
4. Click **"Create"** button
5. Give it a name (e.g., "Streamlit Testing")
6. Click **"Save"**
7. Copy the generated API key (looks like: `1234567890abcdef...`)

### Step 4: Set Environment Variables

```bash
# On Windows (PowerShell)
$env:ELABFTW_API_KEY="your_api_key_here"
$env:ELABFTW_URL="https://localhost:3148"
$env:ELABFTW_VERIFY_SSL="false"  # Important for self-signed cert!

# On Linux/Mac
export ELABFTW_API_KEY="your_api_key_here"
export ELABFTW_URL="https://localhost:3148"
export ELABFTW_VERIFY_SSL="false"
```

**Verify configuration:**
```bash
# PowerShell
echo $env:ELABFTW_API_KEY
echo $env:ELABFTW_URL

# Bash
echo $ELABFTW_API_KEY
echo $ELABFTW_URL
```

---

## Part 2: Create Test Experiment with ndx-photometry Data

### Step 5: Create a New Experiment

We'll use the eLabFTW API to create an experiment with realistic fiber photometry data.

Create a Python script to populate test data:

```python
# create_test_experiment.py
import os
import sys
sys.path.append('elabftw-app-tool/scripts')

import elabapi_python
from datetime import date, time

# Configure API
api_key = os.environ.get('ELABFTW_API_KEY')
elabftw_url = os.environ.get('ELABFTW_URL')
verify_ssl = os.environ.get('ELABFTW_VERIFY_SSL', 'true').lower() == 'true'

configuration = elabapi_python.Configuration()
configuration.api_key['api_key'] = api_key
configuration.api_key_prefix['api_key'] = 'Authorization'
configuration.host = f"{elabftw_url}/api/v2"
configuration.verify_ssl = verify_ssl

api_client = elabapi_python.ApiClient(configuration)
experiments_api = elabapi_python.ExperimentsApi(api_client)

# Create complete ndx-photometry compliant metadata
metadata = {
    "extra_fields": {
        # Subject Information (7 fields - all present)
        "Subject ID": {
            "type": "text",
            "value": "M001",
            "required": True,
            "position": 1,
            "group_id": 1,
            "description": "Unique subject identifier"
        },
        "Species": {
            "type": "text",
            "value": "Mus musculus",
            "required": True,
            "position": 2,
            "group_id": 1,
            "description": "Species name (Latin)"
        },
        "Sex": {
            "type": "select",
            "value": "M",
            "required": True,
            "position": 3,
            "group_id": 1,
            "description": "Subject sex",
            "options": ["M", "F", "U"]
        },
        "Age (days)": {
            "type": "number",
            "value": "90",
            "required": False,
            "position": 4,
            "group_id": 1,
            "description": "Age in days at time of surgery"
        },
        "Weight (g)": {
            "type": "number",
            "value": "28.5",
            "required": False,
            "position": 5,
            "group_id": 1,
            "description": "Weight in grams"
        },
        "Genotype": {
            "type": "text",
            "value": "C57BL/6J",
            "required": False,
            "position": 6,
            "group_id": 1,
            "description": "Genetic strain or background"
        },
        "Subject Description": {
            "type": "text",
            "value": "Wildtype control mouse for fiber photometry validation",
            "required": False,
            "position": 7,
            "group_id": 1,
            "description": "Additional notes about the subject"
        },

        # Surgery & Injection (10 fields - all present)
        "Surgery Date": {
            "type": "date",
            "value": "2025-10-15",
            "required": True,
            "position": 8,
            "group_id": 2,
            "description": "Date of surgical procedure (YYYY-MM-DD)"
        },
        "Indicator Label": {
            "type": "text",
            "value": "GCaMP6f",
            "required": True,
            "position": 9,
            "group_id": 2,
            "description": "Name of the calcium indicator (e.g., GCaMP6f, jRGECO1a)"
        },
        "Injection Location": {
            "type": "text",
            "value": "Ventral Tegmental Area (VTA)",
            "required": True,
            "position": 10,
            "group_id": 2,
            "description": "Brain region where indicator was injected"
        },
        "Injection AP (mm)": {
            "type": "number",
            "value": "-3.2",
            "required": True,
            "position": 11,
            "group_id": 2,
            "description": "Anterior-Posterior coordinate from Bregma (mm)"
        },
        "Injection ML (mm)": {
            "type": "number",
            "value": "0.5",
            "required": True,
            "position": 12,
            "group_id": 2,
            "description": "Medial-Lateral coordinate from Bregma (mm)"
        },
        "Injection DV (mm)": {
            "type": "number",
            "value": "-4.5",
            "required": True,
            "position": 13,
            "group_id": 2,
            "description": "Dorsal-Ventral coordinate from brain surface (mm)"
        },
        "Viral Vector": {
            "type": "text",
            "value": "AAV9-Syn-GCaMP6f",
            "required": False,
            "position": 14,
            "group_id": 2,
            "description": "Full name of viral construct (serotype-promoter-gene)"
        },
        "Injection Volume (nL)": {
            "type": "number",
            "value": "500",
            "required": False,
            "position": 15,
            "group_id": 2,
            "description": "Volume injected in nanoliters"
        },
        "Fiber Implant Location": {
            "type": "text",
            "value": "Above VTA",
            "required": False,
            "position": 16,
            "group_id": 2,
            "description": "Where the optical fiber was implanted"
        },
        "Surgery Notes": {
            "type": "text",
            "value": "Surgery completed without complications. Animal recovered well.",
            "required": False,
            "position": 17,
            "group_id": 2,
            "description": "Additional surgical notes"
        },

        # Session Information (7 fields - all present)
        "Session ID": {
            "type": "text",
            "value": "M001_20251101_VTA_001",
            "required": True,
            "position": 18,
            "group_id": 3,
            "description": "Unique session identifier"
        },
        "Session Date": {
            "type": "date",
            "value": "2025-11-01",
            "required": True,
            "position": 19,
            "group_id": 3,
            "description": "Date of recording session (YYYY-MM-DD)"
        },
        "Session Time": {
            "type": "time",
            "value": "14:30:00",
            "required": True,
            "position": 20,
            "group_id": 3,
            "description": "Start time of session (HH:MM:SS)"
        },
        "Experimenter": {
            "type": "text",
            "value": "Dr. Jane Smith",
            "required": True,
            "position": 21,
            "group_id": 3,
            "description": "Name of person who performed recording"
        },
        "Session Duration (min)": {
            "type": "number",
            "value": "30",
            "required": False,
            "position": 22,
            "group_id": 3,
            "description": "Total duration of recording in minutes"
        },
        "Behavioral Task": {
            "type": "text",
            "value": "Free exploration in novel environment",
            "required": False,
            "position": 23,
            "group_id": 3,
            "description": "Description of behavioral paradigm"
        },
        "Session Notes": {
            "type": "text",
            "value": "Good signal quality throughout session. No artifacts detected.",
            "required": False,
            "position": 24,
            "group_id": 3,
            "description": "Additional session notes"
        },

        # Device Configuration (10 fields - all present)
        "Fiber Core Diameter (μm)": {
            "type": "number",
            "value": "400",
            "required": True,
            "position": 25,
            "group_id": 4,
            "description": "Core diameter of optical fiber in micrometers"
        },
        "Fiber Numerical Aperture": {
            "type": "number",
            "value": "0.48",
            "required": True,
            "position": 26,
            "group_id": 4,
            "description": "Numerical aperture (NA) of fiber (range: 0.1-1.0)"
        },
        "Excitation Wavelength (nm)": {
            "type": "number",
            "value": "470",
            "required": True,
            "position": 27,
            "group_id": 4,
            "description": "Excitation light wavelength in nanometers"
        },
        "Emission Wavelength (nm)": {
            "type": "number",
            "value": "525",
            "required": True,
            "position": 28,
            "group_id": 4,
            "description": "Emission filter wavelength in nanometers"
        },
        "Excitation Source": {
            "type": "text",
            "value": "470nm LED (Thorlabs M470F3)",
            "required": False,
            "position": 29,
            "group_id": 4,
            "description": "Light source model and specifications"
        },
        "Excitation Power (mW)": {
            "type": "number",
            "value": "0.5",
            "required": False,
            "position": 30,
            "group_id": 4,
            "description": "Excitation light power at fiber tip in milliwatts"
        },
        "Photodetector Model": {
            "type": "text",
            "value": "Newport 2151 Femtowatt Photoreceiver",
            "required": False,
            "position": 31,
            "group_id": 4,
            "description": "Model of photodetector/PMT used"
        },
        "Dichroic Mirror": {
            "type": "text",
            "value": "490nm longpass dichroic",
            "required": False,
            "position": 32,
            "group_id": 4,
            "description": "Dichroic mirror specifications"
        },
        "Emission Filter": {
            "type": "text",
            "value": "525/50nm bandpass filter",
            "required": False,
            "position": 33,
            "group_id": 4,
            "description": "Emission filter specifications"
        },
        "Device Description": {
            "type": "text",
            "value": "Custom fiber photometry rig with LED excitation and lock-in detection",
            "required": False,
            "position": 34,
            "group_id": 4,
            "description": "Overall device description"
        },

        # Recording Channel (3 fields - all present)
        "Recording Location": {
            "type": "text",
            "value": "VTA dopamine neurons",
            "required": True,
            "position": 35,
            "group_id": 5,
            "description": "Brain region/cell type recorded from"
        },
        "Sampling Rate (Hz)": {
            "type": "number",
            "value": "1000",
            "required": False,
            "position": 36,
            "group_id": 5,
            "description": "Data acquisition sampling rate in Hz"
        },
        "Signal Type": {
            "type": "text",
            "value": "Fluorescence (F) and isosbestic control (F_iso)",
            "required": False,
            "position": 37,
            "group_id": 5,
            "description": "Type of signals recorded"
        },

        # Notes & Provenance (8 fields - all present)
        "Data File Path": {
            "type": "text",
            "value": "/data/fiber_photometry/M001/2025-11-01/M001_20251101_001.csv",
            "required": False,
            "position": 38,
            "group_id": 6,
            "description": "Path to raw data file"
        },
        "Analysis Software": {
            "type": "text",
            "value": "Python 3.13 with pynwb, ndx-fiber-photometry",
            "required": False,
            "position": 39,
            "group_id": 6,
            "description": "Software used for analysis"
        },
        "Lab": {
            "type": "text",
            "value": "Neuroscience Research Lab",
            "required": False,
            "position": 40,
            "group_id": 6,
            "description": "Lab or institution name"
        },
        "Protocol": {
            "type": "text",
            "value": "IACUC Protocol #2024-001",
            "required": False,
            "position": 41,
            "group_id": 6,
            "description": "Animal protocol or ethics approval number"
        },
        "Funding": {
            "type": "text",
            "value": "NIH Grant R01-NS123456",
            "required": False,
            "position": 42,
            "group_id": 6,
            "description": "Funding source"
        },
        "Related Publications": {
            "type": "text",
            "value": "Smith et al. (2024) Nature Neuroscience",
            "required": False,
            "position": 43,
            "group_id": 6,
            "description": "Related publications or DOIs"
        },
        "Data Quality": {
            "type": "text",
            "value": "Excellent - low noise, stable baseline",
            "required": False,
            "position": 44,
            "group_id": 6,
            "description": "Notes on data quality"
        },
        "Additional Notes": {
            "type": "text",
            "value": "This is a test experiment for validating the Streamlit fiber photometry metadata tool.",
            "required": False,
            "position": 45,
            "group_id": 6,
            "description": "Any additional notes"
        }
    },
    "elabftw": {
        "display_main_text": True,
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

# Create experiment
experiment_body = {
    'title': 'Fiber Photometry Test - M001 VTA Recording',
    'body': '''# Test Experiment for Streamlit Validation

This experiment contains **complete ndx-fiber-photometry metadata** for testing Journey A validation.

## Summary
- **Subject:** M001 (Mus musculus, Male, 90 days, 28.5g)
- **Surgery:** VTA injection of AAV9-Syn-GCaMP6f on 2025-10-15
- **Session:** Recording on 2025-11-01 at 14:30
- **Recording Site:** VTA dopamine neurons
- **Excitation:** 470nm LED, 0.5mW
- **Emission:** 525nm bandpass filter
- **Sampling:** 1000 Hz

## Metadata
All 45 fields are populated in the metadata section below.
- ✅ **18 required fields** - All present
- ✅ **27 optional fields** - All present

## Purpose
Test dataset for validating:
1. Journey A (Validation) - should show 0 errors
2. Parser script - should extract all fields correctly
3. NWB conversion - should map to ndx-fiber-photometry objects
''',
    'metadata': metadata
}

try:
    result = experiments_api.post_experiment(body=experiment_body)
    experiment_id = result.id

    print("=" * 70)
    print("✅ Test Experiment Created Successfully!")
    print("=" * 70)
    print(f"\n📋 Experiment ID: {experiment_id}")
    print(f"📝 Title: {result.title}")
    print(f"🔗 URL: {elabftw_url}/experiments.php?mode=view&id={experiment_id}")
    print(f"\n✅ All 45 fields populated (18 required + 27 optional)")
    print("\nNext steps:")
    print(f"1. Run Journey A validation with experiment ID: {experiment_id}")
    print(f"2. Expected result: 0 errors, 0 warnings")
    print(f"3. All required fields should be present")
    print("\n" + "=" * 70)

except Exception as e:
    print(f"❌ Failed to create experiment: {e}")
    sys.exit(1)
```

Save this as `create_test_experiment.py` and run it:

```bash
python create_test_experiment.py
```

**Expected Output:**
```
======================================================================
✅ Test Experiment Created Successfully!
======================================================================

📋 Experiment ID: 1
📝 Title: Fiber Photometry Test - M001 VTA Recording
🔗 URL: https://localhost:3148/experiments.php?mode=view&id=1

✅ All 45 fields populated (18 required + 27 optional)

Next steps:
1. Run Journey A validation with experiment ID: 1
2. Expected result: 0 errors, 0 warnings
3. All required fields should be present

======================================================================
```

---

## Part 3: Run Journey A to Validate the Experiment

### Step 6: Install Streamlit Dependencies

```bash
cd elabftw-app-tool/streamlit_app
pip install streamlit elabapi-python
# OR
pixi add streamlit elabapi-python
```

### Step 7: Launch the Streamlit App

```bash
streamlit run Home.py
```

**Output:**
```
  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.1.x:8501
```

### Step 8: Use Journey A to Validate

1. Browser opens to Home page
2. Click **"🚀 Start Journey A"** button
3. Enter experiment ID from Step 5 (e.g., `1`)
4. Click **"🔍 Load Experiment"** button

**Expected Results:**

✅ **Perfect Validation:**
```
🎉 Perfect! This experiment meets all ndx-fiber-photometry requirements!

✅ All 18 required fields present
✅ No data range warnings
✅ Ready for NWB file generation
```

**What you should see:**
- Green success box: "This experiment meets all requirements!"
- Experiment info displayed (ID, title, dates)
- Current metadata viewable in expander
- Option to export validated metadata as JSON
- No "Fill Missing Fields" form (since all fields are present)

**Validation Checks Performed:**
- ✅ All 18 required fields present
- ✅ Data ranges valid:
  - Coordinates within -10 to 10 mm
  - Excitation wavelength: 470nm (within 300-800nm)
  - Emission wavelength: 525nm (within 300-800nm)
  - Numerical aperture: 0.48 (within 0.1-1.0)
- ✅ All field types correct
- ✅ Group structure intact

---

## Part 4: Run pytest Suite (Testing All Journeys)

### Step 9: Install pytest and Dependencies

```bash
cd c:\Users\shahh\Projects\elabftw-app\elabftw-app-tool

# Install test dependencies
pip install pytest pytest-mock requests-mock
# OR
pixi add pytest pytest-mock requests-mock
```

### Step 10: Run the Complete Test Suite

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_streamlit_journeys.py -v

# Run with coverage
pytest tests/ -v --cov=streamlit_app --cov-report=html

# Run only Journey A tests
pytest tests/ -v -k "journey_a"

# Run only validation tests
pytest tests/ -v -k "validation"
```

**Expected Test Categories:**

1. **Template Tests** (`test_template.py`)
   - Validates template JSON structure
   - Checks 45 fields present
   - Verifies 18 required fields marked
   - Tests 6 groups configured

2. **Parser Tests** (`test_parser.py`)
   - Tests metadata extraction
   - Validates required field checking
   - Tests data range validation
   - Tests NWB mapping

3. **Journey A Tests** (`test_journey_a.py`)
   - Test experiment loading
   - Test validation logic
   - Test missing field detection
   - Test experiment update

4. **Journey B Tests** (`test_journey_b.py`)
   - Test form rendering
   - Test JSON export/import
   - Test experiment creation
   - Test validation

5. **Journey C Tests** (`test_journey_c.py`)
   - Test template loading
   - Test blank experiment detection
   - Test template application
   - Test merging with existing metadata

6. **Integration Tests** (`test_integration.py`)
   - Test full workflow: C → A validation
   - Test workflow: B → A validation
   - Test API error handling
   - Test cross-journey consistency

---

## Part 5: Manual Testing Checklist

### Journey A - Validate & Fix
- [ ] Load experiment with complete metadata → Shows "Perfect!" message
- [ ] Load experiment with 5 missing fields → Shows 5 errors
- [ ] Fill missing fields → Update succeeds
- [ ] Re-validate after update → Shows "Perfect!" message
- [ ] Load non-existent experiment ID → Shows error message

### Journey B - Create New Entry
- [ ] Fill all 45 fields → Submission succeeds
- [ ] Fill only 17/18 required → Shows validation error
- [ ] Export to JSON → File downloads correctly
- [ ] Import from JSON → Form pre-populates
- [ ] Submit without API → Falls back to local JSON save

### Journey C - Add Template
- [ ] Template loads with correct stats (45 fields, 18 required, 6 groups)
- [ ] Load blank experiment → Shows "ready for template" message
- [ ] Load experiment with metadata → Shows merge warning
- [ ] Apply template → Success with balloons
- [ ] Verify in eLabFTW → All 45 fields present

---

## Part 6: Troubleshooting

### Issue: "elabftw-python not installed"
```bash
pip install elabapi-python
```

### Issue: "SSL: CERTIFICATE_VERIFY_FAILED"
```bash
# Set environment variable
export ELABFTW_VERIFY_SSL="false"  # Linux/Mac
$env:ELABFTW_VERIFY_SSL="false"    # PowerShell
```

### Issue: "API Error 401 Unauthorized"
- Check API key is correct
- Verify API key has not expired
- Ensure you're logged into eLabFTW
- Check API key has proper permissions

### Issue: "Connection refused on localhost:3148"
```bash
# Check if containers are running
docker compose ps

# Restart if needed
docker compose restart

# View logs
docker compose logs -f
```

### Issue: Experiment ID doesn't exist
- Check experiment was created successfully
- Verify you're using the correct experiment ID (number shown in URL)
- Log into eLabFTW web interface and verify experiment exists

---

## Part 7: Cleanup

### Stop eLabFTW (Keep Data)
```bash
docker compose down
```

### Remove Everything (Wipe Data)
```bash
docker compose down -v
rm docker-compose.yml
```

### Restart eLabFTW Later
```bash
# Re-run deployment script
python deploy-local.py

# Choose option 1 to keep existing data
# Your admin account and all experiments will still be there!
```

---

## Summary Checklist

- [ ] Deploy local eLabFTW with `deploy-local.py`
- [ ] Access https://localhost:3148 and accept cert warning
- [ ] Log in with admin@localhost / elabftw123
- [ ] Get API key from User Panel
- [ ] Set environment variables (ELABFTW_API_KEY, ELABFTW_URL, ELABFTW_VERIFY_SSL)
- [ ] Create test experiment with `create_test_experiment.py`
- [ ] Note experiment ID (e.g., 1)
- [ ] Launch Streamlit: `streamlit run Home.py`
- [ ] Use Journey A to validate experiment ID
- [ ] Verify 0 errors, all fields present
- [ ] Run pytest suite: `pytest tests/ -v`
- [ ] Verify all tests pass

---

## Next Steps After Validation

1. **Test Journey C**: Create another blank experiment, use Journey C to inject template
2. **Test Journey B**: Fill form from scratch, create new experiment
3. **Test Parser**: Run parser script directly on experiment
4. **NWB Conversion**: Use validated metadata to generate NWB file (future phase)
5. **DANDI Upload**: Upload NWB file to DANDI archive (future phase)

---

## Useful Commands Reference

```bash
# Docker Management
docker compose ps                    # Show container status
docker compose logs -f               # Tail logs
docker compose restart               # Restart all containers
docker compose down                  # Stop (keep data)
docker compose down -v               # Stop and wipe data

# eLabFTW CLI
docker exec elabftw bin/console      # Access eLabFTW console

# Testing
pytest tests/ -v                     # Run all tests
pytest tests/ -v -k "journey_a"      # Run specific journey tests
pytest tests/ -v --maxfail=1         # Stop on first failure
pytest tests/ -v --pdb               # Drop into debugger on failure

# Streamlit
streamlit run Home.py                # Run with default settings
streamlit run Home.py --server.port 8502  # Custom port
streamlit run Home.py --server.runOnSave true  # Auto-reload
```

---

**Version:** 1.0.0
**Last Updated:** 2025-11-04
**Tested With:** eLabFTW 5.1+, Python 3.13, Streamlit 1.28+
