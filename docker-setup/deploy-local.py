#!/usr/bin/env python3
"""
One-button bootstrap for the eLabFTW local stack.

Steps:
1. Optionally refresh docker-compose.yml with local tweaks.
2. Wipe existing containers/volumes (skip with --keep).
3. Start docker compose and wait for the PHP container to be healthy.
4. Run bin/init db:install (idempotent).
5. Upsert deterministic sysadmin + API token.
6. Sync .env with matching credentials.
"""

from __future__ import annotations

import argparse
import os
import textwrap
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
import tempfile
import re

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
COMPOSE_FILE = BASE_DIR / "docker-compose.yml"
ENV_FILE = BASE_DIR / ".env"

DEFAULT_EMAIL = os.environ.get("ELABFTW_DEFAULT_EMAIL", "admin@localhost")
DEFAULT_PASSWORD = os.environ.get("ELABFTW_DEFAULT_PASSWORD", "elabftw123")
DEFAULT_FIRSTNAME = os.environ.get("ELABFTW_DEFAULT_FIRSTNAME", "Admin")
DEFAULT_LASTNAME = os.environ.get("ELABFTW_DEFAULT_LASTNAME", "User")
DEFAULT_LANG = os.environ.get("ELABFTW_DEFAULT_LANG", "en_GB")
DEFAULT_TOKEN_NAME = os.environ.get("ELABFTW_DEFAULT_API_TOKEN_NAME", "Local Dev Token")
DEFAULT_TOKEN_BODY = os.environ.get(
    "ELABFTW_DEFAULT_API_TOKEN_BODY",
    "a1c670a35459b11fd1ce468b3d512d4d6a83aa6d9f91c55088cd3bc47421dc199b43a72b86eb862b28892",
)
SITE_URL = os.environ.get("ELABFTW_SITE_URL", "https://localhost:3148")
VERIFY_SSL = os.environ.get("ELABFTW_VERIFY_SSL", "false")

PHP_CONTAINER = os.environ.get("ELABFTW_PHP_CONTAINER", "elabftw")
MYSQL_CONTAINER = os.environ.get("ELABFTW_MYSQL_CONTAINER", "elabftw-mysql")

JSON_PERMS = (
    "JSON_OBJECT("
    "'base', 20, "
    "'book', false, "
    "'teams', JSON_ARRAY(), "
    "'users', JSON_ARRAY(), "
    "'teamgroups', JSON_ARRAY()"
    ")"
)


# ---------------------------------------------------------------------------
# Shell helpers
# ---------------------------------------------------------------------------

def run(cmd: str, *, check: bool = True, capture: bool = True) -> subprocess.CompletedProcess[str]:
    """Run shell command rooted in BASE_DIR."""
    result = subprocess.run(
        cmd,
        shell=True,
        cwd=str(BASE_DIR),
        text=True,
        capture_output=capture,
    )
    if check and result.returncode != 0:
        sys.stderr.write(f"\n❌ Command failed: {cmd}\n")
        if result.stderr:
            sys.stderr.write(result.stderr + "\n")
        sys.exit(result.returncode)
    return result


def download_compose(force: bool) -> None:
    if COMPOSE_FILE.exists() and not force:
        return
    print("📥 Fetching docker-compose.yml from get.elabftw.net ...")
    url = "https://get.elabftw.net/?config"
    try:
        with urllib.request.urlopen(url) as resp:
            content = resp.read().decode("utf-8")
    except Exception as exc:  # pragma: no cover - network failure
        sys.stderr.write(f"❌ Unable to download compose file: {exc}\n")
        sys.exit(1)
    COMPOSE_FILE.write_text(content)
    print("   ✅ Saved compose file.")


