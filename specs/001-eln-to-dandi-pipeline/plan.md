# Implementation Plan: ELN to DANDI Pipeline Automation

**Branch**: `heet-dev` | **Date**: 2025-10-27 | **Spec**: ../001-eln-to-dandi-pipeline/spec.md
**Input**: Feature specification from `specs/001-eln-to-dandi-pipeline/spec.md`

## Summary

elabftw-app automates the protocol-to-publication workflow for NIH neuroscience investigators conducting fiber photometry behavioral experiments. The system integrates Electronic Lab Notebooks (LabArchives NIH instance and eLabFTW) with structured storage directories, automatically generates NWB-compliant files with ndx-fiber-photometry metadata, and uploads them to the DANDI data repository.

**Technical Approach**: Microservices architecture with FastAPI backend for API orchestration, Streamlit operator UI for monitoring, Celery workers for long-running packaging/upload jobs, watchfiles-based directory monitoring for data readiness detection, modular ELN and storage adapters for multi-backend support, and pynwb/neuroconv for NWB generation with ndx-fiber-photometry extension. All operations are idempotent with structured logging and provenance tracking back to ELN entries.

## Technical Context

**Language/Version**: Python 3.13 (NON-NEGOTIABLE)
**Primary Dependencies**: FastAPI, Streamlit, pynwb, neuroconv, ndx-fiber-photometry, dandi-cli, elabapi-python, Celery, Redis, watchfiles
**Storage**: Local filesystem (Phase 1), OneDrive/Box adapters (Phase 3), Redis for task queue state
**Testing**: pytest with pytest-asyncio; E2E tests MUST use real ELN/DANDI APIs (no mocks)
**Target Platform**: Linux server (production), Windows (development support)
**Project Type**: Web application monorepo (backend API + operator UI + workers)
**Performance Goals**: <5 min sync latency (ELN → Dir), <10 sec metadata extraction, <10 min NWB packaging (P95), >95% DANDI upload success
**Constraints**: NIH data governance (no PII exfiltration), NWB schema compliance, DANDI rate limits (chunked uploads <256 MiB), idempotent operations, structured logging with request_id/subject_id/entry_id
**Scale/Scope**: 10+ concurrent experiments, datasets up to 10GB, multi-lab deployment, TDT tank + AnyMaze + video processing

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

✅ **Principle I (Mission-Driven Architecture)**: All features directly support ELN → NWB → DANDI pipeline
✅ **Principle II (Data Standards Compliance)**: pynwb + neuroconv + ndx-fiber-photometry mandatory; pynwb validation gate enforced
✅ **Principle III (Multi-ELN Support)**: Modular adapters for LabArchives (NIH wrapper) and eLabFTW (elabapi-python)
✅ **Principle IV (Python 3.13 & Pixi-Only)**: Python 3.13 runtime enforced; pixi.toml for all dependencies; no pip/conda
✅ **Principle V (Testing Discipline)**: E2E tests use real LabArchives/eLabFTW/DANDI APIs; unit/integration may use fakes
✅ **Principle VI (Idempotency & Determinism)**: NWB packaging idempotent (byte-stable excluding timestamps); retry-safe workers
✅ **Principle VII (Observability)**: Structured JSON logging, sync latency tracking, DANDI upload metrics, provenance to ELN

**Review Gates (pre-merge)**:
1. NWB Validation Gate: `pynwb.validate()` passes on generated files
2. DANDI Dry-Run Gate: `dandi upload --dry-run` succeeds without errors
3. Spec/Plan Alignment Gate: Implementation matches approved spec.md
4. Constitution Compliance Gate: All NON-NEGOTIABLE principles satisfied
5. Python 3.13 Gate: All code runs on Python 3.13 (no version fallbacks)
6. Pixi-Only Gate: No pip/conda/poetry in scripts or CI (pixi tasks only)
7. E2E Test Gate: No mocked external systems (may mark blocked if credentials unavailable)

## Project Structure

### Documentation (this feature)

