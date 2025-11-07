#!/usr/bin/env python3
"""
Get eLabFTW API Token and Save to .env

This script helps you retrieve your eLabFTW API token and automatically
saves it to the .env file for use with the upload script.

Usage:
    python get_elabftw_token.py

Requirements:
    pip install requests python-dotenv
"""

import os
import sys
from getpass import getpass
from pathlib import Path
from dotenv import load_dotenv, set_key, find_dotenv
import requests


def update_env_file(key, value, env_file_path):
    """
    Update or add a key-value pair in the .env file.

    Args:
        key: Environment variable name
        value: Environment variable value
        env_file_path: Path to the .env file
    """
    env_file = Path(env_file_path)

    # Create .env file if it doesn't exist
    if not env_file.exists():
        env_file.touch()
        print(f"Created new .env file at: {env_file}")

    # Use python-dotenv's set_key function to update/add the value
    set_key(env_file, key, value)
    print(f"✓ Saved {key} to {env_file}")


def check_token_validity(host, token):
    """
    Verify if an API token is valid by testing it against the eLabFTW instance.

    Args:
        host: eLabFTW instance URL
        token: API token to validate

    Returns:
        bool: True if token is valid, False otherwise
    """
    print(f"\nValidating token against {host}...")

    try:
        # Try to access the info endpoint
        response = requests.get(
            f"{host}/api/v2/info",
            headers={"Authorization": token},
            timeout=10
        )

        if response.status_code == 200:
            info = response.json()
            print("✓ Token is VALID")
            print(f"  eLabFTW Version: {info.get('elabftw_version', 'unknown')}")
            print(f"  Instance URL: {host}")
            return True
        elif response.status_code == 401:
            print("✗ Token is INVALID (401 Unauthorized)")
            return False
        else:
            print(f"✗ Token validation failed (Status: {response.status_code})")
            return False

    except requests.exceptions.RequestException as e:
        print(f"✗ Error connecting to eLabFTW: {e}")
        return False


def print_manual_instructions(host):
    """
    Print instructions for manually retrieving an API token from eLabFTW.
    """
    print("\n" + "="*70)
    print("HOW TO GET YOUR API TOKEN")
    print("="*70)
    print(f"\n1. Open your eLabFTW instance in a browser:")
    print(f"   {host}")
    print("\n2. Log in with your credentials")
    print("\n3. Click on your username (top-right corner)")
    print("\n4. Select 'User Control Panel' from the dropdown")
    print("\n5. Navigate to the 'API Keys' tab/section")
    print("\n6. Click 'Generate new API key'")
    print("\n7. Give it a name (e.g., 'ArchiveFlow Upload Script')")
    print("\n8. Copy the generated key")
    print("   Format will look like: 1-abc123def456...")
    print("\n" + "="*70)
    print("\n⚠️  IMPORTANT: The API key is only shown once!")
    print("   Make sure to copy it before closing the page.")
    print("="*70 + "\n")


def main():
    """Main function to guide token retrieval and saving"""

    print("\n" + "="*70)
    print("eLabFTW API TOKEN SETUP")
    print("="*70)

    # Determine .env file location (same directory as this script)
    script_dir = Path(__file__).parent
    env_file = script_dir / '.env'

    # Load existing .env if present
    load_dotenv(env_file)

    # Step 1: Get or confirm eLabFTW host
    print("\n" + "-"*70)
    print("Step 1: eLabFTW Instance URL")
    print("-"*70)

    host = os.getenv('ELABFTW_URL')

    if host:
        print(f"\nFound existing host in .env: {host}")
        change = input("Use this host? (Y/n): ").strip().lower()
        if change == 'n':
            host = None

    if not host:
        print("\nEnter your eLabFTW instance URL")
        print("Examples:")
        print("  - http://localhost:3148/login (local Docker)")
        print("  - https://eln.example.org (production)")
        host = input("\nHost URL: ").strip()

        if not host:
            print("Error: Host URL is required")
            sys.exit(1)

    # Remove trailing slash if present
    host = host.rstrip('/')

    # Save host to .env
    update_env_file('ELABFTW_URL', host, env_file)

    # Step 2: Check for existing token
    print("\n" + "-"*70)
    print("Step 2: API Token")
    print("-"*70)

    existing_token = os.getenv('ELABFTW_API_KEY')
    token_valid = False

    if existing_token:
        print(f"\nFound existing token in .env: {existing_token[:10]}...")

        # Validate the existing token
        token_valid = check_token_validity(host, existing_token)

        if token_valid:
            print("\n✓ Your existing token is valid and working!")
            update = input("\nDo you want to replace it with a new token? (y/N): ").strip().lower()
            if update != 'y':
                print("\n✓ Setup complete! Your .env file is ready to use.")
                print(f"\nConfiguration saved in: {env_file}")
                return

    # Step 3: Get new token
    if not token_valid:
        print("\n" + "-"*70)
        print("Step 3: Retrieve API Token")
        print("-"*70)

        # Show instructions
        print_manual_instructions(host)

        # Prompt for token
        print("After you've generated your API token, paste it below:")
        new_token = getpass("API Token (input hidden): ").strip()

        if not new_token:
            print("\nError: No token entered")
            sys.exit(1)

        # Validate the new token
        is_valid = check_token_validity(host, new_token)

        if not is_valid:
            print("\n✗ Token validation failed")
            print("Please check:")
            print("  - Token was copied correctly (no extra spaces)")
            print("  - eLabFTW instance URL is correct")
            print("  - Token has proper permissions")
            sys.exit(1)

        # Save the valid token
        print("\n" + "-"*70)
        print("Step 4: Save Token")
        print("-"*70)

        update_env_file('ELABFTW_API_KEY', new_token, env_file)

        print("\n" + "="*70)
        print("✓ SETUP COMPLETE!")
        print("="*70)
        print(f"\nYour configuration has been saved to:")
        print(f"  {env_file}")
        print("\nYou can now run the upload script:")
        print("  python upload_to_elabftw.py")
        print("="*70 + "\n")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nError: {e}")
        sys.exit(1)
