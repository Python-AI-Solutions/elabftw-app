#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Update eLabFTW Experiment Templates - Consolidate Mouse Groups
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
API_KEY = "c52605ee3081d2a50ccc76488f1bb776a0d365580295246c7112e42691a748c983f6888caa0024f971f5"

# Updated Surgery Template - Single Mouse Group
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
        "Virus 1": {"type": "text", "value": "", "position": 10, "group_id": 4},
        "Virus 1 Source": {"type": "text", "value": "", "position": 11, "group_id": 4},
        "Virus 1 Cat#": {"type": "text", "value": "", "position": 12, "group_id": 4},
        "Virus 1 Lot#": {"type": "text", "value": "", "position": 13, "group_id": 4},
        "Virus 1 Titer": {"type": "number", "value": "", "units": ["vg/ml"], "position": 14, "group_id": 4},
        "Virus 1 Dilution": {"type": "text", "value": "", "position": 15, "group_id": 4},
        "Virus 2": {"type": "text", "value": "", "position": 16, "group_id": 4},
        "Virus 2 Source": {"type": "text", "value": "", "position": 17, "group_id": 4},
        "Virus 2 Cat#": {"type": "text", "value": "", "position": 18, "group_id": 4},
        "Virus 2 Lot#": {"type": "text", "value": "", "position": 19, "group_id": 4},
        "Virus 2 Titer": {"type": "number", "value": "", "units": ["vg/ml"], "position": 20, "group_id": 4},
        "Virus 2 Dilution": {"type": "text", "value": "", "position": 21, "group_id": 4},
        "Inj 1 Brain Area": {"type": "text", "value": "", "position": 22, "group_id": 5},
        "Inj 1 Hemisphere": {"type": "radio", "value": "", "options": ["L", "R"], "position": 23, "group_id": 5},
        "Inj 1 AP": {"type": "number", "value": "", "units": ["mm"], "position": 24, "group_id": 5},
        "Inj 1 ML": {"type": "number", "value": "", "units": ["mm"], "position": 25, "group_id": 5},
        "Inj 1 DV": {"type": "number", "value": "", "units": ["mm"], "position": 26, "group_id": 5},
        "Inj 1 Virus": {"type": "text", "value": "", "position": 27, "group_id": 5},
        "Inj 1 Volume": {"type": "number", "value": "", "units": ["nl"], "position": 28, "group_id": 5},
        "Inj 1 Speed": {"type": "number", "value": "100", "units": ["nl/min"], "position": 29, "group_id": 5},
        "Inj 2 Brain Area": {"type": "text", "value": "", "position": 30, "group_id": 6},
        "Inj 2 Hemisphere": {"type": "radio", "value": "", "options": ["L", "R"], "position": 31, "group_id": 6},
        "Inj 2 AP": {"type": "number", "value": "", "units": ["mm"], "position": 32, "group_id": 6},
        "Inj 2 ML": {"type": "number", "value": "", "units": ["mm"], "position": 33, "group_id": 6},
        "Inj 2 DV": {"type": "number", "value": "", "units": ["mm"], "position": 34, "group_id": 6},
        "Inj 2 Virus": {"type": "text", "value": "", "position": 35, "group_id": 6},
        "Inj 2 Volume": {"type": "number", "value": "", "units": ["nl"], "position": 36, "group_id": 6},
        "Inj 2 Speed": {"type": "number", "value": "100", "units": ["nl/min"], "position": 37, "group_id": 6},
        "Implant 1 Type": {"type": "select", "value": "", "options": ["Cannula", "Fiber Optic", "GRIN Lens", "Prism Lens", "Other"], "position": 38, "group_id": 7},
        "Implant 1 Brain Area": {"type": "text", "value": "", "position": 39, "group_id": 7},
        "Implant 1 Hemisphere": {"type": "radio", "value": "", "options": ["L", "R"], "position": 40, "group_id": 7},
        "Implant 1 AP": {"type": "number", "value": "", "units": ["mm"], "position": 41, "group_id": 7},
        "Implant 1 ML": {"type": "number", "value": "", "units": ["mm"], "position": 42, "group_id": 7},
        "Implant 1 DV": {"type": "number", "value": "", "units": ["mm"], "position": 43, "group_id": 7},
        # Single Subject/Mouse Details Group
        "Subject ID": {"type": "text", "value": "", "position": 44, "group_id": 8},
        "Strain": {"type": "text", "value": "", "position": 45, "group_id": 8},
        "Cage ID": {"type": "text", "value": "", "position": 46, "group_id": 8},
        "Genotype": {"type": "text", "value": "", "position": 47, "group_id": 8},
        "Sex": {"type": "radio", "value": "", "options": ["M", "F"], "position": 48, "group_id": 8},
        "Date of Birth": {"type": "date", "value": "", "position": 49, "group_id": 8},
        "Weight": {"type": "number", "value": "", "units": ["g"], "position": 50, "group_id": 8},
        "Negate ML": {"type": "checkbox", "value": "", "position": 51, "group_id": 8},
        "Subject Notes": {"type": "text", "value": "", "position": 52, "group_id": 8},
        # Notes
        "Injection Notes": {"type": "text", "value": "", "position": 53, "group_id": 9},
        "Implant Notes": {"type": "text", "value": "", "position": 54, "group_id": 9},
        "Surgery Notes": {"type": "text", "value": "", "position": 55, "group_id": 9}
    },
    "elabftw": {
        "display_main_text": False,
        "extra_fields_groups": [
            {"id": 1, "name": "General Info"},
            {"id": 2, "name": "Surgery Type"},
            {"id": 3, "name": "Injection Method"},
            {"id": 4, "name": "Viral Vectors"},
            {"id": 5, "name": "Injection 1"},
            {"id": 6, "name": "Injection 2"},
            {"id": 7, "name": "Implant 1"},
            {"id": 8, "name": "Subject/Mouse Details"},
            {"id": 9, "name": "Notes"}
        ]
    }
}

