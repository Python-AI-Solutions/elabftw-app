# eLabFTW Local Development Deployment

## Quick Start

`deploy-local.py` wipes any existing stack by default, boots the local HTTPS docker-compose stack, and seeds a deterministic sysadmin account so you can log in immediately.

## Get Started

```bash
uv run python deploy-local.py
```
- add `--keep` to reuse existing containers/volumes instead of calling `docker compose down -v`
- add `--refresh-config` to redownload the upstream `docker-compose.yml`

What the script does:

- downloads/patches the official `docker-compose.yml` for HTTPS on `https://localhost:3148`
- wipes containers/volumes (unless `--keep`) and runs `docker compose up -d`
- waits for the `elabftw` container to report healthy, then runs `bin/init db:install` (idempotent)
- upserts the sysadmin account with deterministic credentials (override via `ELABFTW_DEFAULT_*` env vars):
  - email `admin@localhost`
  - password `elabftw123`
  - API token `Local Dev Token` with fixed body (`ELABFTW_DEFAULT_API_TOKEN_BODY`)
- renames the database container to `elabftw-mysql` (override with `ELABFTW_MYSQL_CONTAINER`) to avoid conflicts on shared Docker hosts
- rewrites `.env` so `ELABFTW_API_KEY`, `ELABFTW_URL=https://localhost:3148`, and `ELABFTW_VERIFY_SSL=false` match the running stack

## Daily Use

- open `https://localhost:3148`, accept the self‑signed certificate warning, and log in with the credentials above
- rerun the script any time; use `--keep` if you want to preserve existing data
- useful commands:
  ```bash
  docker compose ps          # show status
  docker compose logs -f     # tail logs
  docker compose down        # stop containers (keep data)
  docker compose down -v     # stop and wipe all data
  ```

## Notes

- First boot can take a minute while MySQL and PHP warm up; the script polls until the `elabftw` container reports healthy (or times out with a warning).
- Credentials are idempotent: rerunning the script resets the password/token to the deterministic values unless you override them via environment variables.

For production installs or deeper configuration, see the upstream docs: https://doc.elabftw.net
