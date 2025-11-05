# Quickstart Guide: elabftw-app

**Version**: 1.0
**Date**: 2025-10-27
**Branch**: `heet-dev`
**Audience**: Operators, Developers, Lab Technicians

## Overview

elabftw-app automates the pipeline from Electronic Lab Notebook (ELN) recording through NWB file packaging to DANDI archive upload for fiber photometry behavioral neuroscience experiments. This guide covers:

- **Installation**: Setting up development environment
- **Configuration**: ELN and storage backend setup
- **Running Services**: API, UI, and worker processes
- **First Sync**: Triggering your first ELN synchronization
- **Monitoring**: Using the Streamlit dashboard
- **Troubleshooting**: Common errors and solutions

---

## Prerequisites

Before starting, ensure you have:

### Required Software

- **Python 3.13** (NON-NEGOTIABLE)
  - Download: https://www.python.org/downloads/
  - Verify: `python --version` (must show 3.13.x)
- **pixi** (package manager)
  - Install: `curl -fsSL https://pixi.sh/install.sh | bash` (Linux/macOS)
  - Windows: Download from https://github.com/prefix-dev/pixi/releases
  - Verify: `pixi --version`
- **Git** (version control)
  - Download: https://git-scm.com/downloads
  - Verify: `git --version`
- **Redis** (task queue broker)
  - Linux: `sudo apt-get install redis-server` or `brew install redis`
  - Windows: https://github.com/microsoftarchive/redis/releases
  - Verify: `redis-cli ping` (should return "PONG")

### Required Access

- **ELN Credentials**:
  - LabArchives: API token for NIH instance
  - OR eLabFTW: API key for your instance
- **Storage Access**:
  - Local: Read/write permissions for data directory (e.g., `/storage/experiments`)
  - OneDrive/Box (optional): OAuth2 credentials