# Updated Behavior Template - Single Subject Group
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
        # Single Subject Details
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


def update_template(template_id, metadata):
    """Update an existing template's metadata"""
    headers = {
        "Authorization": API_KEY,
        "Content-Type": "application/json"
    }

    payload = {
        "metadata": metadata
    }

    try:
        response = requests.patch(
            f"{API_ENDPOINT}/experiments_templates/{template_id}",
            headers=headers,
            json=payload,
            verify=False
        )

        if response.status_code == 200:
            print(f"✓ Updated template ID {template_id}")
            return True
        else:
            print(f"✗ Failed to update template ID {template_id}")
            print(f"  Status: {response.status_code}")
            print(f"  Response: {response.text}")
            return False

    except Exception as e:
        print(f"✗ Error updating template: {e}")
        return False


def main():
    """Main function"""
    print("\n" + "="*70)
    print("Updating eLabFTW Templates - Consolidating Mouse Groups")
    print("="*70 + "\n")

    # Update Surgery Template (ID: 1)
    surgery_success = update_template(1, SURGERY_TEMPLATE)

    # Update Behavior Template (ID: 2)
    behavior_success = update_template(2, BEHAVIOR_TEMPLATE)

    print("\n" + "="*70)
    print("Summary")
    print("="*70)

    if surgery_success and behavior_success:
        print("\n✓ All templates updated successfully!")
        print("\nChanges:")
        print("  Surgery Template:")
        print("    - Removed: Mouse 1 & Mouse 2 groups")
        print("    - Added: Single 'Subject/Mouse Details' group")
        print("    - Fields: Subject ID, Strain, Cage ID, Genotype, Sex, DOB, Weight, Negate ML, Notes")
        print("\n  Behavior Template:")
        print("    - Removed: Mouse 1 & Mouse 2 Result groups")
        print("    - Added: Single 'Subject Details' group")
        print("    - Fields: Subject ID, Weight, Reward Consumed, Shock Intensity, Box Number, Notes")
        print("\nNote: For multiple subjects, create one experiment per subject")
        print("      or use a text field to record multiple subject IDs")
    else:
        print("\n✗ Some templates failed to update")
        sys.exit(1)


if __name__ == "__main__":
    main()
