#!/usr/bin/env python3
"""
eLabFTW Local Development Deployment Script
Downloads official docker-compose.yml and configures it for easy local access
"""

import json
import os
import secrets
import shlex
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path
import re


TOKEN_CACHE_PATH = Path(__file__).resolve().parent / ".elabftw_api_token.json"


def run_command(cmd, capture_output=True, check=True):
    """Run a shell command and return result"""
    result = subprocess.run(
        cmd, shell=True, capture_output=capture_output, text=True, check=False
    )
    if check and result.returncode != 0:
        print(f"❌ Command failed: {cmd}")
        if result.stderr:
            print(result.stderr)
        sys.exit(1)
    return result


def clear_cached_api_token():
    """Remove cached plaintext API token file if present."""
    try:
        TOKEN_CACHE_PATH.unlink()
    except FileNotFoundError:
        pass
    except OSError as exc:
        print(f"   ⚠️  Unable to delete cached API token: {exc}")


def check_existing_deployment():
    """Check for existing containers and volumes, return whether to skip download"""
    import time

    print("🔍 Checking for existing deployment...")

    # Check for volumes FIRST (before running compose down)
    result = run_command("docker volume ls --format '{{.Name}}'", check=False)
    volumes = [line for line in result.stdout.splitlines() if "elabftw" in line]

    # Check for containers
    result = run_command("docker ps -a --format '{{.Names}}'", check=False)
    containers = [
        line
        for line in result.stdout.splitlines()
        if "elabftw" in line or "mysql" in line
    ]

    if volumes:
        print("\n⚠️  Existing eLabFTW deployment detected!\n")

        if volumes:
            print("   Volumes found (contains your data & passwords):")
            for volume in volumes:
                print(f"     - {volume}")
            print()

        if containers:
            print("   Containers found:")
            for container in containers:
                print(f"     - {container}")
            print()

        print("Options:")
        print(
            "  1) Keep existing data and restart (preserves registration & passwords)"
        )
        print("  2) Wipe everything and start fresh (⚠️  DELETES ALL DATA)")
        print("  3) Cancel deployment")
        print()

        choice = input("Choose option [1/2/3]: ").strip()

        if choice == "1":
            print("\n✅ Keeping existing deployment...")

            # Stop containers but keep volumes
            if containers:
                print("   Stopping existing containers...")
                for container in containers:
                    run_command(
                        f"docker stop {container} 2>/dev/null || true", check=False
                    )
                    run_command(
                        f"docker rm {container} 2>/dev/null || true", check=False
                    )
                time.sleep(1)

            print("   ✅ Existing data preserved! (including passwords)")
            return True  # Skip download to preserve passwords

        elif choice == "2":
            print("\n🗑️  Removing existing deployment...")

            # Stop containers first
            for container in containers:
                print(f"   Removing container {container}...")
                run_command(
                    f"docker rm -f {container} 2>/dev/null || true", check=False
                )

            time.sleep(1)

            # Remove volumes
            for volume in volumes:
                print(f"   Removing volume {volume}...")
                run_command(
                    f"docker volume rm -f {volume} 2>/dev/null || true", check=False
                )

            # Remove networks
            run_command(
                "docker network rm elabftw_elabftw-net 2>/dev/null || true", check=False
            )

            print("⏳ Waiting for cleanup to complete...")
            time.sleep(2)
            print("✅ Cleanup complete!\n")
            clear_cached_api_token()
            return False  # Proceed with full deployment

        elif choice == "3":
            print("\n❌ Deployment cancelled.")
            sys.exit(0)

        else:
            print("\n❌ Invalid option. Deployment cancelled.")
            sys.exit(1)

    # No existing deployment found
    return False  # Proceed with full deployment


def show_startup_banner():
    """Display startup banner"""
    print("\n" + "=" * 70)
    print("🧪 eLabFTW Local Development Deployment")
    print("=" * 70)
    print()


def download_compose_file():
    """Download official docker-compose.yml"""
    print("📥 Downloading official docker-compose.yml from get.elabftw.net...")
    url = "https://get.elabftw.net/?config"

    try:
        with urllib.request.urlopen(url) as response:
            content = response.read().decode("utf-8")

        with open("docker-compose.yml", "w") as f:
            f.write(content)

        print("   ✅ Downloaded successfully")
        return content
    except Exception as e:
        print(f"   ❌ Failed to download: {e}")
        sys.exit(1)