- **DANDI Credentials**:
  - DANDI API key (get from https://dandiarchive.org/settings/token)
  - Access to test dandiset (or permission to create one)

---

## Installation

### Step 1: Clone Repository

```bash
git clone https://github.com/your-org/elabftw-app.git
cd elabftw-app
git checkout heet-dev
```

### Step 2: Install Dependencies with pixi

```bash
# Install all dependencies (Python packages, tools, etc.)
pixi install

# Verify installation
pixi list
```

**Important**: Do NOT use `pip`, `conda`, `poetry`, or `pipenv`. All dependencies are managed via `pixi.toml`.

### Step 3: Start Redis

```bash
# Linux/macOS
redis-server

# Windows (if installed as service)
redis-server --service-start

# Verify Redis is running
redis-cli ping  # Should return "PONG"
```

---

## Configuration

### Step 1: Create `.env` File

Copy the template and edit with your credentials:

```bash
cp .env.example .env
```

**`.env` Template**:

```bash
# ELN Configuration (choose ONE backend)
ELN_BACKEND=labarchives  # or "elabftw"

# LabArchives Configuration (if using LabArchives)
LABARCHIVES_TOKEN=your_labarchives_api_token_here
LABARCHIVES_BASE_URL=https://nih.labarchives.com

# eLabFTW Configuration (if using eLabFTW)
ELABFTW_API_KEY=your_elabftw_api_key_here
ELABFTW_BASE_URL=https://elabftw.yourlab.edu

# Storage Configuration
STORAGE_BACKEND=local  # or "onedrive" or "box"
STORAGE_ROOT_PATH=/storage/experiments  # Absolute path to data directory

# OneDrive Configuration (if using OneDrive)
ONEDRIVE_CLIENT_ID=your_client_id
ONEDRIVE_CLIENT_SECRET=your_client_secret
ONEDRIVE_TENANT_ID=your_tenant_id

# Box Configuration (if using Box)
BOX_CLIENT_ID=your_client_id
BOX_CLIENT_SECRET=your_client_secret

# DANDI Configuration
DANDI_API_KEY=your_dandi_api_key_here
DANDI_BASE_URL=https://api.dandiarchive.org/api

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Logging
LOG_LEVEL=INFO  # or DEBUG for verbose logging
LOG_FORMAT=json  # Structured JSON logging
```

**Security Notes**:
- **NEVER commit `.env` to Git** (already in `.gitignore`)
- Store production credentials in secrets manager (AWS Secrets Manager, Azure Key Vault, etc.)
- Use read-only API keys where possible

### Step 2: Verify Storage Directory

```bash
# Create storage root if it doesn't exist
mkdir -p /storage/experiments

# Verify write permissions
touch /storage/experiments/test.txt
rm /storage/experiments/test.txt
```

### Step 3: Test ELN Connection

```bash
# Test LabArchives authentication
pixi run python -c "
from adapters.eln.labarchives.adapter import LabArchivesAdapter
adapter = LabArchivesAdapter()
success, error = adapter.authenticate({'token': 'YOUR_TOKEN'})
print(f'Auth successful: {success}')
"

# OR test eLabFTW authentication
pixi run python -c "
from adapters.eln.elabftw.adapter import ElabFTWAdapter
adapter = ElabFTWAdapter()
success, error = adapter.authenticate({'token': 'YOUR_API_KEY'})
print(f'Auth successful: {success}')
"
```

---

## Running Services

elabftw-app consists of three main services:

1. **FastAPI Backend** (API server)
2. **Streamlit UI** (operator dashboard)
3. **Celery Worker** (background tasks)

### Option 1: Run All Services (Development)

```bash
# Terminal 1: Start API
pixi run api

# Terminal 2: Start UI
pixi run ui

# Terminal 3: Start Worker
pixi run worker
```

### Option 2: Run with Docker Compose (Production-like)

```bash
docker-compose up
```

### Service Endpoints

- **API**: http://localhost:8000
  - Health check: http://localhost:8000/health
  - API docs: http://localhost:8000/docs (Swagger UI)
- **UI**: http://localhost:8501
  - Dashboard homepage

### Verifying Services

```bash
# Check API health
curl http://localhost:8000/health

# Expected response:
# {
#   "status": "healthy",
#   "version": "1.0.0",
#   "components": {
#     "redis": "up",
#     "eln_adapter": "up",
#     "storage_adapter": "up"
#   },
#   "timestamp": "2025-10-27T15:00:00Z"
# }
```

---

## First Sync

### Step 1: Trigger Manual ELN Sync

**Option A: Via API**

```bash
curl -X POST http://localhost:8000/v1/sync \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "your_eln_project_id",
    "since": "2025-10-01T00:00:00Z",
    "force_resync": false
  }'

# Expected response:
# {
#   "accepted": true,
#   "request_id": "req_1730026800_abc123",
#   "message": "Sync job queued successfully"
# }
```

**Option B: Via UI**

1. Navigate to http://localhost:8501
2. Click "Manual Triggers" in sidebar
3. Enter project ID and date range
4. Click "Trigger Sync"

### Step 2: Monitor Sync Progress

**Via API**:

```bash
# Get status for a subject
curl http://localhost:8000/v1/status/M001

# Expected response:
# {
#   "subject_id": "M001",
#   "sessions": [
#     {
#       "session_id": "M001_2025-10-27_fear_conditioning",
#       "current_stage": "awaiting_data",
#       "last_updated": "2025-10-27T09:00:00Z",
#       "error_messages": []
#     }
#   ]
# }
```

**Via UI**:

1. Navigate to "Pipeline Status" page
2. View real-time status for all subjects
3. Color-coded badges indicate stage:
   - 🔵 **eln_synced**: Directory created
   - 🟡 **awaiting_data**: Waiting for data upload
   - 🟠 **preprocessing**: Processing data
   - 🟣 **packaging**: Generating NWB file
   - 🟢 **completed**: Uploaded to DANDI
   - 🔴 **failed**: Error occurred

### Step 3: Upload Raw Data

After sync, the system creates a directory structure:

```
/storage/experiments/M001/behavior/fear_conditioning/2025-10-27/
├── raw/                # ← Upload your data files here
│   ├── TDT_Tank/       # TDT tank folder (entire folder)
│   ├── protocol.csv    # Protocol CSV file
│   └── video_01.mp4    # Video file (optional)
├── processed/          # System-generated files
├── metadata/           # System-generated metadata
└── analysis/           # Analysis outputs
```

**Upload Instructions**:

1. Copy TDT tank folder to `raw/TDT_Tank/`
2. Copy protocol CSV to `raw/protocol.csv`
3. Copy video files to `raw/` (optional)

**Automatic Trigger**:

- File system watcher detects when all required files are present
- Preprocessing task automatically queued
- No manual intervention needed

---

## Monitoring

### Streamlit Dashboard

Navigate to http://localhost:8501

**Dashboard Pages**:

1. **Home**: Overview of pipeline activity
   - Total subjects, sessions, NWB files
   - Recent activity log
   - System health status

2. **Pipeline Status**: Real-time session status
   - Filter by subject, protocol, date range
   - Color-coded stage indicators
   - Error messages (if failed)
   - Click session for details

3. **Subjects**: Subject browser
   - List all subjects with metadata
   - Session count, last session date
   - Click subject for session list

4. **Logs**: Structured log viewer
   - Filter by level (INFO, WARNING, ERROR)
   - Search by request_id, subject_id, entry_id
   - JSON log formatting

5. **Manual Triggers**: Operator interventions
   - Trigger ELN sync
   - Force NWB re-packaging
   - Retry failed uploads

### API Monitoring

```bash
# List all subjects
curl http://localhost:8000/v1/subjects

# Get sessions for a subject
curl http://localhost:8000/v1/sessions/M001

# Get pipeline status
curl http://localhost:8000/v1/status/M001
```

### Celery Monitoring (Optional)

Install Flower (Celery monitoring tool):

```bash
pixi run flower
```

Navigate to http://localhost:5555 for task monitoring.

---

## Manual Interventions

### Force NWB Re-Packaging

**Use Case**: Code changes, metadata corrections, NWB schema updates

**Via API**:

```bash
curl -X POST http://localhost:8000/v1/nwb/package \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "M001_2025-10-27_fear_conditioning",
    "force_repackage": true
  }'
```

**Via UI**:

1. Navigate to "Manual Triggers"
2. Enter session ID
3. Check "Force Re-Package"
4. Click "Trigger Packaging"

### Retry Failed Upload

**Use Case**: Network failures, DANDI API errors

**Via UI**:

1. Navigate to "Pipeline Status"
2. Find failed session
3. Click "Retry Upload" button

---

## Development Workflow

### Running Tests

```bash
# Run all tests (unit + integration + e2e)
pixi run test

# Run only unit tests (fast)
pixi run unit

# Run only integration tests
pixi run integration

# Run only E2E tests (requires credentials)
pixi run e2e

# Run with coverage report
pixi run pytest --cov=app --cov=adapters --cov=nwb --cov=dandi
```

### Linting and Type Checking

```bash
# Lint code (ruff)
pixi run lint

# Format code (ruff format)
pixi run fmt

# Type check (mypy)
pixi run typecheck
```

### Pre-Commit Hooks

```bash
# Install pre-commit hooks
pixi run pre-commit install

# Run manually
pixi run pre-commit run --all-files
```

### Creating a Feature Branch

```bash
# Create new branch from main
git checkout -b feature/my-feature

# Make changes, commit
git add .
git commit -m "feat: add new feature"

# Push to remote
git push -u origin feature/my-feature

# Create pull request on GitHub
```

---

## Troubleshooting

### Issue: API Returns 500 Internal Server Error

**Symptoms**: `curl http://localhost:8000/health` returns 500 error

**Solutions**:

1. Check Redis is running:
   ```bash
   redis-cli ping  # Should return "PONG"
   ```

2. Check logs:
   ```bash
   tail -f logs/api.log
   ```

3. Verify `.env` configuration:
   ```bash
   cat .env | grep -E "REDIS|ELN|STORAGE"
   ```

4. Restart services:
   ```bash
   # Kill all processes
   pkill -f uvicorn
   pkill -f celery

   # Restart
   pixi run api
   pixi run worker
   ```

---

### Issue: ELN Authentication Failed

**Symptoms**: Sync job fails with "Authentication failed" error

**Solutions**:

1. Verify credentials in `.env`:
   ```bash
   # Test LabArchives token
   curl -H "Authorization: Bearer YOUR_TOKEN" \
     https://nih.labarchives.com/api/notebooks

   # Test eLabFTW API key
   curl -H "Authorization: YOUR_API_KEY" \
     https://elabftw.yourlab.edu/api/v2/experiments
   ```

2. Check token expiration (regenerate if expired)

3. Verify base URL is correct:
   - LabArchives NIH: `https://nih.labarchives.com`
   - eLabFTW: Your institution's URL

4. Check ELN backend selection in `.env`:
   ```bash
   ELN_BACKEND=labarchives  # or "elabftw"
   ```

---

### Issue: NWB Validation Failed

**Symptoms**: Pipeline status shows `failed` at `packaging` stage

**Error Messages** (in logs):
- "pynwb validation failed: missing required field 'subject_id'"
- "Invalid species URI"
- "Timestamp format error"

**Solutions**:

1. Check ELN metadata:
   ```bash
   # View parsed metadata
   curl http://localhost:8000/v1/sessions/M001 | jq '.sessions[0].metadata'
   ```

2. Verify required fields are present:
   - `subject_id`
   - `species`
   - `sex`
   - `session_date`

3. Check NWB schema mapping:
   - Review `nwb/schemas/v1.0-fiber-photometry.json`
   - Ensure ELN fields map correctly

4. Manual validation:
   ```bash
   pixi run python -c "
   import pynwb
   with pynwb.NWBHDF5IO('/path/to/file.nwb', 'r') as io:
       nwb = io.read()
       errors = pynwb.validate(nwb)
       print(errors)
   "
   ```

5. Force re-package with corrected metadata:
   ```bash
   curl -X POST http://localhost:8000/v1/nwb/package \
     -H "Content-Type: application/json" \
     -d '{"session_id": "M001_2025-10-27_fear_conditioning", "force_repackage": true}'
   ```

---

### Issue: DANDI Upload Failed

**Symptoms**: Pipeline status shows `failed` at `uploading` stage

**Error Messages**:
- "DANDI API rate limit exceeded"
- "Invalid dandiset ID"
- "Network timeout"
- "Checksum verification failed"

**Solutions**:

1. Check DANDI credentials:
   ```bash
   # Test DANDI API key
   curl -H "Authorization: token YOUR_API_KEY" \
     https://api.dandiarchive.org/api/dandisets/
   ```

2. Verify dandiset exists:
   ```bash
   # List your dandisets
   pixi run dandi ls
   ```

3. Retry upload (automatic after 3 exponential backoff attempts)

4. Check network connectivity:
   ```bash
   ping api.dandiarchive.org
   ```

5. Manual upload for debugging:
   ```bash
   pixi run dandi upload \
     --dandiset-path /path/to/dandiset \
     --dandi-instance dandi \
     /path/to/file.nwb
   ```

6. Check DANDI file size limits (max 100GB per file)

---

### Issue: File Watcher Not Detecting Files

**Symptoms**: Files uploaded to `raw/` directory but pipeline stays in `awaiting_data` stage

**Solutions**:

1. Verify file paths are correct:
   ```bash
   ls -la /storage/experiments/M001/behavior/fear_conditioning/2025-10-27/raw/
   ```

2. Check readiness criteria:
   - **Fiber Photometry**: TDT tank folder + protocol CSV
   - Verify both are present

3. Check file permissions:
   ```bash
   # Watcher needs read permissions
   chmod -R +r /storage/experiments/
   ```

4. Check watcher logs:
   ```bash
   tail -f logs/worker.log | grep "watcher"
   ```

5. Manually trigger preprocessing:
   ```bash
   curl -X POST http://localhost:8000/v1/nwb/package \
     -H "Content-Type: application/json" \
     -d '{"session_id": "M001_2025-10-27_fear_conditioning", "force_repackage": true}'
   ```

6. Restart worker (watcher may be stuck):
   ```bash
   pkill -f celery
   pixi run worker
   ```

---

### Issue: Port Already in Use

**Symptoms**: `Address already in use` error when starting services

**Solutions**:

1. Find process using port:
   ```bash
   # Linux/macOS
   lsof -i :8000  # API port
   lsof -i :8501  # UI port

   # Windows
   netstat -ano | findstr :8000
   ```

2. Kill process:
   ```bash
   kill -9 <PID>
   ```

3. Use different port:
   ```bash
   # API
   pixi run uvicorn app.main:app --port 8001

   # UI
   pixi run streamlit run ui/Home.py --server.port 8502
   ```

4. Update `.env`:
   ```bash
   API_PORT=8001
   ```

---

### Issue: Redis Connection Refused

**Symptoms**: `redis.exceptions.ConnectionError: Connection refused`

**Solutions**:

1. Start Redis:
   ```bash
   redis-server
   ```

2. Check Redis is listening:
   ```bash
   redis-cli ping  # Should return "PONG"
   ```

3. Verify Redis configuration in `.env`:
   ```bash
   REDIS_HOST=localhost
   REDIS_PORT=6379
   ```

4. Check firewall (if Redis on remote host):
   ```bash
   telnet <REDIS_HOST> 6379
   ```

---

## Project Structure Overview

```
elabftw-app/
├── app/                    # FastAPI backend
│   ├── main.py             # Application entry point
│   ├── routes/             # API endpoints (/v1/sync, /v1/status, etc.)
│   ├── services/           # Business logic (ELN sync, NWB packaging)
│   └── models/             # Pydantic domain models
├── ui/                     # Streamlit operator dashboard
│   ├── Home.py             # Dashboard homepage
│   └── pages/              # Dashboard pages (status, logs, etc.)
├── workers/                # Celery background tasks
│   ├── celery_app.py       # Celery configuration
│   └── tasks/              # Task definitions (sync, package, upload)
├── adapters/               # Pluggable ELN and storage adapters
│   ├── eln/                # ELN adapters (LabArchives, eLabFTW)
│   └── storage/            # Storage adapters (local, OneDrive, Box)
├── nwb/                    # NWB packaging and validation
│   ├── packager.py         # Main NWB packaging logic
│   ├── validators.py       # pynwb validation wrapper
│   └── schemas/            # ELN → NWB field mapping schemas
├── dandi/                  # DANDI upload and manifest logic
│   ├── uploader.py         # DANDI CLI/API wrapper
│   └── validators.py       # DANDI metadata validation
├── tests/                  # Test suites (unit, integration, e2e)
├── specs/                  # Feature specifications and design docs
├── pixi.toml               # Dependency and task definitions
├── .env.example            # Environment configuration template
└── README.md               # Project README
```

For detailed architecture documentation, see:
- **Data Model**: `specs/heet-dev/data-model.md`
- **API Contracts**: `specs/heet-dev/contracts/api-endpoints.yaml`
- **Implementation Plan**: `specs/heet-dev/plan.md`

---

## Next Steps

1. **Review Plan**: Read `specs/heet-dev/plan.md` for implementation roadmap
2. **Run Tests**: Verify installation with `pixi run test`
3. **First Sync**: Trigger ELN sync and monitor pipeline status
4. **Explore UI**: Navigate dashboard to understand monitoring capabilities
5. **Contribute**: Create feature branch and submit pull requests

---

## Support

For issues and questions:

- **Documentation**: https://github.com/your-org/elabftw-app/tree/main/docs
- **Issues**: https://github.com/your-org/elabftw-app/issues
- **Email**: support@yourlab.edu

---

**Document Status**: Complete
**Last Updated**: 2025-10-27
**Version**: 1.0
