# Implementation Plan: ELN to DANDI Pipeline Automation

**Branch**: `heet-dev` | **Date**: 2025-10-27 | **Spec**: ../001-eln-to-dandi-pipeline/spec.md
**Input**: Feature specification from `specs/001-eln-to-dandi-pipeline/spec.md`

## Summary

elabftw-app automates the protocol-to-publication workflow for NIH neuroscience investigators conducting fiber photometry behavioral experiments. The system integrates Electronic Lab Notebooks (LabArchives NIH instance and eLabFTW, with eLabFTW being CRITICAL for launch) with structured storage directories, semi-automatically generates NWB-compliant files with ndx-fiber-photometry metadata after manual approval, and uploads them to the DANDI data repository with video handling as separate assets.

**Technical Approach**: Microservices architecture with FastAPI backend for API orchestration and shared business logic layer (DRY architecture callable by both API and UI), Streamlit operator UI for monitoring and manual approval gates, Celery workers with dynamic scaling for long-running packaging/upload jobs, hybrid sync strategy (webhooks preferred, polling as fallback), configurable retry policies per job type, watchfiles-based directory monitoring for data readiness detection, modular ELN and storage adapters for multi-backend support, and pynwb/neuroconv for NWB generation with ndx-fiber-photometry extension and configurable scope (raw/processed/both). All operations are idempotent with structured logging and provenance tracking back to ELN entries.

**ArchiveFlow Integration**: This implementation plan builds upon the **ArchiveFlow prototype** developed by **Josh Lawrimore (NIMH DSST)**. ArchiveFlow provides:
- ✅ Complete LabArchives OAuth2 integration (~800 LOC)
- ✅ TDT tank processing and signal pipelines (~1500 LOC)
- ✅ 8-page Streamlit operator UI (~2000 LOC)
- ✅ Laboratory directory structure template and custom widget parsers (~500 LOC)

**Migration Strategy**: Phase -1 (2 weeks) will migrate the existing codebase from `uv` → `pixi` (gradual module-by-module approach), Python 3.11 → 3.13 (direct migration, high risk), and Streamlit-only → FastAPI+Streamlit architecture with shared business logic layer while **preserving all working functionality**. This reduces overall implementation time by an estimated 30-40% (8-10 weeks saved). Rollback strategy uses frozen `archiveflow-legacy` branch.

## Technical Context

**Existing Codebase**: ArchiveFlow prototype by Josh Lawrimore (NIMH DSST) - `nimh-dsst/ArchiveFlow` (private)
**Language/Version**: Python 3.13 (NON-NEGOTIABLE, direct upgrade from 3.11, high risk, no pre-testing)
**Primary Dependencies**: FastAPI (NEW with shared business logic layer), Streamlit (EXISTS), pynwb (EXISTS), neuroconv (EXISTS), ndx-fiber-photometry (EXISTS), dandi-cli, elabapi-python (CRITICAL for launch), Celery (NEW with dynamic scaling), Redis (NEW), watchfiles (upgrade from watchdog)
**Storage**: Local filesystem (IMPLEMENTED), OneDrive/Box adapters (Phase 3)
**Testing**: pytest with pytest-asyncio; E2E tests run on production systems with clearly marked test data on every commit (NO MOCKS)
**Target Platform**: Linux server (production), Windows (development support)
**Project Type**: Web application monorepo (backend API + operator UI + workers) - MIGRATION from Streamlit-only architecture with semi-automatic workflow and manual approval gates
**Performance Goals**: <5 min sync latency (ELN → Dir), <10 sec metadata extraction, <10 min NWB packaging (P95), >95% DANDI upload success, error-free uploads prioritized over speed
**Constraints**: NIH data governance (PII/PHI included as required for NWB compliance), NWB schema compliance with configurable scope (raw/processed/both), DANDI rate limits (chunked uploads <256 MiB), idempotent operations, structured logging with request_id/subject_id/entry_id, video handling as separate MP4 assets
**Scale/Scope**: Dynamic worker scaling (no fixed limit), datasets up to 10GB, multi-lab deployment, TDT tank + AnyMaze + video processing with MP4 compression, hybrid sync (webhooks + polling)