def configure_for_local():
    """Modify docker-compose.yml for local development"""
    print("\n🔧 Configuring for local development...")

    with open("docker-compose.yml", "r") as f:
        content = f.read()

    # 1. Keep HTTPS enabled (default) - self-signed certs will be generated
    # Don't set DISABLE_HTTPS - let it use the default (false)

    # 2. Add port 3148 for HTTPS access
    # Find the line with '443:443' and add 3148:443 before it
    content = re.sub(
        r"(\s+)(- '443:443')",
        r"\1- '3148:443'\n\1\2",
        content,
        count=1,  # Only replace the first occurrence
    )

    # 3. Set SITE_URL for localhost with HTTPS
    content = re.sub(
        r"(\s+- SITE_URL=)$", r"\1https://localhost:3148", content, flags=re.MULTILINE
    )

    # 4. Convert bind mounts to Docker named volumes for local dev
    # Replace /var/elabftw/web:/elabftw/uploads with named volume
    content = re.sub(
        r"(\s+)- /var/elabftw/web:/elabftw/uploads",
        r"\1- elabftw_web:/elabftw/uploads",
        content,
    )

    # Replace /var/elabftw/mysql:/var/lib/mysql with named volume
    content = re.sub(
        r"(\s+)- /var/elabftw/mysql:/var/lib/mysql",
        r"\1- elabftw_mysql:/var/lib/mysql",
        content,
    )

    # 5. Ensure volumes section exists at top level (same level as 'networks' and 'services')
    # Check if there's already a volumes section
    if not re.search(r"^volumes:\s*$", content, re.MULTILINE):
        # Find the end of the file, after networks section
        # Add volumes section at the same indentation level as networks/services
        content = content.rstrip() + "\n\nvolumes:\n  elabftw_web:\n  elabftw_mysql:\n"
    else:
        # If volumes section exists, ensure our volumes are defined
        if "elabftw_web:" not in content:
            content = re.sub(
                r"(^volumes:)",
                r"\1\n  elabftw_web:\n  elabftw_mysql:",
                content,
                flags=re.MULTILINE,
            )

    with open("docker-compose.yml", "w") as f:
        f.write(content)

    # Validate the compose file
    result = run_command("docker compose config > /dev/null 2>&1", check=False)
    if result.returncode != 0:
        print("⚠️  Warning: Generated compose file may have issues")
        print("   Running docker compose config to check...")
        run_command("docker compose config", check=False)

    print("✅ Configuration complete!")
    print("   - HTTPS mode with self-signed certificates")
    print("   - Port 3148 → HTTPS access")
    print("   - SITE_URL → https://localhost:3148")
    print("   - SERVER_NAME → localhost")
    print("   - Using Docker named volumes (Mac-friendly)")


def start_containers():
    """Start Docker containers"""
    print("\n📦 Starting Docker containers...")
    print("   This may take 2-5 minutes for MySQL first-time initialization...")
    result = run_command("docker compose up -d", capture_output=False, check=False)

    if result.returncode != 0:
        print("\n❌ Failed to start containers.")
        print("\n💡 Troubleshooting:")
        print("   1. Check docker-compose.yml was created correctly")
        print("   2. Try: docker compose config")
        print("   3. Try: docker compose down -v && python3 deploy-local.py")
        sys.exit(1)


def wait_for_services_ready(timeout=180, interval=3):
    """Wait until MySQL and eLabFTW containers are ready; return (ready, mysql_password)."""
    import time

    print("   ⏳ Waiting for services to be ready...")

    start = time.time()

    while time.time() - start < timeout:
        mysql_ping = run_command(
            "docker exec mysql sh -c 'MYSQL_PWD=\"$MYSQL_PASSWORD\" mysqladmin ping -uelabftw --silent' >/dev/null 2>&1",
            capture_output=False,
            check=False,
        )

        health_result = run_command(
            "docker inspect elabftw --format='{{.State.Health.Status}}'", check=False
        )

        mysql_ready = mysql_ping.returncode == 0
        elab_ready = (
            health_result.returncode == 0 and health_result.stdout.strip() == "healthy"
        )

        if mysql_ready and elab_ready:
            mysql_pass_result = run_command(
                "docker exec mysql sh -c 'echo $MYSQL_PASSWORD'", check=False
            )
            mysql_password = mysql_pass_result.stdout.strip()
            if mysql_password:
                print("   ✅ All services ready!")
                return True, mysql_password

        time.sleep(interval)

    print("   ⚠️  Timeout waiting for services")
    return False, None


def mysql_query(mysql_password, query, capture_output=True):
    """Execute a MySQL query inside the mysql container."""
    flags = "-N -B" if capture_output else ""
    cmd = (
        "docker exec mysql mysql "
        "-uelabftw "
        f"--password={shlex.quote(mysql_password)} "
        f"elabftw {flags} -e {shlex.quote(query)}"
    )
    return run_command(cmd, capture_output=capture_output, check=False)


