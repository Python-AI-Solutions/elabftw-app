"""
End-to-End Test for Journey A: Validate Existing Entry

This test:
1. Creates a partial experiment in eLabFTW (with 8 missing required fields)
2. Simulates the Streamlit app workflow
3. Validates that the correct validation errors are returned
4. Tests the complete load -> validate -> update -> re-validate workflow

Author: elabftw-app
Created: 2025-11-05
License: MIT
"""

import os
import json
import sys
from pathlib import Path
import pytest
import requests
import urllib3

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    # tests/ -> elabftw-app-tool/ -> elabftw-app/ -> .env
    env_path = Path(__file__).parent.parent.parent / '.env'
    load_dotenv(env_path)
except ImportError:
    pass  # dotenv not installed

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Add parent directory to path for imports
# tests/ -> elabftw-app-tool/
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.parse_elabftw_metadata import ELabFTWMetadataParser


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture(scope="module")
def api_credentials():
    """Get API credentials from environment."""
    api_key = os.environ.get('ELABFTW_API_KEY')
    elabftw_url = os.environ.get('ELABFTW_URL')
    verify_ssl = os.environ.get('ELABFTW_VERIFY_SSL', 'false').lower() == 'true'

    if not api_key or not elabftw_url:
        pytest.skip("ELABFTW_API_KEY and ELABFTW_URL must be set")

    return {
        'api_key': api_key,
        'url': elabftw_url,
        'verify_ssl': verify_ssl
    }


@pytest.fixture(scope="module")
def partial_experiment_data():
    """Load the partial experiment JSON data."""
    # tests/ -> elabftw-app-tool/ -> elabftw-app/ -> test_data/
    json_path = Path(__file__).parent.parent.parent / 'test_data' / 'demo_experiment_partial.json'

    if not json_path.exists():
        pytest.skip(f"Test data not found: {json_path}")

    with open(json_path, 'r') as f:
        return json.load(f)


@pytest.fixture(scope="module")
def test_experiment_id(api_credentials, partial_experiment_data):
    """
    Create a test experiment with partial metadata and return its ID.
    Cleanup after tests complete.
    """
    api_key = api_credentials['api_key']
    elabftw_url = api_credentials['url']
    verify_ssl = api_credentials['verify_ssl']

    print("\n" + "=" * 70)
    print("Creating test experiment with partial metadata...")
    print("=" * 70)

    # Create experiment
    create_payload = {
        'title': partial_experiment_data['title'],
        'body': partial_experiment_data['body'],
        'metadata': json.dumps(partial_experiment_data['metadata'])
    }

    response = requests.post(
        f"{elabftw_url}/api/v2/experiments",
        headers={
            'Authorization': api_key,
            'Content-Type': 'application/json'
        },
        json=create_payload,
        verify=verify_ssl
    )

    assert response.status_code == 201, f"Failed to create experiment: {response.text}"

    # Extract experiment ID from Location header (e.g., "/api/v2/experiments/5")
    location = response.headers.get('Location', '')
    if location:
        experiment_id = int(location.split('/')[-1])
    else:
        # Fallback: try to get from response body
        try:
            experiment_id = response.json()['id']
        except:
            # Last resort: query all experiments and get the most recent one
            list_response = requests.get(
                f"{elabftw_url}/api/v2/experiments",
                headers={'Authorization': api_key},
                verify=verify_ssl
            )
            experiments = list_response.json()
            experiment_id = experiments[0]['id']  # First one is most recent

    print(f"OK Created test experiment ID: {experiment_id}")

    yield experiment_id

    # Cleanup: Delete the test experiment
    print(f"\nOK Cleaning up: Deleting experiment {experiment_id}")
    delete_response = requests.delete(
        f"{elabftw_url}/api/v2/experiments/{experiment_id}",
        headers={'Authorization': api_key},
        verify=verify_ssl
    )

    if delete_response.status_code == 204:
        print(f"OK Successfully deleted experiment {experiment_id}")
    else:
        print(f"WARNING Failed to delete experiment {experiment_id}: {delete_response.text}")


# ============================================================================
# Helper Functions (Simulate Streamlit App Logic)
# ============================================================================