```text
specs/heet-dev/
├── plan.md              # This file (implementation planning document)
├── research.md          # Phase 0 output (API exploration, TDT format, NWB schema research)
├── data-model.md        # Phase 1 output (8 entities: Subject, Surgery, Behavior, etc.)
├── quickstart.md        # Phase 1 output (setup guide for operators/developers)
├── contracts/           # Phase 1 output (adapter interfaces, API schemas)
│   ├── eln-adapter.yaml         # ELN adapter interface contract
│   ├── storage-adapter.yaml     # Storage backend interface contract
│   ├── api-endpoints.yaml       # FastAPI endpoint specifications (OpenAPI)
│   └── nwb-schema.json          # ELN field → NWB field mapping schema
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)

```text
app/                                 # FastAPI backend
├── main.py                          # Application entry point, ASGI app factory
├── config.py                        # Configuration management (from env/secrets)
├── dependencies.py                  # Dependency injection (adapters, Redis client)
├── models/                          # Pydantic domain models
│   ├── subject.py                   # Subject entity
│   ├── surgery.py                   # Surgery entity
│   ├── behavior.py                  # Behavior Session entity
│   ├── acquisition.py               # Data Acquisition entity
│   ├── nwb_dataset.py               # NWB Dataset entity
│   ├── eln_entry.py                 # ELN Entry entity
│   ├── analysis_run.py              # Analysis Run entity
│   └── pipeline_status.py           # Pipeline Status entity
├── routes/                          # API endpoints (versioned under /v1)
│   ├── v1/
│   │   ├── sync.py                  # POST /v1/sync - Trigger ELN sync job
│   │   ├── status.py                # GET /v1/status/{subject_id} - Pipeline status
│   │   ├── subjects.py              # GET /v1/subjects - List subjects
│   │   ├── sessions.py              # GET /v1/sessions/{subject_id} - Sessions
│   │   └── nwb.py                   # POST /v1/nwb/package - Manual NWB packaging
│   └── health.py                    # GET /health - Health check
├── services/                        # Business logic services
│   ├── eln_service.py               # ELN polling, metadata extraction
│   ├── directory_service.py         # Directory structure creation
│   ├── nwb_service.py               # NWB packaging orchestration
│   ├── dandi_service.py             # DANDI upload orchestration
│   └── provenance_service.py        # Git SHA, env hash tracking
└── schemas/                         # Pydantic request/response schemas
    ├── sync_schemas.py              # SyncRequest, SyncResponse
    ├── status_schemas.py            # StatusResponse
    └── nwb_schemas.py               # NWBPackageRequest, NWBPackageResponse

ui/                                  # Streamlit operator UI
├── Home.py                          # Dashboard entry point
├── pages/
│   ├── 1_Pipeline_Status.py         # Real-time pipeline status view
│   ├── 2_Subjects.py                # Subject/session browser
│   ├── 3_Logs.py                    # Structured log viewer
│   └── 4_Manual_Triggers.py         # Manual job submission interface
└── components/
    ├── status_badge.py              # Status badge component
    ├── log_viewer.py                # JSON log formatter
    └── job_trigger.py               # Job trigger form

workers/                             # Celery background workers
├── celery_app.py                    # Celery app configuration (Redis broker)
├── tasks/
│   ├── sync_task.py                 # ELN sync task (polling, metadata extraction)
│   ├── preprocess_task.py           # TDT tank preprocessing task
│   ├── package_task.py              # NWB packaging task (with retries)
│   └── upload_task.py               # DANDI upload task (with exponential backoff)
└── utils/
    ├── retry_policy.py              # Exponential backoff, max retries config
    └── idempotency.py               # Idempotency key generation (subject+session)

adapters/                            # Pluggable adapter implementations
├── eln/
│   ├── base.py                      # ELNAdapter Protocol (abstract interface)
│   ├── labarchives/
│   │   ├── adapter.py               # LabArchivesAdapter (via NIH wrapper)
│   │   ├── auth.py                  # Token-based authentication
│   │   ├── parser.py                # ELN entry → metadata extraction
│   │   └── schema.py                # LabArchives-specific field mappings
│   └── elabftw/
│       ├── adapter.py               # ElabFTWAdapter (via elabapi-python)
│       ├── auth.py                  # API key authentication
│       ├── parser.py                # ELN entry → metadata extraction
│       └── schema.py                # eLabFTW-specific field mappings
└── storage/
    ├── base.py                      # StorageAdapter Protocol (abstract interface)
    ├── local/
    │   ├── adapter.py               # LocalStorageAdapter (filesystem)
    │   ├── watcher.py               # Directory watcher (watchfiles)
    │   └── manifest.py              # Manifest file (.elabftw-manifest.json)
    ├── onedrive/
    │   ├── adapter.py               # OneDriveAdapter (stub - Phase 3)
    │   └── auth.py                  # OAuth2 flow (stub)
    └── box/
        ├── adapter.py               # BoxAdapter (stub - Phase 3)
        └── auth.py                  # OAuth2 flow (stub)

nwb/                                 # NWB packaging and validation
├── package_one.py                   # CLI entry point: python -m nwb.package_one
├── packager.py                      # Main NWB packaging logic (neuroconv + pynwb)
├── validators.py                    # pynwb.validate wrapper + validation report
├── schemas/
│   ├── v1.0-fiber-photometry.json   # ELN field → NWB field mapping (version 1.0)
│   └── mapping_utils.py             # Schema loading and field transformation
├── extensions/
│   └── ndx_fiber_photometry.py      # ndx-fiber-photometry integration
└── provenance.py                    # Git SHA, pixi lock hash extraction

dandi/                               # DANDI upload and manifest logic
├── upload.py                        # CLI entry point: python -m dandi.upload
├── uploader.py                      # DANDI CLI/API wrapper (resumable uploads)
├── validators.py                    # DANDI metadata validation (pre-upload)
├── manifest.py                      # Dandiset metadata YAML generation
└── logging_utils.py                 # Upload status → ELN logging

