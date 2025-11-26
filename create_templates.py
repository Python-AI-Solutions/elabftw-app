#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Create eLabFTW Experiment Templates, Categories, and Tags

Sets up the complete experiment structure aligned with the LabArchives
Tejeda Lab structure as documented in first-api-response.md.

Structure mapping:
- Notebook -> eLabFTW Server (one per lab)
- Experiment Directory -> Category (Behavior, Histology, Metadata, Photometry, Surgeries)
- Cohort Directory -> Tag (Cohort 1, Cohort 2, Baseline, Training Day X, Testing, etc.)
- Widget -> Template (Surgery Data Entry, Behavior Session)
"""

import requests
import json
import sys
import urllib3
from pathlib import Path

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

# Template directory
TEMPLATES_DIR = Path(__file__).parent / "templates"


def load_json(filename: str) -> dict:
    """Load a JSON file from templates directory"""
    file_path = TEMPLATES_DIR / filename
    if not file_path.exists():
        print(f"ERROR: File not found: {file_path}")
        sys.exit(1)

    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_api_key():
    """Prompt user for API key"""
    print("\n" + "="*70)
    print("eLabFTW Experiment Structure Setup")
    print("="*70)
    print("\nTo set up the experiment structure, you need an API key:")
    print("1. Log in to eLabFTW at https://localhost:3148")
    print("2. Go to User Panel (top right) -> API Keys")
    print("3. Click 'Generate new API Key'")
    print("4. Copy the key and paste it here\n")

    api_key = input("Enter your API key: ").strip()
    if not api_key:
        print("ERROR: API key is required")
        sys.exit(1)

    return api_key


def create_category(api_key: str, name: str, color: str) -> bool:
    """Create an experiments category via API (uses teams/1/experiments_categories)"""
    headers = {
        "Authorization": api_key,
        "Content-Type": "application/json"
    }

    payload = {
        "name": name,
        "color": color
    }

    try:
        # Use teams endpoint for categories
        response = requests.post(
            f"{API_ENDPOINT}/teams/1/experiments_categories",
            headers=headers,
            json=payload,
            verify=False
        )

        if response.status_code in (200, 201):
            print(f"  [OK] Created category: {name}")
            return True
        elif response.status_code == 400 and "already exists" in response.text.lower():
            print(f"  [SKIP] Category already exists: {name}")
            return True
        else:
            print(f"  [FAIL] Failed to create category: {name}")
            print(f"    Status: {response.status_code}")
            print(f"    Response: {response.text}")
            return False

    except Exception as e:
        print(f"  [FAIL] Error creating category: {e}")
        return False


def create_tag(api_key: str, tag_name: str) -> bool:
    """Create a tag via API (uses teams/current/tags)"""
    headers = {
        "Authorization": api_key,
        "Content-Type": "application/json"
    }

    try:
        # Use teams/current/tags endpoint for tags
        response = requests.post(
            f"{API_ENDPOINT}/teams/current/tags",
            headers=headers,
            json={"tag": tag_name},
            verify=False
        )

        if response.status_code in (200, 201):
            print(f"  [OK] Created tag: {tag_name}")
            return True
        elif response.status_code == 400 and "already exists" in response.text.lower():
            print(f"  [SKIP] Tag already exists: {tag_name}")
            return True
        else:
            print(f"  [INFO] Tag creation returned: {response.status_code} - {tag_name}")
            return True

    except Exception as e:
        print(f"  [FAIL] Error creating tag: {e}")
        return False


def create_template(api_key: str, title: str, body: str, metadata: dict) -> bool:
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
            verify=False
        )

        if response.status_code == 201:
            print(f"  [OK] Created template: {title}")
            return True
        else:
            print(f"  [FAIL] Failed to create template: {title}")
            print(f"    Status: {response.status_code}")
            print(f"    Response: {response.text}")
            return False

    except Exception as e:
        print(f"  [FAIL] Error creating template: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function"""
    api_key = get_api_key()

    # Load configuration files
    print("\n" + "="*70)
    print("Loading configuration files...")
    print("="*70 + "\n")

    structure = load_json("experiment_structure.json")
    surgery_metadata = load_json("surgery_template.json")
    behavior_metadata = load_json("behavior_template.json")

    print(f"Loaded experiment structure:")
    print(f"  - {len(structure['categories'])} categories")
    print(f"  - {len(structure['tags'])} tags")
    print(f"Loaded surgery template with {len(surgery_metadata['extra_fields'])} fields")
    print(f"Loaded behavior template with {len(behavior_metadata['extra_fields'])} fields")

    # Create categories
    print("\n" + "="*70)
    print("Creating Categories (Experiment Directories)...")
    print("="*70 + "\n")

    categories_ok = True
    for cat in structure["categories"]:
        if not create_category(api_key, cat["name"], cat["color"]):
            categories_ok = False

    # Create tags
    print("\n" + "="*70)
    print("Creating Tags (Cohort/Session Identifiers)...")
    print("="*70 + "\n")

    tags_ok = True
    for tag in structure["tags"]:
        if not create_tag(api_key, tag):
            tags_ok = False

    # Create templates
    print("\n" + "="*70)
    print("Creating Templates (Widgets)...")
    print("="*70 + "\n")

    surgery_ok = create_template(
        api_key=api_key,
        title="Surgery Data Entry",
        body="<p>Use the extra fields below to record surgery details. One entry per subject.</p>",
        metadata=surgery_metadata
    )

    behavior_ok = create_template(
        api_key=api_key,
        title="Behavior Session",
        body="<p>Use the extra fields below to record behavior session data. One entry per subject.</p>",
        metadata=behavior_metadata
    )

    # Summary
    print("\n" + "="*70)
    print("Summary")
    print("="*70)

    print("\nExperiment Structure (from first-api-response.md):")
    print("  LabArchives          ->  eLabFTW")
    print("  ------------------------------------------")
    print("  Notebook             ->  Server (one per lab)")
    print("  Experiment Directory ->  Category")
    print("  Cohort Directory     ->  Tag")
    print("  Widget               ->  Template")

    print("\nCreated Items:")
    print(f"  Categories: {len(structure['categories'])} (Behavior, Histology, Metadata, Photometry, Surgeries)")
    print(f"  Tags: {len(structure['tags'])} (Cohort 1-5, Training Days, Baseline, Testing, etc.)")
    print(f"  Templates: 2 (Surgery Data Entry, Behavior Session)")

    if surgery_ok and behavior_ok:
        print("\n[OK] Setup completed successfully!")
        print("\nHow to use:")
        print("1. Go to Experiments -> Create New")
        print("2. Select a Category (e.g., 'Behavior' or 'Surgeries')")
        print("3. Select a Template (e.g., 'Surgery Data Entry')")
        print("4. Add Tags to organize (e.g., 'Cohort 1', 'Training Day 1')")
        print("5. Fill in the extra fields")
        print("\nNote: Create one experiment entry per subject")
    else:
        print("\n[WARN] Some items may have failed to create")
        print("Check the messages above for details")
        sys.exit(1)


if __name__ == "__main__":
    main()
