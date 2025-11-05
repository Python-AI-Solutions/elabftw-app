#!/usr/bin/env python3
"""
Create and populate a demo eLabFTW experiment for testing Journey A.

This script creates an experiment with PARTIAL metadata to test validation.
It intentionally leaves some required fields empty to trigger validation errors.

Author: elabftw-app
Created: 2025-11-05
License: MIT
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent))

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    # Load .env from project root (two levels up from this script)
    env_path = Path(__file__).parent.parent.parent / '.env'
    load_dotenv(env_path)
except ImportError:
    print("⚠️  python-dotenv not installed. Install with: pip install python-dotenv")

import elabapi_python
from elabapi_python.rest import ApiException


def create_demo_experiment():
    """
    Create a demo experiment with partial fiber photometry metadata.

    Returns:
        int: Created experiment ID
    """
    # Get configuration from environment
    api_key = os.environ.get('ELABFTW_API_KEY')
    elabftw_url = os.environ.get('ELABFTW_URL', 'https://localhost:3148')
    verify_ssl = os.environ.get('ELABFTW_VERIFY_SSL', 'false').lower() == 'true'

    if not api_key:
        print("Error: ELABFTW_API_KEY environment variable not set")
        print("\nPlease set your API key:")
        print("  export ELABFTW_API_KEY='your_api_key_here'")
        sys.exit(1)

    print(f"Connecting to eLabFTW at {elabftw_url}...")
    print(f"SSL verification: {verify_ssl}")

    # Configure API client
    configuration = elabapi_python.Configuration()
    configuration.host = f"{elabftw_url}/api/v2"
    configuration.verify_ssl = verify_ssl

    # Create API client
    api_client = elabapi_python.ApiClient(configuration)

    # Set Authorization header directly (this is the correct way for eLabFTW)
    api_client.default_headers['Authorization'] = api_key

    experiments_api = elabapi_python.ExperimentsApi(api_client)

    # Experiment basic info
    title = "Test Fiber Photometry Session - M001 - Partial Metadata"
    body = """
# Demo Experiment for Journey A Testing

This experiment contains **partial metadata** to test the validation workflow.

## Purpose
- Test Journey A: Validate & Fix Existing Entry
- Intentionally missing 6 required fields
- Used for automated and manual testing

## Missing Required Fields
This experiment is missing:
1. Injection Location
2. Injection AP (mm)
3. Injection ML (mm)
4. Injection DV (mm)
5. Experimenter
6. Fiber Numerical Aperture
7. Emission Wavelength (nm)
8. Recording Location