tests/
├── unit/                            # Fast, isolated tests (fakes/stubs allowed)
│   ├── test_eln_adapters.py         # ELN adapter unit tests (mocked API responses)
│   ├── test_storage_adapters.py     # Storage adapter unit tests
│   ├── test_nwb_packager.py         # NWB packaging logic (fake data)
│   ├── test_dandi_uploader.py       # DANDI uploader logic (mocked API)
│   └── test_services.py             # Service layer tests
├── integration/                     # Real library calls (sandbox services)
│   ├── test_nwb_validation.py       # pynwb.validate on generated files
│   ├── test_celery_tasks.py         # Celery task execution (local Redis)
│   └── test_api_endpoints.py        # FastAPI endpoint tests (TestClient)
├── e2e/                             # End-to-end tests (MUST use real systems)
│   ├── test_labarchives_sync.py     # Real LabArchives API sync
│   ├── test_elabftw_sync.py         # Real eLabFTW API sync
│   ├── test_full_pipeline.py        # ELN → Dir → NWB → DANDI (golden dataset)
│   └── test_dandi_upload.py         # Real DANDI upload (test dandiset)
├── fixtures/
│   ├── eln_entries.json             # Sample ELN entries (no PII)
│   ├── tdt_tank_sample/             # Sample TDT tank structure
│   ├── protocol_csvs/               # Sample protocol CSVs
│   └── golden_nwb/                  # Golden NWB file for validation gate
└── conftest.py                      # Pytest fixtures, markers, session setup

infra/                               # Deployment and ops scripts
├── docker/
│   ├── Dockerfile.api               # FastAPI backend image
│   ├── Dockerfile.ui                # Streamlit UI image
│   └── Dockerfile.worker            # Celery worker image
├── docker-compose.yml               # Local development stack
├── k8s/                             # Kubernetes manifests (production)
│   ├── api-deployment.yaml
│   ├── ui-deployment.yaml
│   ├── worker-deployment.yaml
│   ├── redis-statefulset.yaml
│   └── ingress.yaml
└── scripts/
    ├── health_check.sh              # Service health check script
    └── backup_manifests.sh          # Backup .elabftw-manifest.json files

scripts/                             # Developer and operator scripts
├── setup_dev.sh                     # Initial dev environment setup (pixi install)
├── lint.sh                          # Wrapper for `pixi run lint`
├── test_all.sh                      # Run all test suites (unit + integration + e2e)
└── validate_constitution.py         # Constitution compliance checker (CI gate)

.github/workflows/
├── ci.yml                           # CI pipeline: lint, typecheck, unit, integration
├── e2e.yml                          # E2E pipeline (may skip if credentials unavailable)
└── constitution-check.yml           # Constitution compliance gate