**Critical Migration Requirements**:
- Migrate package manager: `uv` → `pixi` (gradual module-by-module, constitution requirement)
- Upgrade Python: 3.11 → 3.13 (direct, high risk, no pre-testing, constitution requirement)
- Refactor architecture: Streamlit-only → FastAPI + Streamlit microservices with shared business logic layer (DRY)
- Preserve existing functionality: LabArchives integration, TDT processing, laboratory directory structure templates, custom widget parsers
- Extract reusable components: LabArchives API wrapper as separate PyPI package
- Add eLabFTW support: CRITICAL for launch, move to M1/M2 from M3
- Rollback strategy: Keep `archiveflow-legacy` branch frozen, smoke tests for critical paths

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

**MIGRATION NOTE**: Existing `archiveflow/` module will be refactored into new structure while preserving functionality.

```text
archiveflow/                         # EXISTING CODE (to be refactored)
├── api.py                           # LabArchives API wrapper → migrate to adapters/eln/labarchives/
├── structure.py                     # Tejeda schemas → migrate to app/models/ and preserve
├── behavior_widget.py               # Widget parser → migrate to adapters/eln/labarchives/parser.py
├── tejeda_schemas.py                # TDT parsing → migrate to nwb/preprocessing/
├── photometry.py                    # Signal processing → migrate to nwb/preprocessing/
├── signal_processing.py             # → migrate to nwb/preprocessing/
├── analysis.py                      # → preserve in nwb/analysis/
├── app_extraction.py                # → refactor into workers/tasks/
├── app_processing.py                # → refactor into workers/tasks/
├── config.py                        # → migrate to app/config.py
├── status.py                        # → migrate to app/services/
└── utils.py                         # → migrate to app/utils/

Login.py                             # EXISTING Streamlit OAuth entry → migrate to ui/
pages/                               # EXISTING Streamlit pages → migrate to ui/pages/
├── 1_Select_Experiment.py           # → ui/pages/1_Subjects.py (refactored)
├── 2_Experiment_Status_and_Batch_Processing.py  # → ui/pages/1_Pipeline_Status.py
├── 3_Manual_Extraction.py           # → merge into ui/pages/4_Manual_Triggers.py
├── 4_Data_Processing.py             # → merge into ui/pages/4_Manual_Triggers.py
├── 5_Behavior_Map.py                # → preserve in ui/pages/5_Behavior_Analysis.py (NEW)
├── 6_Behavior_Analysis.py           # → preserve in ui/pages/5_Behavior_Analysis.py (NEW)
├── 7_Subject_Status.py              # → ui/pages/2_Subjects.py
└── 8_Data_Export.py                 # → merge into ui/pages/6_Export.py (NEW)

app/                                 # FastAPI backend (NEW)
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

**Constitution Conflicts Requiring Migration**:

| Violation | Required Change | Justification | Impact |
|---|---|---|---|
| Package Manager (`uv` → `pixi`) | Rewrite `pyproject.toml` and dependency management as `pixi.toml` | Constitution Principle IV (NON-NEGOTIABLE) | Medium - Affects all dependency installation, CI/CD, developer workflow |
| Python Version (3.11 → 3.13) | Update all code, test compatibility, update CI images | Constitution Principle IV (NON-NEGOTIABLE) | Low-Medium - Mostly compatible, need to test for breaking changes |
| Architecture (Streamlit-only → FastAPI+Streamlit) | Refactor into microservices, add FastAPI backend, extract business logic from UI | Constitution requirement for API endpoints (FR-020) | High - Major architectural change, but preserves existing UI functionality |

**Refactoring Complexity**:

| Component | Existing Lines | Migration Strategy | Risk |
|---|---|---|---|
| LabArchives API (`archiveflow/api.py`) | ~800 | Extract to `adapters/eln/labarchives/`, consider separate PyPI package | Low - Well-tested, isolated |
| TDT Processing (`tejeda_schemas.py`, `photometry.py`) | ~1500 | Migrate to `nwb/preprocessing/`, preserve signal processing pipelines | Low - Isolated processing logic |
| Streamlit UI (8 pages) | ~2000 | Refactor to call FastAPI backend, preserve UI/UX | Medium - Need to retrofit API calls |
| Widget Parsers (`behavior_widget.py`) | ~500 | Preserve as-is in `adapters/eln/labarchives/parser.py` | Low - Tejeda-specific, stable |

## Phase -1: Codebase Migration & Architecture Refactoring

**NEW PHASE** (must complete before Phase 0)

**Goal**: Migrate ArchiveFlow prototype to constitutional compliance and new architecture while preserving all working functionality.

**Duration**: 2 weeks

**Deliverables**:
- `pixi.toml` with all dependencies migrated from `uv`
- Python 3.13 compatibility verified
- FastAPI backend skeleton with health endpoints
- Refactored `adapters/eln/labarchives/` module from `archiveflow/api.py`
- Preserved TDT processing in `nwb/preprocessing/`
- Updated Streamlit UI to work with new structure
- All existing tests passing

### Migration Tasks

**M-1: Package Manager Migration (`uv` → `pixi`)**
- Extract all dependencies from `pyproject.toml` and `uv.lock`
- Create `pixi.toml` with equivalent dependency specifications
- Define pixi tasks: `api`, `ui`, `test`, `lint`, `fmt`, `typecheck`
- Update all documentation and scripts to use `pixi run` commands
- Update CI/CD workflows to use pixi
- Remove `uv` references and lock files

**M-2: Python Version Upgrade (3.11 → 3.13) - DIRECT MIGRATION, HIGH RISK**
- Update `pixi.toml` to specify Python 3.13
- Direct migration without pre-testing (fastest approach, high risk)
- Update type hints if needed for 3.13 strict mode
- Update CI images to Python 3.13
- Document any breaking changes or required code modifications as they occur
- Accept risk of runtime failures in exchange for faster migration

**M-3: Directory Structure Refactoring with Shared Business Logic Layer**
- Create new directory structure: `app/`, `ui/`, `workers/`, `adapters/`, `nwb/`, `dandi/`
- Create `app/services/` as shared business logic layer callable by both FastAPI and Streamlit (DRY architecture)
- Migrate `archiveflow/api.py` → `adapters/eln/labarchives/adapter.py`
- Migrate `archiveflow/behavior_widget.py` → `adapters/eln/labarchives/parser.py`
- Migrate `archiveflow/structure.py` → `app/models/` (preserve laboratory directory schemas as templates)
- Migrate `archiveflow/tejeda_schemas.py` → `nwb/preprocessing/tdt_parser.py`
- Migrate `archiveflow/photometry.py` → `nwb/preprocessing/signal_processing.py`
- Migrate `archiveflow/config.py` → `app/config.py`
- Migrate `archiveflow/status.py` → `app/services/status_service.py`
- Preserve existing Streamlit pages in `ui/pages/` with minimal changes
- Extract business logic from UI components into shared services layer

**M-4: FastAPI Backend Skeleton**
- Create `app/main.py` with ASGI app factory
- Implement health check endpoint: `GET /health`
- Implement basic status endpoint: `GET /v1/status/{subject_id}`
- Configure CORS for Streamlit UI access
- Set up dependency injection for adapters
- Add structured logging configuration (JSON format)

**M-5: Streamlit UI Retrofit**
- Update `ui/Home.py` (from `Login.py`) to work with new structure
- Update page imports to reference new module structure
- Test OAuth2 flow still works
- Preserve all 8 existing pages with minimal changes
- Document UI → API integration points for Phase 2

**M-6: LabArchives API Wrapper Extraction (Optional)**
- Evaluate feasibility of extracting `adapters/eln/labarchives/` as separate package
- Document API surface for reusability
- Defer actual PyPI publication to post-MVP
- Ensure adapter implements Protocol interface for swappability

**M-7: Test Migration with Smoke Tests**
- Migrate existing tests to new structure
- Update imports to reference new module paths
- Ensure all unit tests pass with Python 3.13
- Add smoke tests covering critical paths for rollback validation
- Document any test failures or compatibility issues
- Add pixi task: `pixi run test`
- Configure E2E tests to run on production systems with clearly marked test data

**M-8: eLabFTW Adapter Implementation (MOVED FROM M3, CRITICAL FOR LAUNCH)**
- Implement eLabFTW adapter using elabapi-python SDK
- API key authentication and entry retrieval
- Metadata parsing from eLabFTW entries (RESTful API)
- Hybrid design: standard interface with optional eLabFTW-specific extensions
- Status update logging to eLabFTW entries
- Unit and integration tests for eLabFTW adapter
- This is CRITICAL and must be completed in M1/M2 timeline

**Acceptance Criteria**:
- ✅ `pixi install` successfully installs all dependencies (gradual module-by-module migration)
- ✅ `pixi run test` runs all existing tests and passes (including smoke tests)
- ✅ Python 3.13 compatibility verified (accepting high risk of runtime issues)
- ✅ FastAPI backend starts with shared business logic layer and responds to health checks
- ✅ Streamlit UI starts, displays existing pages, and calls shared business logic
- ✅ LabArchives OAuth2 flow works end-to-end
- ✅ TDT parsing and signal processing functions work unchanged
- ✅ Constitution compliance: no `uv`, `pip`, `conda` references in codebase
- ✅ All existing ArchiveFlow functionality preserved
- ✅ `archiveflow-legacy` branch frozen for rollback strategy

## Phase 0: Research & Discovery

**Goal**: Investigate external APIs, data formats, and integration patterns to derisk technical unknowns.

**Duration**: 1 week

**Deliverables**: `specs/heet-dev/research.md`

### Research Areas

1. **LabArchives API Integration** ✅ **MOSTLY COMPLETE** (validate and document)
   - ✅ OAuth2 authentication implemented (`archiveflow/api.py`)
   - ✅ Entry retrieval, notebook traversal working
   - ✅ Custom widget parsing for structured behavior forms implemented
   - 🟡 Document rate limits and pagination patterns (need formal testing)
   - ❌ Status update/logging API (append notes) - needs implementation
   - 🟡 Error handling exists, retry patterns need formalization with configurable policies

2. **eLabFTW API Integration - CRITICAL FOR LAUNCH**
   - `elabapi-python` SDK authentication (API key management)
   - Entry retrieval and filtering (by date, user, tags)
   - Metadata extraction from structured fields and Markdown content
   - Hybrid adapter design: standard interface with optional eLabFTW-specific extensions
   - Status field updates vs. comment appending
   - Webhook support for real-time updates (preferred over polling)
   - Differences from LabArchives API patterns
   - THIS IS CRITICAL and moved to M1/M2 priority

3. **TDT Tank Data Processing** ✅ **IMPLEMENTED** (document and validate)
   - ✅ TDT tank folder parser implemented (`archiveflow/tejeda_schemas.py`)
   - ✅ Stream extraction: TTL events, 405A isosbestic, 470D experimental (`archiveflow/photometry.py`)
   - ✅ Signal processing pipelines implemented (`archiveflow/signal_processing.py`)
   - ✅ Timestamp alignment working for laboratory conventions
   - 🟡 Document integration with neuroconv TDTDataInterface (validate compatibility)
   - 🟡 Sampling rate extraction implemented, needs formal validation

4. **NWB Schema Mapping (ndx-fiber-photometry) with Configurable Scope**
   - `ndx-fiber-photometry` extension schema (FiberPhotometry, FiberPhotometryResponseSeries)
   - Required metadata fields (subject, session, timestamps, acquisition device)
   - Mapping from TDT tank + ELN metadata → NWB structure
   - Configurable NWB scope per experiment: raw/processed/both
   - Multi-trial/multi-timepoint handling in NWB
   - pynwb validation using NWB Inspector tool (not static golden dataset)
   - Video handling as separate DANDI assets (MP4 format with light compression)

5. **File System Watcher Patterns with Auto-Organization** 🟡 **PARTIALLY IMPLEMENTED** (upgrade and automate)
   - ✅ `watchdog` library used in ArchiveFlow (need to migrate to `watchfiles`)
   - 🟡 Readiness detection exists but needs formalization (experiment type rules)
   - 🟡 Manual trigger patterns exist, need semi-automatic event-driven triggers with approval gates
   - 🟡 Large file handling tested informally, needs performance validation for video files
   - 🟡 File modification handling exists, needs edge case testing
   - 🆕 Auto-organize misplaced files to correct locations with researcher notifications
   - 🆕 Strict cohort naming enforcement with rejection of non-compliant names

6. **DANDI Upload Best Practices with Video Handling**
   - `dandi-cli` vs. API usage (resumable uploads, chunking)
   - Dandiset metadata YAML structure and validation
   - Rate limiting and throttling strategies
   - Configurable retry logic per job type (not fixed 3 retries)
   - Error-free uploads prioritized over speed
   - Checksum verification and retry failed only (not all)
   - Asset ID retrieval and logging back to ELN
   - Video assets as separate DANDI uploads (MP4 format, light compression, required)

7. **Celery Architecture for Long-Running Jobs with Dynamic Scaling**
   - Redis broker configuration (persistence, memory limits)
   - Task routing (separate queues for sync, preprocessing, packaging, upload)
   - Configurable retry policies per job type (exponential backoff, max retries, dead-letter queue)
   - Idempotency key patterns (composite keys: subject_id + session_date)
   - Dynamic worker scaling (no fixed capacity limit)
   - Manual approval gates before NWB generation and upload
   - Researcher-controlled pipeline pause for specific experiments
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

**ACCELERATED** due to existing ArchiveFlow implementation.

**Scope**:
- ✅ LabArchives ELN adapter (ALREADY IMPLEMENTED - migrate from `archiveflow/api.py`)
- 🆕 eLabFTW ELN adapter (CRITICAL FOR LAUNCH - moved from M3 to M1)
- ✅ Local storage adapter (ALREADY IMPLEMENTED - migrate from `archiveflow/structure.py`)
- ✅ TDT tank parsing (ALREADY IMPLEMENTED - migrate from `archiveflow/tejeda_schemas.py`)
- ✅ Streamlit UI with 8 pages (ALREADY IMPLEMENTED - retrofit to call shared business logic layer)
- 🆕 FastAPI backend with sync, status, health endpoints and shared business logic layer (NEW)
- 🆕 NWB packaging with configurable scope (raw/processed/both) using pynwb + ndx-fiber-photometry (NEW)
- 🆕 pynwb validation using NWB Inspector tool (NEW)
- 🟡 Structured logging (upgrade from existing logging to JSON format)
- 🟡 Unit and integration tests (migrate existing tests, add smoke tests)
- 🆕 CI pipeline (lint, typecheck, unit, integration) with E2E on production systems (NEW)

**Deliverables**:
- Working LabArchives/eLabFTW → Local Dir → NWB pipeline (✅ Laboratory directory structure template preserved)
- NWB files with configurable scope passing NWB Inspector validation (🆕 NEW)
- API documentation (OpenAPI spec) (🆕 NEW)
- Developer setup guide (quickstart.md) (🟡 Update existing README)
- eLabFTW adapter fully functional (CRITICAL)

**Acceptance Criteria**:
- ✅ User Story 1 acceptance scenarios pass (ELN sync to directory with manual approval) - UPGRADE FROM EXISTING
- 🆕 User Story 3 acceptance scenarios pass (NWB generation with configurable scope and validation) - NEW
- 🆕 User Story 5 acceptance scenarios pass (eLabFTW support, CRITICAL) - NEW
- ✅ Constitution Gates 1, 4, 5, 6, 7 pass (Python 3.13 after direct migration, Pixi-only)
- ✅ Existing ArchiveFlow functionality preserved (OAuth, TDT parsing, UI)
- 🆕 Shared business logic layer callable by both API and UI

**Timeline Adjustment**: Expected 3-4 weeks due to eLabFTW adapter being CRITICAL and moved into M1.

### Milestone 2: Automation - Watcher + DANDI Upload (Weeks 5-8)

**Goal**: Automate preprocessing trigger and DANDI upload with retry logic.

**PARTIALLY ACCELERATED** due to existing preprocessing and watcher infrastructure.

**Scope**:
- 🟡 File system watcher (migrate `watchdog` → `watchfiles`, add semi-automatic triggers with manual approval gates)
- 🆕 Auto-organization of misplaced files with notifications
- 🆕 Strict cohort naming enforcement
- ✅ Preprocessing logic (ALREADY IMPLEMENTED - wrap in Celery tasks)
- 🆕 Celery workers with dynamic scaling (sync, preprocessing, packaging, upload tasks) (NEW)
- 🆕 Redis broker configuration (NEW)
- 🆕 DANDI uploader with video handling (dandi-cli wrapper with resumable uploads, MP4 compression) (NEW)
- 🆕 DANDI validation gate (NEW)
- 🆕 Configurable retry policies per job type (exponential backoff, idempotency keys, retry failed only) (NEW)
- 🆕 Manual approval UI components before NWB generation and upload (NEW)
- 🆕 Researcher-controlled pipeline pause functionality (NEW)
- 🟡 ELN status logging (upgrade existing status tracking to write back to LabArchives/eLabFTW)
- 🆕 Provenance tracking (Git SHA, pixi lock hash) (NEW)
- 🆕 E2E tests (LabArchives/eLabFTW + DANDI with real APIs on production systems) (NEW)

**Deliverables**:
- Semi-automatic pipeline trigger on data readiness with manual approval gates
- Auto-organization of misplaced files with notifications
- DANDI upload with configurable retry, video handling, and error-free prioritization
- Dynamic worker scaling with no fixed capacity limit
- Researcher-controlled pipeline pause functionality
- Provenance records in NWB and ELN
- E2E test suite running on production systems with clearly marked test data

**Acceptance Criteria**:
- User Story 2 acceptance scenarios pass (watcher trigger with auto-organization)
- User Story 4 acceptance scenarios pass (DANDI upload with manual approval and video handling)
- Constitution Gates 2, 3, 6 pass (DANDI dry-run, spec alignment, idempotency)
- DANDI upload success rate >95% with error-free uploads prioritized
- Workers scale dynamically without hitting fixed capacity limits
- Manual approval gates functional in UI

### Milestone 3: Storage Backend Support (Weeks 9-12)

**Goal**: Add OneDrive/Box storage adapters and enhance observability.

**NOTE**: eLabFTW support moved to M1 as CRITICAL for launch.

**Scope**:
- OneDrive storage adapter (OAuth2, file upload/download)
- Box storage adapter (OAuth2, file upload/download)
- Hybrid sync strategy implementation (webhooks preferred, polling as fallback)
- Enhanced observability (sync latency metrics, upload success rate tracking)
- Multi-storage E2E tests (LabArchives + OneDrive, eLabFTW + Box)
- Adapter interface documentation

**Deliverables**:
- Working LabArchives/eLabFTW → OneDrive/Box → NWB → DANDI pipeline
- Hybrid sync strategy (webhooks + polling) fully functional
- Enhanced metrics and monitoring dashboards
- Adapter selection documentation (quickstart.md update)
- Multi-backend test suite

**Acceptance Criteria**:
- Storage adapters pass contract compliance tests
- Hybrid sync strategy works with both webhook and polling modes
- Observability metrics tracked (sync latency <5 min P95, upload success >95%)
- Constitution Gate 3 pass (multi-backend modular design)

### Milestone 4: Production Hardening (Weeks 13-16)

**Goal**: Prepare for production deployment with monitoring, security, and operational tooling.

**Scope**:
- Secrets management (environment variables + `.env` for MVP, modular stubs for cloud migration)
- Streamlit dashboard enhancements (log filtering, manual job triggers, approval interfaces)
- Docker images (API, UI, worker)
- Kubernetes manifests (deployments, services, ingress)
- CI/CD pipeline (Docker build, push, deploy) with E2E on production systems
- Pre-commit hooks (ruff, mypy, secrets detection)
- Production runbooks (onboarding, token rotation, troubleshooting, lab-specific customization)
- NWB Inspector validation in CI (not static golden dataset)

**Deliverables**:
- Production-ready container images
- Kubernetes deployment manifests
- Operator runbooks (including lab-specific customization guides)
- Full CI/CD pipeline with constitution gates and E2E on production systems
- Security audit (secrets scanning, dependency vulnerabilities)

**Acceptance Criteria**:
- All constitution gates pass in CI
- NWB Inspector validation passes in CI (not static golden dataset)
- E2E tests run on production systems with clearly marked test data
- Docker images build and run successfully
- Observability metrics tracked (sync latency <5 min P95, error-free uploads prioritized)
- Pre-commit hooks prevent secret commits
- Manual approval gates fully functional
- Video handling as separate MP4 assets validated

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

### E2E Tests (Real Systems - NO MOCKS, Production Systems with Test Data)

**Coverage Target**: Happy path scenarios

**Scope**:
- LabArchives API sync (real NIH instance with clearly marked test data)
- eLabFTW API sync (real instance with clearly marked test data)
- Full pipeline: ELN → Dir → NWB → DANDI (test data on production systems)
- DANDI upload (test dandiset with clearly marked test data)
- ELN status logging (verify updates in real ELN)
- Manual approval gates and pause functionality
- Video handling as separate MP4 assets

**Tools**: pytest with `@pytest.mark.e2e`, real credentials (from secrets), run on every commit

**Run Command**: `pixi run e2e`

**Important**: Tests run on production systems with clearly marked test data. No mocking allowed.

### NWB Validation Strategy

**Purpose**: CI gate for NWB validation using NWB Inspector tool (not static golden dataset)

**Approach**:
- Use NWB documentation ontology as validation source
- Use NWB Inspector tool for automated validation
- No static golden dataset (too brittle, maintenance burden)

**CI Gate**: Generate NWB from test data → NWB Inspector validation → `dandi upload --dry-run` (MUST pass)

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

**UPDATED SEQUENCE** (reflects ArchiveFlow migration and user decisions):

1. **Approve Plan**: Review plan.md with stakeholders (Josh Lawrimore, DSST team, collaborating laboratories) and approve migration strategy
2. **Phase -1 Migration** (2 weeks): Execute codebase migration (`uv` → `pixi` gradual, Python 3.11 → 3.13 direct/high risk, architecture refactoring with shared business logic, eLabFTW adapter implementation)
3. **Phase 0 Research** (1 week, ACCELERATED): Validate existing implementations, document LabArchives/TDT patterns, research NWB packaging with configurable scope, research NIH-wide directory standards
4. **Phase 1 Design** (2 weeks): Define data models (leverage laboratory directory templates), contracts, update quickstart guide
5. **Generate Tasks**: Run `/tasks` command to generate tasks.md from this plan
6. **Milestone 1 Kickoff** (3-4 weeks, EXTENDED for eLabFTW): Complete NWB packaging with configurable scope, eLabFTW adapter, manual approval gates

**Key Stakeholder Approvals Needed**:
- ✅ Josh Lawrimore: Acknowledge ArchiveFlow contribution, approve refactoring approach
- ✅ Collaborating Laboratories: Approve directory structure template and workflow continuity
- ✅ DSST Leadership: Approve timeline adjustments for eLabFTW priority and resource allocation

**Key Decisions Implemented**:
- Direct Python 3.13 migration (high risk, fastest)
- Gradual module-by-module uv→pixi migration (safest)
- eLabFTW as CRITICAL for launch (moved to M1/M2)
- Semi-automatic workflow with manual approval gates
- Configurable NWB scope (raw/processed/both)
- Video handling as separate MP4 assets
- Hybrid sync strategy (webhooks + polling)
- Dynamic worker scaling
- E2E on production systems with test data
- NWB Inspector validation (no static golden dataset)
- Environment variables + `.env` for MVP secrets
- Rollback via frozen `archiveflow-legacy` branch

---

**Document Version**: 2.0 (Updated for ArchiveFlow Integration)
**Last Updated**: 2025-10-29
**Author**: Claude (via /plan command)
**Original ArchiveFlow**: Josh Lawrimore (NIMH DSST)
**Approved By**: [Pending Stakeholder Review]