def configure_compose() -> None:
    content = COMPOSE_FILE.read_text()

    content = re.sub(
        r"(\s+)(- '443:443')",
        r"\1- '3148:443'\n\1\2",
        content,
        count=1,
    )
    content = re.sub(
        r"(\s+- SITE_URL=).*$",
        rf"\1{SITE_URL}",
        content,
        flags=re.MULTILINE,
    )
    content = re.sub(
        r"(\s+)- /var/elabftw/web:/elabftw/uploads",
        r"\1- elabftw_web:/elabftw/uploads",
        content,
    )
    content = re.sub(
        r"(\s+)- /var/elabftw/mysql:/var/lib/mysql",
        r"\1- elabftw_mysql:/var/lib/mysql",
        content,
    )

    # ensure mysql container name matches expectation
    content = re.sub(
        r"(container_name:\s*)mysql",
        rf"\1{MYSQL_CONTAINER}",
        content,
    )

    if not re.search(r"^volumes:\s*$", content, re.MULTILINE):
        content = content.rstrip() + "\n\nvolumes:\n  elabftw_web:\n  elabftw_mysql:\n"

    COMPOSE_FILE.write_text(content)


def wait_for_health(container: str, timeout: int = 180) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        status = run(
            f"docker inspect {container} --format='{{{{.State.Health.Status}}}}'",
            capture=True,
            check=False,
        )
        if status.returncode == 0 and status.stdout.strip() == "healthy":
            return
        time.sleep(3)
    print(f"⚠️  {container} did not become healthy within {timeout}s – continuing anyway.")


def php_hash(value: str) -> str:
    hashed = run(
        f"docker exec {PHP_CONTAINER} php -r \"echo password_hash('{value}', PASSWORD_DEFAULT);\"",
        capture=True,
        check=False,
    )
    if hashed.returncode != 0 or not hashed.stdout.strip():
        sys.stderr.write("❌ Unable to compute password hash via PHP container.\n")
        sys.exit(1)
    return hashed.stdout.strip()


def get_mysql_password() -> str:
    result = run(
        f"docker exec {MYSQL_CONTAINER} sh -c 'echo \"$MYSQL_PASSWORD\"'",
        capture=True,
        check=False,
    )
    if result.returncode != 0 or not result.stdout.strip():
        sys.stderr.write("❌ Unable to read MYSQL_PASSWORD from mysql container.\n")
        sys.exit(1)
    return result.stdout.strip()


def run_mysql(sql: str, mysql_password: str) -> subprocess.CompletedProcess[str]:
    with tempfile.NamedTemporaryFile("w", delete=False) as tmp:
        tmp.write(sql)
        tmp_path = Path(tmp.name)

    remote = f"/tmp/{tmp_path.name}.sql"
    pw = mysql_password.replace("'", "'\"'\"'")
    try:
        run(f"docker cp {tmp_path} {MYSQL_CONTAINER}:{remote}")
        result = run(
            f"docker exec {MYSQL_CONTAINER} bash -lc "
            f"\"MYSQL_PWD='{pw}' mysql -N -B -uelabftw elabftw < {remote}\"",
            capture=True,
            check=False,
        )
    finally:
        try:
            tmp_path.unlink()
        except OSError:
            pass
        run(
            f"docker exec {MYSQL_CONTAINER} rm -f {remote}",
            capture=False,
            check=False,
        )
    return result