pixi.toml                            # Pixi environment and task definitions
ruff.toml                            # Ruff linter/formatter config (line-length=100)
mypy.ini                             # Mypy type checker config (strict_optional=True)
pyproject.toml                       # Project metadata, dependency declarations
.pre-commit-config.yaml              # Pre-commit hooks (ruff, mypy, secrets detection)
.gitignore                           # Ignore .env, credentials.json, .pixi/, etc.
README.md                            # Project README (quickstart, architecture)
CLAUDE.md                            # Technical guardrails and authoring policy
```

**Structure Decision**: Web application monorepo with separation of concerns:
- `app/` contains the FastAPI backend (API orchestration, business logic, domain models)
- `ui/` contains the Streamlit operator dashboard (monitoring, manual interventions)
- `workers/` contains Celery background tasks (long-running jobs with retry logic)
- `adapters/` contains pluggable ELN and storage backend implementations (Protocol-based)
- `nwb/` and `dandi/` are standalone modules with CLI entry points for packaging/upload
- `tests/` follows pytest conventions with unit/integration/e2e separation (E2E uses real systems)
- `infra/` and `scripts/` support deployment and operational tasks

This structure supports:
- Independent scaling of API, UI, and workers (containerized deployments)
- Clear adapter boundaries for multi-backend support (LabArchives, eLabFTW, OneDrive, Box)
- CLI-first design for NWB packaging and DANDI upload (can run standalone or via workers)
- Comprehensive testing with clear isolation between unit (fast), integration (real libraries), and E2E (real APIs)

## Complexity Tracking

*No constitution violations - table omitted.*

## Phase 0: Research & Discovery

**Goal**: Investigate external APIs, data formats, and integration patterns to derisk technical unknowns.

**Duration**: 1 week

**Deliverables**: `specs/heet-dev/research.md`

### Research Areas

1. **LabArchives API Integration**
   - NIH-approved wrapper library API (authentication, rate limits, pagination)
   - Entry retrieval methods (polling vs. webhooks)
   - Attachment download mechanisms
   - Status update/logging API (append notes/comments)
   - Error handling and retry patterns

2. **eLabFTW API Integration**
   - `elabapi-python` SDK authentication (API key management)
   - Entry retrieval and filtering (by date, user, tags)
   - Metadata extraction from structured fields and Markdown content
   - Status field updates vs. comment appending
   - Differences from LabArchives API patterns

3. **TDT Tank Data Processing**
   - TDT tank folder structure (metadata files, data files, naming conventions)
   - Existing libraries for TDT data reading (tdt-python, neo, etc.)
   - Timestamp alignment requirements for fiber photometry data
   - Sampling rate extraction and validation
   - Integration with neuroconv TDTDataInterface (if available)

4. **NWB Schema Mapping (ndx-fiber-photometry)**
   - `ndx-fiber-photometry` extension schema (FiberPhotometry, FiberPhotometryResponseSeries)
   - Required metadata fields (subject, session, timestamps, acquisition device)
   - Mapping from TDT tank + ELN metadata → NWB structure
   - Multi-trial/multi-timepoint handling in NWB
   - pynwb validation requirements and common failure modes

5. **File System Watcher Patterns**
   - `watchfiles` library capabilities (recursive watching, event filtering)
   - Readiness detection logic (all required files present for experiment type)
   - Debouncing strategies (avoid triggering on partial uploads)
   - Handling of large file uploads (video files, TDT tanks)
   - Graceful handling of file deletions and modifications

6. **DANDI Upload Best Practices**
   - `dandi-cli` vs. API usage (resumable uploads, chunking)
   - Dandiset metadata YAML structure and validation
   - Rate limiting and throttling strategies
   - Checksum verification and retry logic
   - Asset ID retrieval and logging back to ELN

7. **Celery Architecture for Long-Running Jobs**
   - Redis broker configuration (persistence, memory limits)
   - Task routing (separate queues for sync, preprocessing, packaging, upload)
   - Retry policies (exponential backoff, max retries, dead-letter queue)
   - Idempotency key patterns (composite keys: subject_id + session_date)
   - Task monitoring and observability (Flower, structured logging)

8. **Multi-Storage Backend Patterns**
   - OneDrive API authentication (OAuth2, token refresh)
   - Box API authentication and file upload/download
   - Adapter interface design (common operations: read, write, list, watch)
   - Path normalization across backends (filesystem vs. cloud storage)
   - Watcher implementation differences (local inotify vs. cloud webhooks)

### Research Output Format

For each research area, document in `research.md`:
- **Findings**: Key technical insights, API patterns, library capabilities
- **Risks**: Potential blockers, rate limits, authentication complexity
- **Decisions**: Recommended libraries, patterns, and integration approaches
- **Examples**: Code snippets, API request/response examples, configuration samples
- **Open Questions**: Items requiring clarification or further investigation

## Phase 1: Design & Contracts

**Goal**: Define data models, adapter interfaces, API contracts, and system boundaries.

**Duration**: 2 weeks

**Deliverables**: `specs/heet-dev/data-model.md`, `specs/heet-dev/contracts/`, `specs/heet-dev/quickstart.md`

### 1. Data Model (`data-model.md`)

Define 8 core entities with attributes, relationships, and lifecycle states:

**Subject**
- Attributes: subject_id (primary key), species, strain, sex, date_of_birth, surgery_history (list), created_at, updated_at
- Relationships: has many Surgery, has many Behavior Session
- Lifecycle: Created from first ELN entry → Updated with new surgeries/sessions → Archived after experiment completion

**Surgery**
- Attributes: surgery_id (primary key), subject_id (foreign key), surgery_date, procedure_type, implant_details, surgeon_name, recovery_notes, eln_entry_id, created_at
- Relationships: belongs to Subject, linked to ELN Entry
- Lifecycle: Created from ELN Surgery entry → Immutable after creation → Referenced by Behavior Sessions

**Behavior Session**
- Attributes: session_id (primary key), subject_id (foreign key), session_date, protocol_name, duration_minutes, trial_count, environmental_conditions, eln_entry_id, created_at, updated_at
- Relationships: belongs to Subject, may reference Surgery, has one Data Acquisition, has one Pipeline Status
- Lifecycle: Created from ELN Behavior entry → Directory created → Data acquisition detected → NWB generated → Uploaded to DANDI → Complete

**Data Acquisition**
- Attributes: acquisition_id (primary key), session_id (foreign key), acquisition_date, directory_path, file_types (list: TDT, CSV, video), tdt_tank_path, protocol_csv_path, video_paths (list), acquisition_system_metadata, readiness_status (awaiting, ready, processing), created_at, updated_at
- Relationships: belongs to Behavior Session
- Lifecycle: Created when directory detected → Updated as files uploaded → Marked ready when complete → Linked to Analysis Run

**NWB Dataset**
- Attributes: nwb_id (primary key), session_id (foreign key), nwb_file_path, creation_timestamp, validation_status (pending, passed, failed), validation_report_path, code_version_hash, pixi_lock_hash, dandi_asset_id, dandi_upload_timestamp, created_at, updated_at
- Relationships: belongs to Behavior Session, references Subject and Surgery
- Lifecycle: Created during packaging → Validated with pynwb → Uploaded to DANDI → Asset ID logged → Immutable

**ELN Entry**
- Attributes: entry_id (primary key), eln_backend (LabArchives, eLabFTW), entry_type (Surgery, Behavior, Imaging), creation_date, last_modified_date, researcher, parsed_metadata (JSON), raw_content, linked_entity_id (subject/surgery/session), synced_at, created_at, updated_at
- Relationships: links to Subject, Surgery, or Behavior Session
- Lifecycle: Fetched from ELN API → Metadata parsed → Entity created → Status updates logged back → Re-synced on modification

**Analysis Run**
- Attributes: run_id (primary key), acquisition_id (foreign key), run_type (preprocessing, packaging, upload), start_time, end_time, status (pending, running, completed, failed), error_logs, input_files (list), output_files (list), retry_count, created_at, updated_at
- Relationships: belongs to Data Acquisition
- Lifecycle: Queued → Running (task execution) → Completed (success) or Failed (with error logs) → Retried (if transient failure)

**Pipeline Status**
- Attributes: status_id (primary key), session_id (foreign key), current_stage (synced, awaiting_data, preprocessing, packaging, uploading, complete, failed), last_updated, error_messages (list), retry_eligible (bool), manual_intervention_required (bool), created_at, updated_at
- Relationships: belongs to Behavior Session
- Lifecycle: Initialized on sync → Updated through stages → Terminal state (complete or failed) → Logged to ELN

### 2. Contracts (`contracts/`)

**eln-adapter.yaml** (ELN Adapter Interface - OpenAPI YAML)
```yaml
ELNAdapter:
  methods:
    authenticate:
      description: Authenticate with ELN backend
      inputs:
        credentials: dict (token or API key)
      outputs:
        authenticated: bool
        error: Optional[str]

    get_entries:
      description: Retrieve entries since last sync
      inputs:
        since: datetime
        entry_types: list[str] (Surgery, Behavior, Imaging)
      outputs:
        entries: list[ELNEntry]
        error: Optional[str]

    get_entry:
      description: Retrieve single entry by ID
      inputs:
        entry_id: str
      outputs:
        entry: ELNEntry
        error: Optional[str]

    update_entry_status:
      description: Log status update to ELN entry
      inputs:
        entry_id: str
        status_message: str
        timestamp: datetime
      outputs:
        success: bool
        error: Optional[str]

    download_attachment:
      description: Download attachment from ELN entry
      inputs:
        entry_id: str
        attachment_id: str
        destination_path: Path
      outputs:
        success: bool
        file_path: Path
        error: Optional[str]