def execute_mysql_script(sql_content):
    """Execute multiline SQL inside mysql container using a temporary script file."""
    tmp_file_path = None
    remote_path = None
    try:
        with tempfile.NamedTemporaryFile("w", delete=False) as tmp_file:
            tmp_file.write(sql_content)
            tmp_file_path = tmp_file.name

        remote_path = f"/tmp/{os.path.basename(tmp_file_path)}.sql"
        run_command(
            f"docker cp {shlex.quote(tmp_file_path)} mysql:{shlex.quote(remote_path)}",
            capture_output=False,
        )

        result = run_command(
            f"docker exec mysql sh -c 'MYSQL_PWD=\"$MYSQL_PASSWORD\" "
            f"mysql -uelabftw elabftw < {shlex.quote(remote_path)}'",
            capture_output=False,
            check=False,
        )
        return result.returncode == 0
    finally:
        if tmp_file_path and os.path.exists(tmp_file_path):
            os.unlink(tmp_file_path)
        if remote_path:
            run_command(
                f"docker exec mysql rm -f {shlex.quote(remote_path)}",
                capture_output=False,
                check=False,
            )


def cache_api_token(token_value, token_name):
    """Persist plaintext token locally so we can re-display it on reuse."""
    try:
        TOKEN_CACHE_PATH.write_text(
            json.dumps({"token": token_value, "name": token_name})
        )
    except OSError as exc:
        print(f"   ⚠️  Failed to cache API token locally: {exc}")


def load_cached_api_token():
    """Return cached token dict if available."""
    try:
        content = TOKEN_CACHE_PATH.read_text()
        data = json.loads(content)
        if isinstance(data, dict) and "token" in data:
            return {"token": data.get("token"), "name": data.get("name")}
    except FileNotFoundError:
        return None
    except (json.JSONDecodeError, OSError) as exc:
        print(f"   ⚠️  Failed to read cached API token: {exc}")
    return None


def create_api_token_entry(mysql_password, userid, team_id, token_name, token_value=None):
    """Create a read/write API token for the specified user and return plaintext."""
    token_value = token_value or secrets.token_hex(32)

    hash_cmd = (
        f"docker exec -e APITOKEN={shlex.quote(token_value)} elabftw "
        "php -r \"echo password_hash(getenv('APITOKEN'), PASSWORD_BCRYPT);\""
    )
    hash_result = run_command(hash_cmd, check=False)
    if hash_result.returncode != 0 or not hash_result.stdout.strip():
        print("   ⚠️  Failed to generate API token hash.")
        return {"token": None, "name": token_name}

    token_hash = hash_result.stdout.strip()
    token_name_sql = token_name.replace("'", "''")

    sql_content = f"""
DELETE FROM api_keys WHERE userid = {userid} AND name = '{token_name_sql}';

INSERT INTO api_keys (name, hash, can_write, userid, team)
VALUES ('{token_name_sql}', '{token_hash}', 1, {userid}, {team_id});
"""

    if not execute_mysql_script(sql_content):
        print("   ⚠️  Failed to store API token in database.")
        return {"token": None, "name": token_name}

    key_lookup = mysql_query(
        mysql_password,
        f"SELECT id FROM api_keys WHERE userid = {userid} AND name = '{token_name_sql}' "
        "ORDER BY id DESC LIMIT 1;",
    )
    if key_lookup.returncode == 0 and key_lookup.stdout.strip():
        key_id = key_lookup.stdout.strip()
        full_token = f"{key_id}-{token_value}"
    else:
        print("   ⚠️  Unable to determine API token id; returning raw token value.")
        full_token = token_value

    cache_api_token(full_token, token_name)
    return {"token": full_token, "name": token_name}


