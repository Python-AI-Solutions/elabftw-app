#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Create eLabFTW Experiment Templates with Extra Fields
"""

import requests
import json
import sys
import urllib3

# Fix Windows console encoding
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, errors="replace")
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, errors="replace")

# Disable SSL warnings for self-signed cert
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuration
ELABFTW_URL = "https://localhost:3148"
API_ENDPOINT = f"{ELABFTW_URL}/api/v2"

# Templates metadata
SURGERY_TEMPLATE = {
    "extra_fields": {
        "Date of Surgery": {"type": "date", "value": "", "required": True, "position": 1, "group_id": 1},
        "Experiment Description": {"type": "text", "value": "", "position": 2, "group_id": 1},
        "Stereotax Number": {"type": "radio", "value": "", "options": ["1", "2", "3"], "position": 3, "group_id": 1},
        "Intracranial Injection": {"type": "checkbox", "value": "", "position": 4, "group_id": 2},
        "Implant": {"type": "checkbox", "value": "", "position": 5, "group_id": 2},
        "Other Surgery Type": {"type": "text", "value": "", "position": 6, "group_id": 2},
        "Glass Pipette": {"type": "checkbox", "value": "", "position": 7, "group_id": 3},
        "Syringe Needle": {"type": "checkbox", "value": "", "position": 8, "group_id": 3},
        "Other Injection Method": {"type": "text", "value": "", "position": 9, "group_id": 3},
        "Virus Name": {"type": "text", "value": "", "position": 10, "group_id": 4},
        "Virus Source": {"type": "text", "value": "", "position": 11, "group_id": 4},
        "Virus Cat#": {"type": "text", "value": "", "position": 12, "group_id": 4},
        "Virus Lot#": {"type": "text", "value": "", "position": 13, "group_id": 4},
        "Virus Titer": {"type": "number", "value": "", "units": ["vg/ml"], "position": 14, "group_id": 4},
        "Virus Dilution": {"type": "text", "value": "", "position": 15, "group_id": 4},
        "Brain Area": {"type": "text", "value": "", "position": 16, "group_id": 5},
        "Hemisphere": {"type": "radio", "value": "", "options": ["L", "R"], "position": 17, "group_id": 5},
        "AP Coordinate": {"type": "number", "value": "", "units": ["mm"], "position": 18, "group_id": 5},
        "ML Coordinate": {"type": "number", "value": "", "units": ["mm"], "position": 19, "group_id": 5},
        "DV Coordinate": {"type": "number", "value": "", "units": ["mm"], "position": 20, "group_id": 5},
        "Virus Used": {"type": "text", "value": "", "position": 21, "group_id": 5},
        "Injection Volume": {"type": "number", "value": "", "units": ["nl"], "position": 22, "group_id": 5},
        "Injection Speed": {"type": "number", "value": "100", "units": ["nl/min"], "position": 23, "group_id": 5},
        "Implant Type": {"type": "select", "value": "", "options": ["Cannula", "Fiber Optic", "GRIN Lens", "Prism Lens", "Other"], "position": 24, "group_id": 6},
        "Implant Brain Area": {"type": "text", "value": "", "position": 25, "group_id": 6},
        "Implant Hemisphere": {"type": "radio", "value": "", "options": ["L", "R"], "position": 26, "group_id": 6},
        "Implant AP": {"type": "number", "value": "", "units": ["mm"], "position": 27, "group_id": 6},
        "Implant ML": {"type": "number", "value": "", "units": ["mm"], "position": 28, "group_id": 6},
        "Implant DV": {"type": "number", "value": "", "units": ["mm"], "position": 29, "group_id": 6},
        "Subject ID": {"type": "text", "value": "", "position": 30, "group_id": 7},
        "Strain": {"type": "text", "value": "", "position": 31, "group_id": 7},
        "Cage ID": {"type": "text", "value": "", "position": 32, "group_id": 7},
        "Genotype": {"type": "text", "value": "", "position": 33, "group_id": 7},
        "Sex": {"type": "radio", "value": "", "options": ["M", "F"], "position": 34, "group_id": 7},
        "Date of Birth": {"type": "date", "value": "", "position": 35, "group_id": 7},
        "Weight": {"type": "number", "value": "", "units": ["g"], "position": 36, "group_id": 7},
        "Negate ML": {"type": "checkbox", "value": "", "position": 37, "group_id": 7},
        "Subject Notes": {"type": "text", "value": "", "position": 38, "group_id": 7},
        "Injection Notes": {"type": "text", "value": "", "position": 39, "group_id": 8},
        "Implant Notes": {"type": "text", "value": "", "position": 40, "group_id": 8},
        "Surgery Notes": {"type": "text", "value": "", "position": 41, "group_id": 8}
    },
    "elabftw": {
        "display_main_text": False,
        "extra_fields_groups": [
            {"id": 1, "name": "General Info"},
            {"id": 2, "name": "Surgery Type"},
            {"id": 3, "name": "Injection Method"},
            {"id": 4, "name": "Viral Vector"},
            {"id": 5, "name": "Injection Site"},
            {"id": 6, "name": "Implant"},
            {"id": 7, "name": "Subject/Mouse Details"},
            {"id": 8, "name": "Notes"}
        ]
    }
}

BEHAVIOR_TEMPLATE = {
    "extra_fields": {
        "Date": {"type": "date", "value": "", "required": True, "position": 1, "group_id": 1},
        "Start Time": {"type": "time", "value": "", "position": 2, "group_id": 1},
        "Personnel": {"type": "text", "value": "", "position": 3, "group_id": 1},
        "Behavior Room": {"type": "select", "value": "", "options": ["2D-717", "2D-715", "RBC BD825", "RBC BD836", "2D-711"], "position": 4, "group_id": 1},
        "Experiment": {"type": "text", "value": "", "position": 5, "group_id": 1},
        "Manipulation": {"type": "text", "value": "", "position": 6, "group_id": 1},
        "Video File Path": {"type": "text", "value": "", "position": 7, "group_id": 1},
        "AnyMaze Protocol": {"type": "text", "value": "", "position": 8, "group_id": 1},
        "Cue Information": {"type": "text", "value": "", "position": 9, "group_id": 1},
        "Reward Information": {"type": "text", "value": "", "position": 10, "group_id": 1},
        "Subject ID": {"type": "text", "value": "", "position": 11, "group_id": 2},
        "Weight": {"type": "number", "value": "", "units": ["g"], "position": 12, "group_id": 2},
        "Reward Consumed": {"type": "text", "value": "", "position": 13, "group_id": 2},
        "Shock Intensity": {"type": "text", "value": "", "position": 14, "group_id": 2},
        "Box Number": {"type": "text", "value": "", "position": 15, "group_id": 2},
        "Subject Notes": {"type": "text", "value": "", "position": 16, "group_id": 2}
    },
    "elabftw": {
        "display_main_text": False,
        "extra_fields_groups": [
            {"id": 1, "name": "Session Info"},
            {"id": 2, "name": "Subject Details"}
        ]
    }
}


def get_api_key():
    """Prompt user for API key"""
    print("\n" + "="*70)
    print("eLabFTW Template Creator")
    print("="*70)
    print("\nTo create templates, you need an API key:")
    print("1. Log in to eLabFTW at https://localhost:3148")
    print("2. Go to User Panel (top right) → API Keys")
    print("3. Click 'Generate new API Key'")
    print("4. Copy the key and paste it here\n")

    api_key = input("Enter your API key: ").strip()
    if not api_key:
        print("ERROR: API key is required")
        sys.exit(1)

    return api_key


def create_template(api_key, title, body, metadata):
    """Create an experiment template via API"""
    headers = {
        "Authorization": api_key,
        "Content-Type": "application/json"
    }

    payload = {
        "title": title,
        "body": body,
        "metadata": metadata
    }

    try:
        response = requests.post(
            f"{API_ENDPOINT}/experiments_templates",
            headers=headers,
            json=payload,
            verify=False  # Skip SSL verification for self-signed cert
        )

        if response.status_code == 201:
            # eLabFTW sometimes returns empty response body on 201
            try:
                if response.text:
                    template_id = response.json().get("id", "created")
                else:
                    template_id = "created"
            except:
                template_id = "created"
            print(f"✓ Created template: {title}")
            return template_id
        else:
            print(f"✗ Failed to create template: {title}")
            print(f"  Status: {response.status_code}")
            print(f"  Response: {response.text}")
            return None

    except Exception as e:
        print(f"✗ Error creating template: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Main function"""
    api_key = get_api_key()

    print("\n" + "="*70)
    print("Creating Templates...")
    print("="*70 + "\n")

    # Create Surgery Template
    surgery_id = create_template(
        api_key=api_key,
        title="Surgery Data Entry",
        body="<p>Use the extra fields below to record surgery details.</p>",
        metadata=SURGERY_TEMPLATE
    )

    # Create Behavior Template
    behavior_id = create_template(
        api_key=api_key,
        title="Behavior Session",
        body="<p>Use the extra fields below to record behavior session data.</p>",
        metadata=BEHAVIOR_TEMPLATE
    )

    print("\n" + "="*70)
    print("Summary")
    print("="*70)

    if surgery_id and behavior_id:
        print("\n✓ All templates created successfully!")
        print("\nTo use them:")
        print("1. Go to Experiments → Create New")
        print("2. Select template from dropdown")
        print("3. Fill in the extra fields")
    else:
        print("\n✗ Some templates failed to create")
        print("Check the errors above and try again")
        sys.exit(1)


if __name__ == "__main__":
    main()