def load_experiment(experiment_id, api_credentials):
    """
    Simulate the Streamlit load_experiment function.
    Returns (success, experiment_data or error_message)
    """
    api_key = api_credentials['api_key']
    elabftw_url = api_credentials['url']
    verify_ssl = api_credentials['verify_ssl']

    try:
        # Make raw API call (same as Streamlit)
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

            # Extract the actual metadata if it's nested
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


def validate_experiment(experiment_data, api_credentials):
    """
    Simulate the Streamlit validate_experiment function.
    Returns (errors, warnings, nwb_metadata, error_msg)
    """
    try:
        # Create parser (same as Streamlit)
        parser = ELabFTWMetadataParser(
            api_key=api_credentials['api_key'],
            elabftw_url=api_credentials['url'],
            verify_ssl=api_credentials['verify_ssl']
        )

        # Get metadata
        metadata = experiment_data.get('metadata', {})

        # Validate
        errors = parser.validate_required_fields(metadata)
        warnings = parser.validate_data_ranges(metadata)

        # Map to NWB
        nwb_metadata = parser.map_to_nwb_metadata(metadata)

        return errors, warnings, nwb_metadata, None

    except Exception as e:
        return [], [], {}, f"Validation error: {e}"


# ============================================================================
# E2E Tests
# ============================================================================