def create_test_user():
    """Create or refresh the local sysadmin account and its API token."""
    print("\n👤 Creating test admin account...")

    email = "admin@localhost"
    password = os.environ.get("ELABFTW_TEST_PASSWORD", "elabftw123")
    using_custom_password = "ELABFTW_TEST_PASSWORD" in os.environ

    ready, mysql_password = wait_for_services_ready()
    if not ready or not mysql_password:
        print("   ❌ Services not ready in time - please register manually if needed.")
        return {"status": "failed", "email": email}

    user_query = mysql_query(
        mysql_password, f"SELECT userid FROM users WHERE email = '{email}' LIMIT 1;"
    )
    if user_query.returncode != 0:
        print("   ❌ Failed to check existing users in the database.")
        return {"status": "failed", "email": email}

    userid = user_query.stdout.strip()
    user_status = "exists" if userid else "created"

    if userid:
        print(f"   ℹ️  User already exists (ID: {userid}). Refreshing settings.")

    if not userid:
        print("   🔐 Generating password hash...")
        hash_cmd = (
            f"docker exec -e PASSWORD={shlex.quote(password)} elabftw "
            "php -r \"echo password_hash(getenv('PASSWORD'), PASSWORD_DEFAULT);\""
        )
        hash_result = run_command(hash_cmd, check=False)
        if hash_result.returncode != 0 or not hash_result.stdout.strip():
            print("   ❌ Failed to generate password hash.")
            return {"status": "failed", "email": email}

        password_hash = hash_result.stdout.strip()

        print("   📝 Inserting user into database...")
        sql_content = f"""INSERT INTO users (
    email, password_hash, firstname, lastname,
    validated, is_sysadmin, lang, default_read, default_write
) VALUES (
    '{email}',
    '{password_hash}',
    'Admin',
    'User',
    1,
    1,
    'en_GB',
    JSON_OBJECT('base', 20, 'book', false, 'teams', JSON_ARRAY(), 'users', JSON_ARRAY(), 'teamgroups', JSON_ARRAY()),
    JSON_OBJECT('base', 20, 'book', false, 'teams', JSON_ARRAY(), 'users', JSON_ARRAY(), 'teamgroups', JSON_ARRAY())
);

SET @user_id := (SELECT userid FROM users WHERE email = '{email}' LIMIT 1);

INSERT INTO users2teams (users_id, teams_id, is_admin)
VALUES (@user_id, 1, 1)
ON DUPLICATE KEY UPDATE is_admin=VALUES(is_admin);
"""

        if not execute_mysql_script(sql_content):
            print("   ❌ Failed to insert user into database.")
            return {"status": "failed", "email": email}

        confirm = mysql_query(
            mysql_password, f"SELECT userid FROM users WHERE email = '{email}' LIMIT 1;"
        )
        userid = confirm.stdout.strip() if confirm.returncode == 0 else ""

    if not userid:
        print("   ❌ Unable to determine user ID, aborting token creation.")
        return {"status": "failed", "email": email}

    print(f"   ℹ️  Using user ID {userid}")

    ensure_team_sql = f"""
INSERT INTO users2teams (users_id, teams_id, is_admin)
VALUES ({userid}, 1, 1)
ON DUPLICATE KEY UPDATE is_admin=VALUES(is_admin);
"""
    execute_mysql_script(ensure_team_sql)

    team_lookup = mysql_query(
        mysql_password,
        f"SELECT teams_id FROM users2teams WHERE users_id = {userid} ORDER BY is_admin DESC, teams_id LIMIT 1;",
    )
    team_id = 1
    if team_lookup.returncode == 0 and team_lookup.stdout.strip():
        try:
            team_id = int(team_lookup.stdout.strip())
        except ValueError:
            team_id = 1

    token_name = os.environ.get("ELABFTW_TEST_API_TOKEN_NAME", "Local Dev Token")
    custom_token_value = os.environ.get("ELABFTW_TEST_API_TOKEN")
    regenerate_token = user_status == "created" or custom_token_value is not None

    if custom_token_value:
        print("   🔐 Using custom API token from ELABFTW_TEST_API_TOKEN")

    token_info = {"token": None, "name": token_name}

    if regenerate_token:
        print("   🔄 Generating read/write API token...")
        token_info = create_api_token_entry(
            mysql_password,
            userid,
            team_id,
            token_name,
            token_value=custom_token_value,
        )
    else:
        cached_token = load_cached_api_token()
        if cached_token:
            token_info = cached_token
        else:
            print(
                "   ⚠️  Existing API token reused but value is unknown. "
                "Set ELABFTW_TEST_API_TOKEN to reset."
            )
            token_info = {"token": None, "name": token_name}

    print("   ✅ Test account ready!")
    print(f"   📧 Email:    {email}")
    if using_custom_password:
        print(f"   🔑 Password: {password} (from ELABFTW_TEST_PASSWORD)")
    else:
        print(f"   🔑 Password: {password}")
    if token_info.get("token"):
        print(
            f"   🔐 API Token ({token_info.get('name')}): {token_info.get('token')}"
        )

    return {
        "status": user_status,
        "email": email,
        "password": password,
        "user_id": userid,
        "custom_password": using_custom_password,
        "api_token": token_info.get("token"),
        "api_token_name": token_info.get("name"),
    }