These should trigger validation errors in Journey A.
    """

    # Partial metadata - intentionally missing some required fields
    # This will trigger validation errors in Journey A
    partial_metadata = {
        "extra_fields": {
            # GROUP 1: Subject Information (PARTIAL)
            "Subject ID": {
                "type": "text",
                "value": "M001",
                "description": "Unique subject identifier"
            },
            "Species": {
                "type": "select",
                "value": "Mus musculus",
                "description": "Animal species"
            },
            "Sex": {
                "type": "select",
                "value": "M",
                "description": "M=Male, F=Female, U=Unknown"
            },
            "Age (days)": {
                "type": "number",
                "value": "90",
                "description": "Age in days at time of session"
            },
            "Strain": {
                "type": "text",
                "value": "C57BL/6J",
                "description": "Genetic strain"
            },
            "Weight (grams)": {
                "type": "number",
                "value": "25.3",
                "description": "Body weight in grams"
            },

            # GROUP 2: Surgery & Injection (PARTIAL - MISSING COORDINATES AND LOCATION)
            "Surgery Date": {
                "type": "date",
                "value": "2024-10-15",
                "description": "Date of viral injection and/or fiber implantation surgery"
            },
            "Indicator Label": {
                "type": "select",
                "value": "GCaMP6f",
                "description": "Fluorescent indicator type"
            },
            # MISSING: Injection Location (REQUIRED)
            # MISSING: Injection AP (mm) (REQUIRED)
            # MISSING: Injection ML (mm) (REQUIRED)
            # MISSING: Injection DV (mm) (REQUIRED)
            "Viral Vector Name": {
                "type": "text",
                "value": "AAV9-hSyn-GCaMP6f",
                "description": "Full viral construct name"
            },
            "Viral Titer": {
                "type": "text",
                "value": "1e13 GC/mL",
                "description": "Viral titer"
            },
            "Injection Volume (nL)": {
                "type": "number",
                "value": "300",
                "description": "Volume injected in nanoliters"
            },
            "Fiber Implant Depth (mm)": {
                "type": "number",
                "value": "5.2",
                "description": "Depth of fiber tip from brain surface in mm"
            },

            # GROUP 3: Session Information (PARTIAL - MISSING EXPERIMENTER)
            "Session ID": {
                "type": "text",
                "value": "session_20241101_M001",
                "description": "Unique session identifier"
            },
            "Session Date": {
                "type": "date",
                "value": "2024-11-01",
                "description": "Date of recording session"
            },
            "Session Time": {
                "type": "time",
                "value": "14:30",
                "description": "Start time of recording session"
            },
            "Session Description": {
                "type": "text",
                "value": "Baseline recording session",
                "description": "Brief description"
            },
            # MISSING: Experimenter (REQUIRED)
            "Laboratory": {
                "type": "text",
                "value": "Neural Dynamics Lab",
                "description": "Laboratory name"
            },
            "Institution": {
                "type": "text",
                "value": "NIH NIMH",
                "description": "Institution name"
            },

            # GROUP 4: Device Configuration (PARTIAL - MISSING SOME FIELDS)
            "Optical Fiber Model": {
                "type": "text",
                "value": "Doric MFC_400/430-0.48",
                "description": "Manufacturer and model"
            },
            "Fiber Core Diameter (μm)": {
                "type": "number",
                "value": "400",
                "description": "Core diameter in micrometers"
            },
            # MISSING: Fiber Numerical Aperture (REQUIRED)
            "Excitation Wavelength (nm)": {
                "type": "number",
                "value": "470",
                "description": "Excitation light wavelength in nanometers"
            },
            # MISSING: Emission Wavelength (nm) (REQUIRED)
            "Dichroic Mirror Cut-on (nm)": {
                "type": "number",
                "value": "495",
                "description": "Dichroic mirror cut-on wavelength in nm"
            },
            "LED Power (mW)": {
                "type": "number",
                "value": "0.5",
                "description": "LED output power in milliwatts"
            },
            "PMT Gain": {
                "type": "number",
                "value": "5",
                "description": "Photomultiplier tube gain setting"
            },

            # GROUP 5: Recording Channel (MISSING RECORDING LOCATION)
            # MISSING: Recording Location (REQUIRED)
            "Channel Name": {
                "type": "text",
                "value": "GCaMP6f_470nm",
                "description": "Descriptive channel name"
            },
            "Sampling Rate (Hz)": {
                "type": "number",
                "value": "1000",
                "description": "Data acquisition sampling rate in Hz"
            },

            # GROUP 6: Notes & Provenance (COMPLETE)
            "Protocol Name": {
                "type": "text",
                "value": "FP-BASELINE-V1",
                "description": "Experimental protocol or SOP identifier"
            },
            "Data File Path": {
                "type": "text",
                "value": "/data/fp_recordings/M001/session_20241101",
                "description": "Path to raw data files"
            },
            "Behavioral Task": {
                "type": "select",
                "value": "Freely moving",
                "description": "Type of behavioral task during recording"
            },
            "Notes": {
                "type": "text",
                "value": "Animal showed good signal-to-noise ratio. No artifacts detected.",
                "description": "Additional observations or comments"
            },
            "Analysis Status": {
                "type": "select",
                "value": "Pending",
                "description": "Current analysis status for tracking"
            },
            "Quality Control": {
                "type": "select",
                "value": "Pass",
                "description": "Data quality assessment"
            }
        },
        "elabftw": {
            "display_main_text": True
        }
    }

    try:
        # Create experiment
        print("\nCreating experiment...")
        experiment = experiments_api.post_experiment(
            body={
                'title': title,
                'body': body,
                'metadata': partial_metadata
            }
        )

        experiment_id = experiment.id
        print(f"\n✅ SUCCESS! Created experiment ID: {experiment_id}")
        print(f"\nExperiment Details:")
        print(f"  Title: {title}")
        print(f"  URL: {elabftw_url}/experiments.php?mode=view&id={experiment_id}")

        # Count fields
        total_fields = len(partial_metadata['extra_fields'])
        filled_fields = sum(1 for field in partial_metadata['extra_fields'].values()
                          if field.get('value') and field.get('value') != '')
        missing_fields = total_fields - filled_fields

        print(f"\nMetadata Summary:")
        print(f"  Total fields defined: {total_fields}")
        print(f"  Filled fields: {filled_fields}")
        print(f"  Empty fields: {missing_fields}")

        print(f"\n🔍 Missing Required Fields (should trigger validation errors):")
        print(f"  1. Injection Location")
        print(f"  2. Injection AP (mm)")
        print(f"  3. Injection ML (mm)")
        print(f"  4. Injection DV (mm)")
        print(f"  5. Experimenter")
        print(f"  6. Fiber Numerical Aperture")
        print(f"  7. Emission Wavelength (nm)")
        print(f"  8. Recording Location")

        print(f"\n📝 Next Steps:")
        print(f"  1. Open Journey A in Streamlit")
        print(f"  2. Enter experiment ID: {experiment_id}")
        print(f"  3. Observe validation errors")
        print(f"  4. Fill missing required fields")
        print(f"  5. Update experiment and verify validation passes")

        return experiment_id

    except ApiException as e:
        print(f"\n❌ API Error: {e}")
        print(f"\nStatus: {e.status}")
        print(f"Reason: {e.reason}")
        print(f"Body: {e.body}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    print("=" * 70)
    print("Demo eLabFTW Experiment Creator - Journey A Testing")
    print("=" * 70)

    experiment_id = create_demo_experiment()

    print("\n" + "=" * 70)
    print(f"Experiment {experiment_id} created successfully!")
    print("=" * 70)
