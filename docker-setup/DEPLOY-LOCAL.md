# eLabFTW Local Development Deployment

## Quick Start

`deploy-local.py` spins up a local HTTPS stack with Docker and seeds it with a sysadmin account so you can log in immediately.

## Get Started

```bash
uv run python deploy-local.py
```

What the script does:

- pulls the official `docker-compose.yml` and tweaks it for HTTPS on `https://localhost:3148`
- switches persistent data to Docker volumes (`elabftw_elabftw_mysql`, `elabftw_elabftw_web`)
- runs `docker compose up -d` and waits for MySQL + eLabFTW to be ready
- runs `bin/init db:install` on first boot
- creates or verifies the test sysadmin account:
  - email `admin@localhost`
  - password `elabftw123` (override with `ELABFTW_TEST_PASSWORD`)
  - read/write API token printed to the console (`Local Dev Token` by default; override the value with `ELABFTW_TEST_API_TOKEN` and its label with `ELABFTW_TEST_API_TOKEN_NAME`)

## Daily Use

- open `https://localhost:3148`, accept the self‑signed certificate warning, and log in with the credentials above
- rerun the script any time; choose to keep or wipe existing volumes when prompted
- useful commands:
  ```bash
  docker compose ps          # show status
  docker compose logs -f     # tail logs
  docker compose down        # stop containers (keep data)
  docker compose down -v     # stop and wipe all data
  ```

## Notes

- The health checks can take a minute on first boot; the script waits before seeding the user.
- If the admin account already exists your password is left untouched; the script will just report the user ID.

For production installs or deeper configuration, see the upstream docs: https://doc.elabftw.net