```

**storage-adapter.yaml** (Storage Backend Interface - OpenAPI YAML)
```yaml
StorageAdapter:
  methods:
    ensure_structure:
      description: Create directory structure from manifest
      inputs:
        manifest: Manifest (experiment type, subject ID, session date)
      outputs:
        directory_path: Path
        error: Optional[str]

    put:
      description: Write file to storage
      inputs:
        source_path: Path
        destination_path: Path
      outputs:
        success: bool
        error: Optional[str]

    get:
      description: Read file from storage
      inputs:
        file_path: Path
      outputs:
        content: bytes
        error: Optional[str]

    exists:
      description: Check if file/directory exists
      inputs:
        path: Path
      outputs:
        exists: bool

    list:
      description: List files in directory
      inputs:
        directory_path: Path
        recursive: bool
      outputs:
        files: list[Path]
        error: Optional[str]

    watch:
      description: Watch directory for changes (async)
      inputs:
        directory_path: Path
        event_handler: Callable
      outputs:
        watcher_id: str
        error: Optional[str]
```

**api-endpoints.yaml** (FastAPI Endpoint Specifications - OpenAPI 3.1)
```yaml
openapi: 3.1.0
info:
  title: elabftw-app API
  version: 1.0.0

paths:
  /v1/sync:
    post:
      summary: Trigger ELN sync job
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                project_id:
                  type: string
                since:
                  type: string
                  format: date-time
              required: [project_id]
      responses:
        202:
          description: Sync job accepted
          content:
            application/json:
              schema:
                type: object
                properties:
                  accepted:
                    type: boolean
                  request_id:
                    type: string

  /v1/status/{subject_id}:
    get:
      summary: Get pipeline status for subject
      parameters:
        - name: subject_id
          in: path
          required: true
          schema:
            type: string
      responses:
        200:
          description: Pipeline status
          content:
            application/json:
              schema:
                type: object
                properties:
                  subject_id:
                    type: string
                  sessions:
                    type: array
                    items:
                      type: object
                      properties:
                        session_id:
                          type: string
                        session_date:
                          type: string
                        current_stage:
                          type: string
                        last_updated:
                          type: string

  /v1/subjects:
    get:
      summary: List all subjects
      responses:
        200:
          description: Subject list
          content:
            application/json:
              schema:
                type: array
                items:
                  type: object
                  properties:
                    subject_id:
                      type: string
                    species:
                      type: string
                    session_count:
                      type: integer

  /v1/nwb/package:
    post:
      summary: Manually trigger NWB packaging
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                session_id:
                  type: string
                force_repackage:
                  type: boolean
              required: [session_id]
      responses:
        202:
          description: Packaging job accepted
          content:
            application/json:
              schema:
                type: object
                properties:
                  accepted:
                    type: boolean
                  job_id:
                    type: string