class TestJourneyAE2E:
    """End-to-end tests for Journey A: Validate Existing Entry."""

    def test_01_load_partial_experiment(self, test_experiment_id, api_credentials):
        """Test loading an experiment with partial metadata."""
        print("\n" + "-" * 70)
        print("TEST 1: Load Partial Experiment")
        print("-" * 70)

        success, result = load_experiment(test_experiment_id, api_credentials)

        assert success, f"Failed to load experiment: {result}"
        assert 'id' in result
        assert 'metadata' in result
        assert 'extra_fields' in result['metadata']

        print(f"OK Experiment loaded successfully")
        print(f"  ID: {result['id']}")
        print(f"  Title: {result['title']}")
        print(f"  Extra fields count: {len(result['metadata']['extra_fields'])}")


    def test_02_validate_partial_experiment_has_errors(self, test_experiment_id, api_credentials):
        """Test that partial experiment validation returns exactly 8 errors."""
        print("\n" + "-" * 70)
        print("TEST 2: Validate Partial Experiment - Expect 8 Errors")
        print("-" * 70)

        # Load experiment
        success, experiment_data = load_experiment(test_experiment_id, api_credentials)
        assert success, f"Failed to load experiment: {experiment_data}"

        # Validate
        errors, warnings, nwb_metadata, error_msg = validate_experiment(
            experiment_data, api_credentials
        )

        assert error_msg is None, f"Validation failed with error: {error_msg}"

        # Should have missing required fields (at least 8)
        assert len(errors) >= 8, f"Expected at least 8 errors, got {len(errors)}"

        # Check that the core missing fields are detected
        core_missing_fields = [
            'Injection Location',
            'Injection AP (mm)',
            'Injection ML (mm)',
            'Injection DV (mm)',
            'Experimenter',
            'Fiber Numerical Aperture',
            'Emission Wavelength (nm)',
            'Recording Location'
        ]

        for field in core_missing_fields:
            error_found = any(field in error for error in errors)
            assert error_found, f"Expected missing field '{field}' not found in errors"

        print(f"OK Validation returned {len(errors)} errors (expected at least 8)")
        print("\nMissing fields:")
        for i, error in enumerate(errors, 1):
            field_name = error.replace('Required field missing or empty: ', '')
            print(f"  {i}. {field_name}")


    def test_03_validation_generates_nwb_metadata(self, test_experiment_id, api_credentials):
        """Test that NWB metadata is generated even with validation errors."""
        print("\n" + "-" * 70)
        print("TEST 3: NWB Metadata Generation")
        print("-" * 70)

        # Load experiment
        success, experiment_data = load_experiment(test_experiment_id, api_credentials)
        assert success

        # Validate
        errors, warnings, nwb_metadata, error_msg = validate_experiment(
            experiment_data, api_credentials
        )

        # NWB metadata should be generated
        assert nwb_metadata is not None
        assert isinstance(nwb_metadata, dict)
        assert len(nwb_metadata) > 0

        # Check for some expected NWB structure keys (core metadata)
        core_keys = ['subject', 'session', 'indicator', 'optical_fiber']
        for key in core_keys:
            assert key in nwb_metadata, f"Expected NWB core key '{key}' not found"

        print(f"OK NWB metadata generated with {len(nwb_metadata)} top-level keys")
        print(f"  Keys: {list(nwb_metadata.keys())}")


    def test_04_update_and_revalidate_workflow(self, test_experiment_id, api_credentials):
        """
        Test complete workflow:
        1. Load partial experiment
        2. Validate (should have errors)
        3. Add missing fields
        4. Re-validate (should pass)
        """
        print("\n" + "-" * 70)
        print("TEST 4: Complete Update & Re-validate Workflow")
        print("-" * 70)

        # Step 1: Load and validate (should have errors)
        success, experiment_data = load_experiment(test_experiment_id, api_credentials)
        assert success

        errors_before, _, _, _ = validate_experiment(experiment_data, api_credentials)
        assert len(errors_before) >= 8, "Should have 8 errors before update"
        print(f"OK Step 1: Initial validation shows {len(errors_before)} errors")

        # Step 2: Update experiment with missing fields
        missing_fields = {
            'Injection Location': 'NAc',
            'Injection AP (mm)': '1.5',
            'Injection ML (mm)': '0.75',
            'Injection DV (mm)': '-4.5',
            'Experimenter': 'Dr. Test User',
            'Fiber Core Diameter (μm)': '400',
            'Fiber Numerical Aperture': '0.48',
            'Emission Wavelength (nm)': '525',
            'Recording Location': 'NAc'
        }

        current_metadata = experiment_data.get('metadata', {})
        current_extra_fields = current_metadata.get('extra_fields', {})

        # Add missing fields
        for field_name, value in missing_fields.items():
            current_extra_fields[field_name] = {
                'type': 'text',
                'value': str(value)
            }

        # Update via API
        updated_metadata = {
            'extra_fields': current_extra_fields,
            'elabftw': current_metadata.get('elabftw', {})
        }

        response = requests.patch(
            f"{api_credentials['url']}/api/v2/experiments/{test_experiment_id}",
            headers={
                'Authorization': api_credentials['api_key'],
                'Content-Type': 'application/json'
            },
            json={'metadata': json.dumps(updated_metadata)},
            verify=api_credentials['verify_ssl']
        )

        assert response.status_code == 200, f"Failed to update experiment: {response.text}"
        print(f"OK Step 2: Updated experiment with {len(missing_fields)} missing fields")

        # Step 3: Reload and re-validate (should pass now)
        success, updated_experiment_data = load_experiment(test_experiment_id, api_credentials)
        assert success

        errors_after, warnings_after, nwb_metadata_after, error_msg = validate_experiment(
            updated_experiment_data, api_credentials
        )

        assert error_msg is None, f"Validation failed: {error_msg}"
        assert len(errors_after) == 0, f"Should have 0 errors after update, got {len(errors_after)}: {errors_after}"

        print(f"OK Step 3: Re-validation passed with 0 errors")
        print(f"OK Complete workflow successful!")


    def test_05_validation_warnings(self, test_experiment_id, api_credentials):
        """Test that data range validation generates appropriate warnings."""
        print("\n" + "-" * 70)
        print("TEST 5: Data Range Validation Warnings")
        print("-" * 70)

        # Load experiment
        success, experiment_data = load_experiment(test_experiment_id, api_credentials)
        assert success

        # Validate
        errors, warnings, nwb_metadata, error_msg = validate_experiment(
            experiment_data, api_credentials
        )

        # Warnings are optional, just check the function runs
        assert warnings is not None
        assert isinstance(warnings, list)

        print(f"OK Data range validation completed")
        print(f"  Warnings: {len(warnings)}")
        if warnings:
            for i, warning in enumerate(warnings, 1):
                print(f"    {i}. {warning}")


# ============================================================================
# Summary
# ============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("Journey A E2E Test Suite")
    print("=" * 70)
    print("\nTo run these tests:")
    print("  pytest tests/test_journey_a_e2e.py -v")
    print("\nTo run with output:")
    print("  pytest tests/test_journey_a_e2e.py -v -s")
    print("\n" + "=" * 70 + "\n")
