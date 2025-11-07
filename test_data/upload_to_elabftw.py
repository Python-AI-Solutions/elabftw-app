#!/usr/bin/env python3
"""
Upload Experiment to eLabFTW

This script reads an experiment JSON file and uploads it to an eLabFTW instance
using the elabapi-python library.

Usage:
    python upload_to_elabftw.py

Requirements:
    pip install elabapi-python python-dotenv

Environment Variables (set in .env file or system environment):
    ELABFTW_URL - The eLabFTW instance URL (e.g., https://eln.example.org)
    ELABFTW_API_KEY - Your API key from eLabFTW user control panel
"""

import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import elabapi_python
from elabapi_python.rest import ApiException


def load_experiment_json(json_path):
    """Load and parse the experiment JSON file."""
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: File not found: {json_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in file: {e}")
        sys.exit(1)


def convert_extra_fields_to_metadata(extra_fields_dict):
    """
    Convert the extra_fields from the JSON to eLabFTW metadata format.

    Args:
        extra_fields_dict: Dictionary with field names as keys, each containing 'type' and 'value'

    Returns:
        Dictionary in eLabFTW metadata format
    """
    metadata = {
        'extra_fields': {}
    }

    for field_name, field_data in extra_fields_dict.items():
        metadata['extra_fields'][field_name] = {
            'type': field_data.get('type', 'text'),
            'value': field_data.get('value', '')
        }

    return metadata


def create_experiment(exp_client, experiment_data):
    """
    Create an experiment in eLabFTW and update it with the provided data.

    Args:
        exp_client: The elabapi_python.ExperimentsApi client
        experiment_data: Dictionary containing experiment data from JSON

    Returns:
        The ID of the created experiment
    """
    print("Creating new experiment...")

    try:
        # Step 1: Create a new experiment (returns HTTP info including Location header)
        response = exp_client.post_experiment_with_http_info()

        # Extract experiment ID from Location header
        location_header = response[2].get('Location')
        experiment_id = int(location_header.split('/').pop())

        print(f"✓ Created experiment with ID: {experiment_id}")

        # Step 2: Build the patch body with all experiment data
        patch_body = {}

        # Add title if present
        if 'title' in experiment_data:
            patch_body['title'] = experiment_data['title']

        # Add date if present
        if 'date' in experiment_data:
            patch_body['date'] = experiment_data['date']

        # Add body (HTML content) if present
        if 'body' in experiment_data:
            patch_body['body'] = experiment_data['body']

        # Add metadata with extra_fields if present
        if 'metadata' in experiment_data and 'extra_fields' in experiment_data['metadata']:
            metadata = convert_extra_fields_to_metadata(experiment_data['metadata']['extra_fields'])
            patch_body['metadata'] = json.dumps(metadata)

        # Step 3: Update the experiment with all data
        print("Updating experiment with data...")
        exp_client.patch_experiment(experiment_id, body=patch_body)

        print("✓ Successfully updated experiment with all data")

        # Step 4: Retrieve and display the created experiment
        experiment = exp_client.get_experiment(experiment_id)

        print("\n" + "="*60)
        print("EXPERIMENT CREATED SUCCESSFULLY")
        print("="*60)
        print(f"ID: {experiment_id}")
        print(f"Title: {experiment.title}")
        if hasattr(experiment, 'created_at'):
            print(f"Created: {experiment.created_at}")
        if hasattr(experiment, 'sharelink'):
            print(f"Share Link: {experiment.sharelink}")
        print("="*60)

        return experiment_id

    except ApiException as e:
        print(f"Error creating/updating experiment: {e}")
        print(f"Status: {e.status}")
        print(f"Reason: {e.reason}")
        print(f"Body: {e.body}")
        sys.exit(1)


def main():
    """Main function to orchestrate the upload process."""

    # Load environment variables from .env file in project root
    # Look for .env in the parent directory (project root)
    project_root = Path(__file__).parent.parent
    env_file = project_root / '.env'
    load_dotenv(env_file)

    # Get configuration from environment variables
    ELABFTW_URL = os.getenv('ELABFTW_URL')
    api_key = os.getenv('ELABFTW_API_KEY')
    verify_ssl = os.getenv('ELABFTW_VERIFY_SSL', 'true').lower() != 'false'

    # Validate configuration
    if not ELABFTW_URL:
        print("Error: ELABFTW_URL environment variable not set")
        print("Please set it to your eLabFTW instance URL (e.g., https://eln.example.org)")
        sys.exit(1)

    if not api_key:
        print("Error: ELABFTW_API_KEY environment variable not set")
        print("Please generate an API key from your eLabFTW user control panel")
        sys.exit(1)

    # Path to the experiment JSON file
    json_file = Path(__file__).parent / 'demo_experiment_partial.json'

    print(f"Loading experiment data from: {json_file}")
    experiment_data = load_experiment_json(json_file)

    print(f"\nConnecting to eLabFTW instance: {ELABFTW_URL}")

    # Initialize the API client
    configuration = elabapi_python.Configuration()
    configuration.host = f"{ELABFTW_URL}/api/v2"
    configuration.verify_ssl = verify_ssl

    api_client = elabapi_python.ApiClient(configuration)
    api_client.set_default_header(header_name='Authorization', header_value=api_key)

    # Create the Experiments API client
    exp_client = elabapi_python.ExperimentsApi(api_client)

    # Test connection by getting info
    try:
        info_client = elabapi_python.InfoApi(api_client)
        info = info_client.get_info()
        print(f"✓ Connected to eLabFTW (version: {info.elabftw_version})")
    except ApiException as e:
        print(f"Error connecting to eLabFTW: {e}")
        print("Please check your ELABFTW_URL and ELABFTW_API_KEY settings")
        sys.exit(1)

    # Create the experiment
    experiment_id = create_experiment(exp_client, experiment_data)

    print(f"\n✓ Process complete! Experiment ID: {experiment_id}")


if __name__ == '__main__':
    main()
