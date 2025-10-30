## /plan — Technical Implementation Plan Prompt (elabftw-app)

```
/plan
Create the technical implementation plan for elabftw-app.

Summary of spec:
elabftw-app integrates ELNs (LabArchives, eLabFTW) with structured storage directories, automatically generates NWB files with ndx-fiber-photometry metadata, and uploads them to DANDI. It targets NIH investigators to automate the protocol-to-publication workflow.

Non-functional requirements:
- Secure token-based auth
- Modular backend interfaces
- Deterministic data packaging
- Scalable to multiple labs
- Sync latency under 5 minutes

Architecture & Stack:
- Backend: Python 3.13
- Web framework: FastAPI
- UI: Streamlit (operator dashboard)
- ELN Integration: LabArchives wrapper, elabapi-python
- Data packaging: neuroconv + pynwb
- Storage: local FS, OneDrive, Box (modular)
- Repository upload: DANDI CLI & SDK
- Background processing: asyncio / Celery
- Logging/versioning: git SHA, ELN updates

System Design:
- ELN Ingest Module
- Directory Manager
- Watcher Service
- NWB Packager
- Uploader
- Streamlit Dashboard

Data flow:
ELN Entry → API → Metadata → Directory → Data → Processing → NWB → DANDI → ELN Update.

Interfaces:
- ELN API (LabArchives, eLabFTW)
- Storage backends (FS/OneDrive/Box)
- DANDI API
- REST endpoints: `/sync`, `/status`, `/upload`, `/webhook/eln`.
- Streamlit pages: metadata assist, job status.

DevEx & Quality:
- Monorepo layout (`app/`, `ui/`, `workers/`, `adapters/`, `nwb/`, `dandi/`).
- Testing: pytest + mocks for unit, real for e2e.
- CI/CD: GitHub Actions, pixi workflows.
- Reproducibility: pinned deps, manifest logging.

Security:
- Token auth
- Secrets in Secrets Manager
- NIH data boundary respected
- Audit trail

Plan of Work:
- M1: LabArchives ingestion, directory sync, basic NWB.
- M2: DANDI automation, UI, watcher.
- M3: eLabFTW integration, modular backends.
- M4: Generalization.

Cut lines:
- eLabFTW + DANDI can slip without breaking MVP.

Go/No-Go checklist:
- ELN API works
- Directory & NWB stable
- DANDI upload OK
- Audit trail functional
- Constitution compliance (Py 3.13, pixi, no E2E mocks)
```