def initialize_database():
    """Initialize the eLabFTW database and create test user"""
    print("\n🗄️  Initializing eLabFTW database...")
    print("   ⏳ Waiting for container to be healthy...")

    import time

    # Wait for elabftw container to be healthy
    max_attempts = 30
    for attempt in range(max_attempts):
        result = run_command(
            "docker inspect elabftw --format='{{.State.Health.Status}}'", check=False
        )
        if result.stdout.strip() == "healthy":
            print("   ✅ eLabFTW container is healthy")
            break
        elif attempt < max_attempts - 1:
            time.sleep(2)
        else:
            print("   ⚠️  Container not yet healthy, proceeding anyway...")

    # Run database initialization
    print("   Running database installation...")
    result = run_command(
        "docker exec elabftw bin/init db:install", capture_output=False, check=False
    )

    if result.returncode == 0:
        print("   ✅ Database initialized successfully!")
    else:
        print("   ℹ️  Database may already be initialized (this is normal)")

    return create_test_user()


def show_completion_message(is_reuse=False, user_info=None):
    """Show success message and access instructions"""
    print("\n" + "=" * 70)
    print("✅ eLabFTW Deployment Complete!")
    print("=" * 70)
    print()
    print("🌐 Access URL:")
    print("   👉 https://localhost:3148")
    print()

    if is_reuse:
        print("♻️  Using Existing Data:")
        print("   • Your previous registration is preserved")
        print("   • All experiments and data are intact")
        print("   • Login with your existing credentials")
        print()
    else:
        print("📝 First Time Setup:")
        print("   1. Accept the self-signed certificate warning")
        print("      (Click 'Advanced' → 'Proceed to localhost')")
        print("   2. Log in with the auto-created admin account (details below)")
        print(
            "   3. Optional: register additional users at https://localhost:3148/register.php"
        )
        print()
        print("   ✅ Accounts persist across restarts!")
        print("   🔄 Run the script again - your account will still be there!")
        print()

    print("⚠️  Certificate Warning:")
    print("   • Self-signed certificate = browser security warning")
    print("   • This is EXPECTED and SAFE for local development")
    print("   • For production, use proper SSL/TLS certificates")
    print()
    if user_info:
        status = user_info.get("status")
        print("👤 Test Account Status:")
        if status not in {"created", "exists"}:
            print("   • Automatic creation failed - register manually if needed")
        else:
            if status == "created":
                print("   • Auto-created admin account is ready")
            else:
                print("   • Existing admin account detected (settings refreshed)")
            print(f"   • Email:    {user_info.get('email')}")
            password_hint = user_info.get("password")
            if user_info.get("custom_password"):
                print(f"   • Password: {password_hint} (set via ELABFTW_TEST_PASSWORD)")
            else:
                print(f"   • Password: {password_hint}")
            token_value = user_info.get("api_token")
            token_name = user_info.get("api_token_name")
            if token_value:
                label = token_name or "API Token"
                print(f"   • {label}: {token_value}")
        print()

    print("💡 Useful Commands:")
    print("   📊 View logs:        docker compose logs -f")
    print("   🔍 Check status:     docker compose ps")
    print("   🔄 Restart:          docker compose restart")
    print("   🛑 Stop (keep data): docker compose down")
    print("   🗑️  Full wipe:        docker compose down -v && rm docker-compose.yml")
    print()
    print("📚 Documentation: https://doc.elabftw.net")
    print("=" * 70)


def main():
    """Main deployment workflow"""
    try:
        # Show startup banner
        show_startup_banner()

        # Check for existing deployment and determine if we should skip download
        skip_download = check_existing_deployment()

        if not skip_download:
            # Download the official compose file
            download_compose_file()

            # Configure for local development
            configure_for_local()
        else:
            print("\n♻️  Using existing configuration...")
            print("   Skipping download and configuration to preserve passwords")

            # Check if docker-compose.yml exists
            if not os.path.exists("docker-compose.yml"):
                print("   ⚠️  Warning: docker-compose.yml not found, downloading...")
                download_compose_file()
                configure_for_local()
                print("   ⚠️  Note: Passwords may have changed, connection might fail")
                skip_download = False  # Treat as new deployment

        user_info = None

        # Start the containers
        start_containers()

        if not skip_download:
            # Initialize the database (only on fresh deployment)
            user_info = initialize_database()
        else:
            print("\n✅ Using existing database (with your previous registration)")
            user_info = create_test_user()

        # Show completion message
        show_completion_message(skip_download, user_info)

    except KeyboardInterrupt:
        print("\n\n❌ Deployment cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