```

**nwb-schema.json** (ELN Field → NWB Field Mapping - Version 1.0)
```json
{
  "version": "1.0",
  "schema_date": "2025-10-27",
  "mappings": {
    "subject": {
      "eln_field": "subject_id",
      "nwb_field": "Subject.subject_id",
      "required": true,
      "transform": null
    },
    "species": {
      "eln_field": "species",
      "nwb_field": "Subject.species",
      "required": true,
      "transform": "species_code_to_ncbi"
    },
    "sex": {
      "eln_field": "sex",
      "nwb_field": "Subject.sex",
      "required": true,
      "transform": "normalize_sex"
    },
    "date_of_birth": {
      "eln_field": "dob",
      "nwb_field": "Subject.date_of_birth",
      "required": false,
      "transform": "parse_datetime"
    },
    "session_start_time": {
      "eln_field": "session_date",
      "nwb_field": "NWBFile.session_start_time",
      "required": true,
      "transform": "parse_datetime"
    },
    "fiber_photometry": {
      "eln_field": "tdt_tank_path",
      "nwb_field": "FiberPhotometry",
      "required": true,
      "transform": "load_tdt_timeseries"
    }
  },
  "transforms": {
    "species_code_to_ncbi": {
      "description": "Map species common name to NCBI taxonomy ID",
      "examples": {
        "mouse": "http://purl.obolibrary.org/obo/NCBITaxon_10090",
        "rat": "http://purl.obolibrary.org/obo/NCBITaxon_10116"
      }
    },
    "normalize_sex": {
      "description": "Normalize sex values to NWB vocabulary",
      "examples": {
        "M": "M",
        "F": "F",
        "male": "M",
        "female": "F"
      }
    },
    "parse_datetime": {
      "description": "Parse datetime string to ISO8601",
      "format": "ISO8601"
    },
    "load_tdt_timeseries": {
      "description": "Load TDT tank data and convert to NWB timeseries",
      "library": "tdt-python or neo"
    }
  }
}
```

### 3. Quickstart Guide (`quickstart.md`)

Write operator-facing quickstart guide covering:
- **Prerequisites**: Python 3.13, pixi, Git, Redis, access to ELN/DANDI/storage
- **Installation**: `pixi install`, secrets configuration (`.env` template)
- **Configuration**: ELN backend selection (LabArchives vs. eLabFTW), storage backend, DANDI credentials
- **Running Services**: `pixi run api`, `pixi run ui`, `pixi run worker`
- **First Sync**: Trigger manual ELN sync via API or UI
- **Monitoring**: Dashboard overview, log viewer, pipeline status tracking
- **Manual Interventions**: Triggering NWB repackaging, retrying failed uploads
- **Troubleshooting**: Common errors (authentication failures, NWB validation errors, DANDI upload failures)

## Phase 2: Core Implementation (4 Milestones)

**Duration**: 16 weeks total

### Milestone 1: MVP - LabArchives + Local NWB (Weeks 1-4)

**Goal**: Demonstrate end-to-end pipeline with LabArchives and local filesystem storage.

**Scope**:
- LabArchives ELN adapter (authentication, entry retrieval, status updates)
- Local storage adapter (directory creation, manifest files)
- FastAPI backend with sync, status, and health endpoints
- Basic Streamlit UI (pipeline status view)
- NWB packaging (pynwb + ndx-fiber-photometry) with TDT tank support
- pynwb validation gate
- Structured logging (JSON format)
- Unit and integration tests
- CI pipeline (lint, typecheck, unit, integration)

**Deliverables**:
- Working LabArchives → Local Dir → NWB pipeline (manual data upload)
- NWB files passing pynwb validation
- API documentation (OpenAPI spec)
- Developer setup guide (quickstart.md)

**Acceptance Criteria**:
- User Story 1 acceptance scenarios pass (ELN sync to directory)
- User Story 3 acceptance scenarios pass (NWB generation and validation)
- Constitution Gates 1, 4, 5, 6, 7 pass (NWB validation, Python 3.13, Pixi-only, E2E discipline, observability)

### Milestone 2: Automation - Watcher + DANDI Upload (Weeks 5-8)

**Goal**: Automate preprocessing trigger and DANDI upload with retry logic.

**Scope**:
- File system watcher (watchfiles) with readiness detection
- Celery workers (sync, preprocessing, packaging, upload tasks)
- Redis broker configuration
- DANDI uploader (dandi-cli wrapper with resumable uploads)
- DANDI validation gate
- Retry policies (exponential backoff, idempotency keys)
- ELN status logging (upload success/failure)
- Provenance tracking (Git SHA, pixi lock hash)
- E2E tests (LabArchives + DANDI with real APIs)

**Deliverables**:
- Automatic pipeline trigger on data readiness
- DANDI upload with retry and resumption
- Provenance records in NWB and ELN
- E2E test suite (may be marked blocked if credentials unavailable)

**Acceptance Criteria**:
- User Story 2 acceptance scenarios pass (watcher trigger)
- User Story 4 acceptance scenarios pass (DANDI upload)
- Constitution Gates 2, 3, 6 pass (DANDI dry-run, spec alignment, idempotency)
- DANDI upload success rate >95% in testing

### Milestone 3: Multi-Backend Support (Weeks 9-12)

**Goal**: Add eLabFTW ELN support and OneDrive/Box storage adapters.

**Scope**:
- eLabFTW ELN adapter (elabapi-python integration)
- Adapter selection via configuration (environment variables)
- OneDrive storage adapter (OAuth2, file upload/download)
- Box storage adapter (OAuth2, file upload/download)
- Multi-backend E2E tests (eLabFTW + local, LabArchives + OneDrive)
- Adapter interface documentation

**Deliverables**:
- Working eLabFTW → Local/OneDrive/Box → NWB → DANDI pipeline
- Adapter selection documentation (quickstart.md update)
- Multi-backend test suite

**Acceptance Criteria**:
- User Story 5 acceptance scenarios pass (multi-ELN support)
- Pipeline functions identically with LabArchives and eLabFTW
- Storage adapters pass contract compliance tests
- Constitution Gate 3 pass (multi-ELN modular design)

### Milestone 4: Production Hardening (Weeks 13-16)

**Goal**: Prepare for production deployment with monitoring, security, and operational tooling.

**Scope**:
- Secrets management (environment variables + secrets manager integration stubs)
- Enhanced observability (sync latency metrics, upload success rate tracking)
- Streamlit dashboard enhancements (log filtering, manual job triggers)
- Docker images (API, UI, worker)
- Kubernetes manifests (deployments, services, ingress)
- CI/CD pipeline (Docker build, push, deploy)
- Pre-commit hooks (ruff, mypy, secrets detection)
- Production runbooks (onboarding, token rotation, troubleshooting)
- Golden dataset E2E test (CI gate)

**Deliverables**:
- Production-ready container images
- Kubernetes deployment manifests
- Operator runbooks
- Full CI/CD pipeline with constitution gates
- Security audit (secrets scanning, dependency vulnerabilities)

**Acceptance Criteria**:
- All constitution gates pass in CI
- Golden dataset E2E test passes (NWB validation + DANDI dry-run)
- Docker images build and run successfully
- Observability metrics tracked (sync latency <5 min P95)
- Pre-commit hooks prevent secret commits

## Testing Strategy

### Unit Tests (Fast, Isolated)

**Coverage Target**: 85% minimum

**Scope**:
- ELN adapter methods (mocked API responses)
- Storage adapter methods (in-memory filesystem)
- NWB packager logic (fake TDT data)
- DANDI uploader logic (mocked API)
- Service layer methods
- Pydantic model validation

**Tools**: pytest, pytest-mock, fakefs

**Run Command**: `pixi run unit`

### Integration Tests (Real Libraries)

**Coverage Target**: Key integration points

**Scope**:
- pynwb validation on generated NWB files
- Celery task execution (local Redis)
- FastAPI endpoint tests (TestClient)
- Directory watcher event handling
- Adapter interface contract compliance

**Tools**: pytest, pytest-asyncio, TestClient (FastAPI)

**Run Command**: `pixi run integration`

### E2E Tests (Real Systems - NO MOCKS)

**Coverage Target**: Happy path scenarios

**Scope**:
- LabArchives API sync (real NIH instance or sandbox)
- eLabFTW API sync (real demo instance)
- Full pipeline: ELN → Dir → NWB → DANDI (golden dataset)
- DANDI upload (test dandiset)
- ELN status logging (verify updates in real ELN)

**Tools**: pytest with `@pytest.mark.e2e`, real credentials (from secrets)

**Run Command**: `pixi run e2e`

**Important**: If credentials unavailable, tests MUST be skipped with `pytest.skip(reason="blocked by credentials")`, NOT mocked.

### Golden Dataset

**Purpose**: CI gate for NWB validation and DANDI dry-run

**Contents**:
- Sample ELN entry (JSON fixture, no PII)
- Sample TDT tank folder (minimal data)
- Sample protocol CSV
- Expected NWB file structure (validated with pynwb)

**Location**: `tests/fixtures/golden_dataset/`

**CI Gate**: Generate NWB from golden dataset → `pynwb.validate()` → `dandi upload --dry-run` (MUST pass)

## Risk Mitigation

### Risk 1: LabArchives API Access

**Likelihood**: Medium | **Impact**: High

**Mitigation**:
- Early authentication testing with NIH wrapper
- Document rate limits and implement backoff
- Fallback to eLabFTW for development if LabArchives unavailable
- E2E tests marked as blocked (not mocked) if credentials unavailable

### Risk 2: Multi-Storage Complexity

**Likelihood**: Medium | **Impact**: Medium

**Mitigation**:
- Prioritize local filesystem adapter (M1)
- OneDrive/Box adapters as stubs until OAuth2 flow configured (M3)
- Adapter interface design validated early (Phase 1)
- Contract compliance tests ensure adapter consistency

### Risk 3: NWB Schema Evolution

**Likelihood**: Low | **Impact**: Medium

**Mitigation**:
- Pin ndx-fiber-photometry version in pixi.toml
- Version NWB schema mappings (nwb/schemas/v1.0-*.json)
- Document migration procedure in quickstart.md
- Golden dataset NWB file versioned in Git

### Risk 4: DANDI Rate Limits

**Likelihood**: High | **Impact**: Low

**Mitigation**:
- Implement chunked uploads (<256 MiB)
- Exponential backoff on 429 responses
- Upload queue with rate limiting (Celery task routing)
- Monitor upload success rate (target >95%)

### Risk 5: Data Volume Scaling

**Likelihood**: Medium | **Impact**: Medium

**Mitigation**:
- Performance testing with 10GB datasets (TDT tanks + video)
- Streaming uploads for large files
- Async I/O for file operations
- Storage backend optimization (Phase 3)

### Risk 6: ELN Customization

**Likelihood**: High | **Impact**: Low

**Mitigation**:
- Modular ELN adapters with schema.py per backend
- Document field mapping customization in quickstart.md
- Provide example custom field parsers
- Versioned schema mappings (nwb/schemas/)

## Dependencies & Integrations

### External APIs

- **LabArchives NIH Instance**: Authentication, entry retrieval, attachment download, status updates
- **eLabFTW Demo Instance**: API key authentication, RESTful API for entries, comments
- **DANDI Archive**: Upload API, metadata validation, asset management

### Libraries

- **FastAPI**: API framework (async endpoints, Pydantic schemas)
- **Streamlit**: Operator dashboard (real-time status, log viewer)
- **pynwb**: NWB file generation and validation
- **neuroconv**: Data converter orchestration
- **ndx-fiber-photometry**: NWB extension for fiber photometry data
- **dandi-cli**: DANDI upload client (resumable uploads)
- **elabapi-python**: eLabFTW Python SDK
- **Celery**: Background task queue (with Redis broker)
- **watchfiles**: File system watcher (async directory monitoring)
- **Redis**: Task queue broker and result backend

### Storage

- **Local Filesystem**: Primary storage (M1-M2)
- **OneDrive**: Cloud storage adapter (M3)
- **Box**: Cloud storage adapter (M3)

### CI/CD

- **GitHub Actions**: CI pipeline (lint, typecheck, test, constitution gates)
- **Docker**: Container images (API, UI, worker)
- **Kubernetes**: Production deployment (optional, M4)

## Success Metrics

### Phase 0 Success Criteria

- All 8 research areas documented with findings, risks, decisions
- Code examples for LabArchives API, eLabFTW API, TDT tank reading
- ndx-fiber-photometry integration pattern validated
- Celery architecture documented (task routing, retry policies)

### Phase 1 Success Criteria

- Data model documented (8 entities with attributes, relationships, lifecycle)
- Contracts defined (ELN adapter, storage adapter, API endpoints, NWB schema)
- Quickstart guide written (setup, configuration, first sync, monitoring)
- Phase 1 deliverables reviewed and approved

### Milestone 1 Success Criteria (M1)

- LabArchives adapter passes unit tests (authentication, entry retrieval)
- Local storage adapter creates directory structures
- FastAPI API responds to sync and status requests
- NWB files generated from TDT tanks pass pynwb validation
- Streamlit UI displays pipeline status
- CI pipeline passes (lint, typecheck, unit, integration)

### Milestone 2 Success Criteria (M2)

- Watcher detects data readiness and triggers Celery tasks
- NWB packaging task completes successfully (with retry on failure)
- DANDI upload task uploads to test dandiset (with retry)
- Provenance (Git SHA, pixi lock hash) recorded in NWB and ELN
- E2E test passes (LabArchives → Dir → NWB → DANDI)

### Milestone 3 Success Criteria (M3)

- eLabFTW adapter passes unit and E2E tests
- OneDrive/Box adapters implement storage interface (may be stubs)
- Pipeline functions identically with LabArchives and eLabFTW
- Multi-backend E2E tests pass

### Milestone 4 Success Criteria (M4)

- Docker images build and run successfully
- Kubernetes manifests deploy to test cluster
- Golden dataset E2E test passes in CI
- All constitution gates pass
- Operator runbooks completed
- Security audit passes (no secrets in Git, dependency vulnerabilities addressed)

## Open Questions

1. **LabArchives API Rate Limits**: What are the documented rate limits for the NIH LabArchives instance? Do we need request throttling?

2. **TDT Tank Processing Library**: Should we use `tdt-python`, `neo`, or implement a custom parser? What are the performance implications?

3. **DANDI Test Dandiset**: Do we have access to a test/sandbox dandiset for E2E testing, or should we create one?

4. **Secrets Management**: Should we integrate with a secrets manager (AWS Secrets Manager, Azure Key Vault, HashiCorp Vault) in M4, or defer to post-MVP?

5. **OneDrive/Box OAuth2**: Do we need to support device code flow for headless authentication, or can we assume pre-configured access tokens?

6. **Multi-Trial NWB Packaging**: Should each trial be a separate NWBFile, or multiple trials in a single file with separate timeseries objects?

7. **Watcher Debouncing**: What is the recommended debounce interval for large file uploads (video files)? Should we use file size stability checks?

8. **ELN Polling Interval**: What is the optimal polling interval for ELN APIs? Should we support webhook-based triggers if available?

9. **Kubernetes Production Deployment**: Is Kubernetes the target production environment, or should we also support Docker Compose for smaller deployments?

10. **Custom Field Parsing**: Should we provide a plugin system for labs to define custom ELN field parsers, or document examples for manual customization?

## Next Steps (Post-Planning)

1. **Approve Plan**: Review plan.md with stakeholders and approve for implementation
2. **Phase 0 Research**: Execute research phase (1 week) and produce research.md
3. **Phase 1 Design**: Define data models, contracts, and quickstart guide (2 weeks)
4. **Generate Tasks**: Run `/tasks` command to generate tasks.md from this plan
5. **Milestone 1 Kickoff**: Begin implementation of LabArchives + Local NWB MVP (4 weeks)

---

**Document Version**: 1.0
**Last Updated**: 2025-10-27
**Author**: Claude (via /plan command)
**Approved By**: [Pending Stakeholder Review]