def provision_credentials(mysql_password: str) -> tuple[str, str]:
    password_hash = php_hash(DEFAULT_PASSWORD)
    token_hash = php_hash(DEFAULT_TOKEN_BODY)

    email_sql = DEFAULT_EMAIL.replace("'", "''")
    fname_sql = DEFAULT_FIRSTNAME.replace("'", "''")
    lname_sql = DEFAULT_LASTNAME.replace("'", "''")
    token_name_sql = DEFAULT_TOKEN_NAME.replace("'", "''")

    sql = textwrap.dedent(
        f"""
        SET @password_hash := '{password_hash}';
        SET @token_hash := '{token_hash}';
        SET @token_body := '{DEFAULT_TOKEN_BODY}';
        SET @token_name := '{token_name_sql}';
        SET @lang := '{DEFAULT_LANG}';

        INSERT INTO users (email, password_hash, firstname, lastname, validated, is_sysadmin, lang, default_read, default_write)
        VALUES ('{email_sql}', @password_hash, '{fname_sql}', '{lname_sql}', 1, 1, @lang, {JSON_PERMS}, {JSON_PERMS})
        ON DUPLICATE KEY UPDATE
            password_hash = @password_hash,
            firstname = VALUES(firstname),
            lastname = VALUES(lastname),
            validated = 1,
            is_sysadmin = 1,
            lang = @lang,
            default_read = {JSON_PERMS},
            default_write = {JSON_PERMS};

        SELECT @userid := userid FROM users WHERE email = '{email_sql}' LIMIT 1;

        INSERT INTO users2teams (users_id, teams_id, is_admin)
        VALUES (@userid, 1, 1)
        ON DUPLICATE KEY UPDATE is_admin = VALUES(is_admin);

        INSERT INTO api_keys (name, hash, can_write, userid, team)
        VALUES (@token_name, @token_hash, 1, @userid, 1)
        ON DUPLICATE KEY UPDATE hash = @token_hash, can_write = 1, team = 1;

        SELECT @userid AS user_id, id AS token_id
        FROM api_keys
        WHERE userid = @userid AND name = @token_name
        LIMIT 1;
        """
    )

    result = run_mysql(sql, mysql_password)
    if result.returncode != 0:
        sys.stderr.write("❌ Failed to configure database credentials:\n")
        sys.stderr.write(result.stderr)
        sys.exit(result.returncode)

    rows = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    if not rows:
        sys.stderr.write("❌ Unable to read user/token ids from SQL output.\n")
        sys.exit(1)

    user_id, token_id = rows[-1].split("\t")
    full_token = f"{token_id}-{DEFAULT_TOKEN_BODY}"
    return user_id, full_token


def update_env_file(api_token: str) -> None:
    desired = {
        "ELABFTW_API_KEY": api_token,
        "ELABFTW_URL": SITE_URL,
        "ELABFTW_VERIFY_SSL": VERIFY_SSL,
        "ELABFTW_MYSQL_HOST": MYSQL_CONTAINER,
    }

    existing: dict[str, str] = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                key, value = line.split("=", 1)
                existing[key] = value

    existing.update(desired)

    lines = [f"{key}={value}" for key, value in existing.items()]
    ENV_FILE.write_text("\n".join(lines).strip() + "\n")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description="Bootstrap eLabFTW docker stack.")
    parser.add_argument(
        "--keep",
        action="store_true",
        help="Reuse existing containers/volumes instead of wiping first.",
    )
    parser.add_argument(
        "--refresh-config",
        action="store_true",
        help="Redownload docker-compose.yml from get.elabftw.net before starting.",
    )
    args = parser.parse_args()

    download_compose(force=args.refresh_config or not COMPOSE_FILE.exists())
    configure_compose()

    if not args.keep:
        print("🧹 Removing any existing containers/volumes (docker compose down -v)...")
        run("docker compose down -v", check=False, capture=False)

    print("🚀 Starting docker compose stack...")
    run("docker compose up -d --remove-orphans", capture=False)

    print("⏳ Waiting for PHP container health check...")
    wait_for_health(PHP_CONTAINER)

    print("🛠️ Running bin/init db:install (idempotent)...")
    run(f"docker exec {PHP_CONTAINER} bin/init db:install", check=False, capture=False)

    mysql_password = get_mysql_password()

    print("🔐 Upserting sysadmin user + API token...")
    user_id, api_token = provision_credentials(mysql_password)

    print("\n✅ Stack ready!")
    print(f"   URL:      {SITE_URL}")
    print(f"   Email:    {DEFAULT_EMAIL}")
    print(f"   Password: {DEFAULT_PASSWORD}")
    print(f"   API Key:  {DEFAULT_TOKEN_NAME} -> {api_token}")

    update_env_file(api_token)
    print(f"   .env updated at {ENV_FILE}")
    print("\nDone ✅")


if __name__ == "__main__":
    main()
