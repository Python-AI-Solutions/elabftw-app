#!/usr/bin/env python3
"""
Create admin user for eLabFTW
"""

import subprocess
import sys
import shlex
import tempfile
import os


def run_command(cmd, capture_output=True, check=True):
    """Run a shell command and return result"""
    result = subprocess.run(
        cmd, shell=True, capture_output=capture_output, text=True, check=False
    )
    if check and result.returncode != 0:
        print(f"ERROR: Command failed: {cmd}")
        if result.stderr:
            print(result.stderr)
        sys.exit(1)
    return result


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


def create_admin_user():
    """Create a test admin user directly in the database."""
    print("\n>> Creating admin account...")

    email = "admin@localhost"
    password = os.environ.get("ELABFTW_TEST_PASSWORD", "elabftw123")

    # Get MySQL password from container
    mysql_pass_result = run_command(
        'docker exec mysql sh -c "echo $MYSQL_PASSWORD"', check=False
    )
    mysql_password = mysql_pass_result.stdout.strip()

    if not mysql_password:
        print("ERROR: Could not get MySQL password from container")
        sys.exit(1)

    # Check if user already exists
    existing_user = mysql_query(
        mysql_password, f"SELECT userid FROM users WHERE email = '{email}' LIMIT 1;"
    )

    if existing_user.returncode != 0:
        print("ERROR: Failed to check existing users in the database.")
        sys.exit(1)

    if existing_user.returncode == 0 and existing_user.stdout.strip():
        userid = existing_user.stdout.strip()
        print(f"INFO: User already exists (ID: {userid}).")
        print(">> Use your existing credentials to log in.")
        print(f"   Email: {email}")
        print(f"   Password: elabftw123")
        return

    # Generate password hash using PHP (same as eLabFTW uses)
    print(">> Generating password hash...")
    hash_cmd = (
        f"docker exec -e PASSWORD={shlex.quote(password)} elabftw "
        "php -r \"echo password_hash(getenv('PASSWORD'), PASSWORD_DEFAULT);\""
    )
    hash_result = run_command(hash_cmd, check=False)
    if hash_result.returncode != 0 or not hash_result.stdout.strip():
        print("ERROR: Failed to generate password hash.")
        sys.exit(1)

    password_hash = hash_result.stdout.strip()

    print(">> Inserting user into database...")
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

    tmp_file_path = None
    try:
        with tempfile.NamedTemporaryFile("w", delete=False) as tmp_file:
            tmp_file.write(sql_content)
            tmp_file_path = tmp_file.name

        run_command(
            f"docker cp {shlex.quote(tmp_file_path)} mysql:/tmp/create_admin_user.sql",
            capture_output=False,
        )

        insert_result = run_command(
            'docker exec mysql sh -c \'MYSQL_PWD="$MYSQL_PASSWORD" '
            "mysql -uelabftw elabftw < /tmp/create_admin_user.sql'",
            capture_output=False,
            check=False,
        )

        if insert_result.returncode != 0:
            print("ERROR: Failed to insert user into database.")
            sys.exit(1)

    finally:
        if tmp_file_path and os.path.exists(tmp_file_path):
            os.unlink(tmp_file_path)
        run_command(
            "docker exec mysql rm -f /tmp/create_admin_user.sql",
            capture_output=False,
            check=False,
        )

    print("SUCCESS: Admin account created successfully!")
    print(f"   Email:    {email}")
    print(f"   Password: {password}")
    print("\nAccess at: https://localhost:3148")


if __name__ == "__main__":
    create_admin_user()
