# ELN to DANDI Pipeline Automation - Project Overview

**Project Name**: elabftw-app
**Version**: 1.0.0
**Status**: Planning & Design Complete, Ready for Implementation
**Last Updated**: 2025-10-29

---

## Executive Summary

The **ELN to DANDI Pipeline Automation** project automates the protocol-to-publication workflow for neuroscience fiber photometry experiments. It bridges the gap between Electronic Lab Notebooks (ELNs) and the DANDI neuroscience data archive by automatically generating NWB (Neurodata Without Borders) compliant files from experimental records.

### Problem Statement

NIH intramural investigators are required to transition to electronic records for all experiments (June 2024 mandate). Research laboratories conducting fiber photometry behavioral experiments in mice currently face:
- **10+ minutes** of manual metadata handling per experiment
- **Hours** of manual data packaging and validation
- **Inconsistent** data formatting and incomplete provenance tracking
- **Difficulty sharing** data in standardized formats for collaboration

### Solution

An integrated pipeline that:
1. **Syncs** experimental metadata from ELNs (LabArchives, eLabFTW) to structured directories
2. **Watches** for raw data files and automatically triggers preprocessing
3. **Packages** metadata and data into NWB-compliant files with full provenance
4. **Uploads** validated NWB files to DANDI archive with researcher approval
5. **Logs** all operations back to the ELN for complete audit trail

### Expected Impact

- ⏱️ **95% reduction** in manual data packaging time (hours → minutes)
- ✅ **100% NWB/DANDI compliance** for supported experiments
- 🔄 **<5 minute sync latency** from ELN update to structured directory
- 📊 **Complete provenance tracking** (code versions, transformations, metadata)
- 🤝 **Multi-lab support** through modular ELN and storage adapters

---

## What We're Building

### Core Workflow

```
┌─────────────────────┐
│  Researcher         │
│  Creates ELN Entry  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐      ┌──────────────────┐
│  ELN API Sync       │◄─────┤ LabArchives      │
│  (every 5 min or    │      │ eLabFTW          │
│   webhook trigger)  │      └──────────────────┘
└──────────┬──────────┘
           │ Parse metadata
           ▼
┌─────────────────────┐
│  Create Structured  │
│  Directory          │
│  (Surgery/Behavior/ │
│   Photometry/etc.)  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Researcher Drops   │
│  Raw Data Files     │
│  (TDT tanks, CSVs,  │
│   videos)           │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  File Watcher       │
│  Detects Readiness  │
│  (all required      │
│   files present)    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Manual Approval    │◄─── Researcher reviews
│  (Operator UI)      │     and approves
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Preprocessing      │
│  (TDT extraction,   │
│   signal processing)│
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  NWB File           │
│  Generation         │
│  (ndx-fiber-        │
│   photometry)       │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  NWB Validation     │
│  (pynwb.validate()  │
│   + NWB Inspector)  │
└──────────┬──────────┘
           │ Pass
           ▼
┌─────────────────────┐
│  Manual Approval    │◄─── Researcher reviews
│  for Upload         │     NWB file
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐      ┌──────────────────┐
│  DANDI Upload       │─────►│ DANDI Archive    │
│  (automatic after   │      │ (Public Repo)    │
│   approval)         │      └──────────────────┘
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Log Status to ELN  │
│  (DANDI asset ID,   │
│   code version)     │
└─────────────────────┘
```

### Key Features

#### 1. Multi-ELN Support (CRITICAL)
- **LabArchives**: NIH instance with OAuth2 authentication, custom widget parsing
- **eLabFTW**: Open-source ELN with API key authentication, metadata templates
- Modular adapter architecture for future ELN integrations

#### 2. Automated Directory Management
- Lab-specific directory schemas (Surgery, Behavior, Photometry, Histology, Metadata)
- Cohort-based organization with strict naming enforcement
- Auto-organization of misplaced files with notifications

#### 3. NWB File Generation
- **Configurable scope**: raw data / preprocessed signals / both (per-experiment)
- **ndx-fiber-photometry** extension for fiber photometry experiments
- Complete metadata: subject info, surgery details, session data, device specs
- Full provenance tracking (git commit SHA, processing parameters)

#### 4. DANDI Integration
- Automatic upload after validation and manual approval
- Video handling: separate MP4 assets with light compression
- Retry logic: configurable per job type, retry failed only
- Upload tracking: DANDI asset IDs logged to ELN

#### 5. Semi-Automatic Workflow
- **Manual approval gates**: Before NWB generation and DANDI upload
- **Researcher control**: Pause pipeline for specific experiments
- **Ambiguous case handling**: Consult researcher for missing metadata or errors

#### 6. Observability
- Structured JSON logging (request_id, subject_id, session_id)
- Metrics: sync latency (<5 min target), DANDI upload success rate (>95%)
- Operator dashboard: Streamlit UI for monitoring and manual interventions

---

## Technical Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND LAYER                            │
├─────────────────────────────────────────────────────────────┤
│  Streamlit Operator UI                                       │
│  ├── Pipeline Status Dashboard                               │
│  ├── Metadata Browser                                        │
│  ├── Manual Approval Interface                               │
│  └── Configuration Management                                │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                 BUSINESS LOGIC LAYER                         │
│                (Shared by Streamlit + FastAPI)               │
├─────────────────────────────────────────────────────────────┤
│  ├── ELN Service (polling/webhooks, metadata extraction)     │
│  ├── Directory Service (structure creation, file organization)│
│  ├── Pipeline Service (orchestration, state management)      │
│  ├── NWB Service (packaging, validation, NWB Inspector)      │
│  └── DANDI Service (upload, retry logic, manifest)           │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        │                         │
        ▼                         ▼
┌──────────────────┐    ┌──────────────────┐
│  FastAPI Backend │    │  Celery Workers  │
│  REST Endpoints  │    │  Background Jobs │
│  ├── /v1/sync    │    │  ├── Preprocessing│
│  ├── /v1/status  │    │  ├── NWB Packaging│
│  ├── /v1/upload  │    │  └── DANDI Upload │
│  └── /webhook/eln│    └──────────────────┘
└──────────────────┘              │
                                  │
                                  ▼
                        ┌──────────────────┐
                        │  Redis Task Queue│
                        │  & Result Backend│
                        └──────────────────┘
```

### Adapter Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    ADAPTER LAYER                             │
├─────────────────────────────────────────────────────────────┤
│  ELN Adapters (Protocol-based)                               │
│  ├── LabArchives Adapter                                     │
│  │   ├── OAuth2 authentication                               │
│  │   ├── XML/REST API calls                                  │
│  │   └── Custom widget parsing                               │
│  └── eLabFTW Adapter                                         │
│      ├── API key authentication                              │
│      ├── RESTful API calls                                   │
│      └── Metadata template parsing                           │
│                                                               │
│  Storage Adapters (Protocol-based)                           │
│  ├── Local Filesystem (aiofiles)                             │
│  ├── OneDrive (Microsoft Graph API)                          │
│  └── Box (Box SDK)                                           │
└─────────────────────────────────────────────────────────────┘
```

### Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Runtime** | Python 3.13 | NON-NEGOTIABLE (constitution) |
| **Package Manager** | pixi | NON-NEGOTIABLE (constitution) |
| **Backend API** | FastAPI | Async REST endpoints |
| **Operator UI** | Streamlit | Dashboard and manual interventions |
| **Background Jobs** | Celery + Redis | Long-running tasks (preprocessing, upload) |
| **File Watching** | watchfiles | Directory monitoring (Rust-based, 10x faster than watchdog) |
| **ELN Integration** | LabArchives wrapper, elabapi-python | Official SDKs |
| **NWB Packaging** | pynwb, neuroconv, ndx-fiber-photometry | NWB standard libraries |
| **DANDI Upload** | dandi-cli, dandi SDK | DANDI official tools |
| **Signal Processing** | TDT SDK, GuPPy | Fiber photometry analysis |
| **Testing** | pytest, pytest-asyncio | Unit, integration, E2E |
| **Linting** | ruff | Code quality |
| **Type Checking** | mypy | Static analysis |

---

## Project Phases & Timeline

### Phase -1: Codebase Migration (2 weeks)

**Objective**: Migrate existing ArchiveFlow prototype to constitutional compliance

**Background**: ArchiveFlow is a working prototype (~4,800 LOC) built by Josh Lawrimore with LabArchives integration, TDT processing, and Streamlit UI. It uses `uv` (not `pixi`) and Python 3.11 (not 3.13).

**Tasks**:
- **M-1**: Migrate dependencies from `uv` to `pixi` (gradual, module-by-module)
- **M-2**: Upgrade Python 3.11 → 3.13 (direct migration, HIGH RISK, no pre-testing)
- **M-3**: Refactor `archiveflow/` into new structure (`app/`, `ui/`, `workers/`, `adapters/`)
- **M-4**: Create FastAPI backend skeleton with shared business logic layer
- **M-5**: Retrofit Streamlit UI to use shared business logic
- **M-6**: Extract LabArchives API wrapper for separate PyPI package
- **M-7**: Migrate tests to new structure
- **M-8**: **NEW** Implement eLabFTW adapter (CRITICAL, moved from M3)

**Migration Strategy**: Incremental refactoring with parallel operation (both ArchiveFlow and new system running)

**Rollback**: Branch strategy - keep `archiveflow-legacy` frozen

---

### Phase 0: Research (1 week)

**Objective**: Validate technical approaches and resolve implementation unknowns

**Research Areas** (most already validated by ArchiveFlow):
1. ✅ LabArchives API integration (VALIDATED by ArchiveFlow)
2. 🆕 eLabFTW API integration (NEW - critical for launch)
3. ✅ TDT tank data processing (VALIDATED by ArchiveFlow)
4. 🟡 NWB schema mapping (libraries present, packaging logic needed)
5. 🟡 File system watcher patterns (watchdog → watchfiles upgrade)
6. 🆕 DANDI upload best practices (not implemented in ArchiveFlow)
7. 🆕 Celery architecture for scientific pipelines (not in ArchiveFlow)
8. 🆕 Multi-storage backend patterns (OneDrive, Box)

**Output**: `research.md` with findings, decisions, and rationales

---

### Milestone 1: MVP - Multi-ELN + Local NWB Generation (3-4 weeks)

**ACCELERATED** (due to ArchiveFlow foundation)

**Deliverables**:
- ✅ LabArchives ELN adapter (ALREADY IMPLEMENTED in ArchiveFlow)
- 🆕 eLabFTW adapter (MOVED FROM M3, CRITICAL FOR LAUNCH)
- 🆕 Shared business logic layer (DRY architecture)
- ✅ Directory creation from metadata (ALREADY IMPLEMENTED)
- 🆕 Configurable NWB file generation (raw/processed/both)
- 🆕 NWB Inspector validation (no static golden dataset)
- 🆕 Manual approval UI for NWB generation
- 🟡 Manual upload trigger via UI (existing Streamlit pages retrofitted)

**Cut Line**: DANDI automation can be manual for MVP

---

### Milestone 2: Automation - Watcher + DANDI Upload (4-5 weeks)

**PARTIALLY ACCELERATED** (preprocessing exists, needs Celery wrapping)

**Deliverables**:
- 🆕 Semi-automatic file watcher with manual approval gates
- 🆕 Hybrid sync strategy (webhooks preferred, polling fallback)
- 🟡 Background job orchestration (Celery) - wraps existing preprocessing
- 🆕 Configurable retry policies per job type (retry failed only)
- 🆕 Dynamic worker scaling (no fixed concurrent limit)
- 🆕 DANDI upload automation with manual approval
- 🆕 Video handling: separate MP4 assets with light compression
- 🆕 Auto-organization of misplaced files with notifications
- 🆕 Strict cohort naming enforcement
- 🆕 Researcher-controlled pipeline pause
- 🆕 ELN status update logging (DANDI asset IDs, code versions)

**Cut Line**: Multi-storage backends (OneDrive/Box) can slip

---

### Milestone 3: Storage Backend Support (3-4 weeks)

**Renamed** (eLabFTW moved to M1)

**Deliverables**:
- 🆕 OneDrive storage adapter (Microsoft Graph API)
- 🆕 Box storage adapter (Box SDK)
- 🆕 Storage backend selection via configuration
- 🆕 Async file operations for all backends
- ✅ Full E2E tests for both LabArchives and eLabFTW (multi-ELN validated)

**Cut Line**: Advanced preprocessing pipelines can slip

---

### Milestone 4: Production Hardening (2-3 weeks)

**Deliverables**:
- Performance optimization (signal processing, NWB generation)
- Error recovery and retry logic refinement
- Monitoring and alerting (Prometheus/Grafana integration)
- Documentation and operator training materials
- Security review (secrets management, NIH data boundary)
- Load testing (concurrent experiments, DANDI upload throughput)

---

### Total Timeline: 14-19 weeks

**With ArchiveFlow foundation**: 30-40% reduction vs. building from scratch

---

## Constitution Compliance

The project adheres to 7 core principles defined in [`.specify/memory/constitution.md`](.specify/memory/constitution.md):

### ✅ I. Mission-Driven Architecture
All features support ELN → directory → NWB → DANDI workflow. No unnecessary complexity.

### ✅ II. Data Standards Compliance (NON-NEGOTIABLE)
- NWB format mandatory (pynwb, neuroconv, ndx-fiber-photometry)
- All NWB files must pass `pynwb.validate()` before upload
- DANDI upload automation required
- All transformations auditable with provenance

### ✅ III. Multi-ELN Support
- Modular adapters: LabArchives (NIH wrapper), eLabFTW (elabapi-python SDK)
- New ELN integrations must NOT require core pipeline changes
- Each adapter handles authentication, retrieval, status updates independently

### ✅ IV. Python 3.13 & Pixi-Only (NON-NEGOTIABLE)
- Python 3.13 everywhere (production, CI, notebooks, scripts)
- pixi exclusively for dependency management
- All tasks via `pixi run ...`

### ✅ V. Testing Discipline
- Unit/integration tests may use fakes
- **E2E tests MUST use real systems** (LabArchives, eLabFTW, DANDI APIs)
- No mocks in E2E tests
- If real access unavailable, mark as *blocked* (not mocked)
- E2E tests run on every commit

### ✅ VI. Idempotency & Determinism
- Re-running pipeline produces byte-identical NWB files (excluding timestamps)
- Directory watcher handles duplicate events gracefully
- Failed operations safely retryable without corruption
- Code version hashes recorded in ELN logs

### ✅ VII. Observability
- Structured JSON logs (request_id, subject_id, session_id, job_id)
- Sync latency tracked (target: <5 minutes)
- DANDI upload success rate monitored (target: >95%)
- Provenance recorded in NWB files and ELN

---

## Key Decisions & Rationale

### Decision 1: Semi-Automatic Workflow (Not Fully Automatic)

**Decision**: Manual approval gates before NWB generation and DANDI upload

**Rationale**:
- Research data integrity is critical - errors can invalidate experiments
- Researchers need visibility before public data sharing
- Ambiguous cases (missing metadata, file errors) require human judgment
- Provides pause capability for specific experiments

**Impact**: Slightly slower workflow, but safer and more trusted by researchers

---

### Decision 2: eLabFTW as CRITICAL for Launch

**Decision**: Move eLabFTW from Milestone 3 to Milestone 1 (CRITICAL)

**Rationale**:
- Specific collaborating laboratories are blocked without eLabFTW
- Multi-ELN support is core mission, not optional enhancement
- LabArchives-only limits adoption outside NIH

**Impact**: Extends M1 from 2-3 weeks to 3-4 weeks

---

### Decision 3: Configurable NWB Scope

**Decision**: Per-experiment selection of raw/processed/both data in NWB files

**Rationale**:
- Different experiments have different requirements
- Preprocessed-only: smaller files, faster uploads, loses raw data
- Both: comprehensive but very large files
- Researcher choice balances needs

**Impact**: Requires UI for configuration, more complex packaging logic

---

### Decision 4: Hybrid Sync Strategy

**Decision**: Webhooks preferred, polling as fallback

**Rationale**:
- Webhooks provide real-time sync (best UX)
- Not all ELN systems support webhooks reliably
- Polling ensures fallback (5-minute delay acceptable)
- Reduces server load vs. aggressive polling

**Impact**: More complex sync logic, but better performance when webhooks available

---

### Decision 5: Direct Python 3.13 Migration (HIGH RISK)

**Decision**: Migrate to Python 3.13 without pre-testing

**Rationale**:
- Constitution requires Python 3.13 (NON-NEGOTIABLE)
- Pre-testing delays timeline significantly
- Dependencies (pydantic, streamlit, neuroconv) likely compatible
- Risk: numerical instability in signal processing

**Mitigation**: Smoke tests covering critical paths, validation of signal processing outputs post-migration

**Impact**: Faster migration but higher risk of subtle bugs

---

### Decision 6: Lab-Agnostic Design

**Decision**: Remove all explicit "Tejeda Lab" references, make universally applicable

**Rationale**:
- System designed for multiple NIH labs and external collaborators
- Hardcoding lab-specific names limits adoption
- Generic terminology improves maintainability

**Impact**: Requires configurable schemas, but enables multi-lab deployment

---

### Decision 7: Videos as Separate DANDI Assets

**Decision**: Upload videos as separate assets (not embedded in NWB)

**Rationale**:
- Video files are very large (GB-sized)
- Embedding in NWB creates unmanageable file sizes
- DANDI best practice: separate video assets
- Light compression (MP4) balances quality and size

**Impact**: More complex upload logic, but manageable NWB file sizes

---

### Decision 8: Environment Variables for Secrets (MVP)

**Decision**: Use `.env` + `.gitignore` for MVP, not cloud secrets manager

**Rationale**:
- Simpler to implement and debug
- Sufficient security for initial deployment
- Architecture remains modular for future migration to cloud secrets manager
- NIH policies don't mandate specific solution

**Impact**: Less secure than cloud solutions, but acceptable for MVP with migration path

---

## Success Criteria

The project will be considered successful when:

1. ✅ **SC-001**: Metadata handling time reduced from 10+ minutes to <10 seconds
2. ✅ **SC-002**: Manual data packaging time reduced by 95%
3. ✅ **SC-003**: 100% of fiber photometry experiments generate valid NWB files
4. ✅ **SC-004**: 100% of uploaded files pass DANDI validation
5. ✅ **SC-005**: Sync latency averages <5 minutes (ELN → NWB)
6. ✅ **SC-006**: DANDI upload success rate >95%
7. ✅ **SC-007**: All operations include provenance tracking (code versions in NWB + ELN)
8. ✅ **SC-008**: System supports dynamic scaling for concurrent experiments (no fixed limit)
9. ✅ **SC-009**: Researchers can view pipeline status within 10 seconds
10. ✅ **SC-010**: Stable operation with both LabArchives and eLabFTW (multi-ELN validated)

---

## Risk Management

### High Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| **Python 3.13 incompatibility** | Medium | High | Smoke tests post-migration, validate numerical outputs |
| **LabArchives API rate limits** | Medium | Medium | Exponential backoff, respect rate limits, polling interval tuning |
| **DANDI upload failures** | Medium | High | Retry logic with exponential backoff, resumable uploads, manual retry UI |
| **NWB schema evolution** | Low | Medium | Pin ndx-fiber-photometry version, migration scripts for schema updates |
| **Data corruption during refactoring** | Low | Critical | Parallel operation (ArchiveFlow + new system), smoke tests, frozen legacy branch |

### Medium Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| **eLabFTW custom templates** | Medium | Medium | Hybrid adapter design, per-lab parser configs |
| **Multi-storage auth complexity** | Medium | Low | Modular adapters, start with local filesystem |
| **Concurrent processing race conditions** | Low | Medium | File locking, timestamp-based conflict resolution, idempotency keys |

### Reduced Risks (Due to ArchiveFlow Validation)

- ✅ **LabArchives API access**: VALIDATED (working in ArchiveFlow)
- ✅ **TDT processing**: VALIDATED (implemented in ArchiveFlow)
- ✅ **Local storage patterns**: VALIDATED (working directory structure)
- ✅ **Streamlit UI viability**: VALIDATED (8-page UI exists)

---

## Stakeholders & Collaboration

### Primary Stakeholders

- **DSST (Division of Scientific and Statistical Tools)**: Development team
- **Josh Lawrimore, PhD**: ArchiveFlow developer, consultation during migration
- **Collaborating Research Laboratories**: End users (fiber photometry experiments)
- **NIH NIMH**: Institutional sponsor, compliance oversight

### External Dependencies

- **LabArchives**: ELN API access, NIH instance availability
- **eLabFTW**: Open-source ELN, API compatibility
- **DANDI**: Archive API access, upload quotas, staging environment
- **NWB Community**: Schema updates, ndx-fiber-photometry maintenance

---

## Repository Structure

```
elabftw-app/
├── .claude/                    # Claude Code commands and settings
│   ├── commands/
│   │   ├── constitution.md
│   │   ├── specify.md
│   │   ├── plan.md
│   │   └── tasks.md
│   └── settings.local.json
├── .specify/                   # Speckit templates and memory
│   ├── memory/
│   │   └── constitution.md
│   ├── templates/
│   │   ├── spec-template.md
│   │   ├── plan-template.md
│   │   └── tasks-template.md
│   └── scripts/                # PowerShell automation scripts
├── specs/                      # Feature specifications
│   └── 001-eln-to-dandi-pipeline/
│       ├── spec.md             # Feature specification
│       ├── plan.md             # Implementation plan
│       ├── research.md         # Phase 0 research findings
│       ├── data-model.md       # Phase 1 data models
│       ├── quickstart.md       # Phase 1 developer guide
│       ├── contracts/          # API specifications
│       │   ├── eln-adapter.yaml
│       │   ├── storage-adapter.yaml
│       │   ├── api-endpoints.yaml
│       │   └── nwb-schema.json
│       ├── checklists/
│       │   └── requirements.md
│       └── CLARIFICATION_QUESTIONS.md
├── app/                        # FastAPI backend (future)
│   ├── main.py
│   ├── routes/
│   ├── services/               # Shared business logic
│   └── schemas/
├── ui/                         # Streamlit operator UI (future)
│   ├── Home.py
│   └── pages/
├── workers/                    # Celery background jobs (future)
│   └── tasks.py
├── adapters/                   # Modular interfaces (future)
│   ├── eln/
│   │   ├── labarchives/
│   │   └── elabftw/
│   └── storage/
│       ├── local/
│       ├── onedrive/
│       └── box/
├── nwb/                        # NWB packaging (future)
│   ├── packager.py
│   └── schemas/
├── dandi/                      # DANDI uploader (future)
│   └── uploader.py
├── tests/                      # Test suite
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── ArchiveFlow.zip             # Existing prototype codebase
├── pixi.toml                   # Dependency management
├── pyproject.toml              # Project metadata
├── ruff.toml                   # Linting configuration
├── mypy.ini                    # Type checking configuration
├── claude.md                   # CLAUDE.md technical guardrails
├── PROJECT_OVERVIEW.md         # This file
└── README.md                   # Project readme (future)
```

---

## Development Workflow

### Getting Started

1. **Prerequisites**:
   - Python 3.13 installed
   - pixi installed (`curl -fsSL https://pixi.sh/install.sh | bash`)
   - Git configured

2. **Clone Repository**:
   ```bash
   git clone https://github.com/Python-AI-Solutions/elabftw-app.git
   cd elabftw-app
   ```

3. **Install Dependencies**:
   ```bash
   pixi install-pypi
   ```

4. **Run Services** (after implementation):
   ```bash
   pixi run api      # Start FastAPI backend
   pixi run ui       # Start Streamlit UI
   pixi run worker   # Start Celery worker
   ```

5. **Run Tests**:
   ```bash
   pixi run test           # All tests
   pixi run unit           # Unit tests only
   pixi run integration    # Integration tests
   pixi run e2e            # E2E tests (requires credentials)
   ```

6. **Code Quality**:
   ```bash
   pixi run lint           # Ruff linting
   pixi run format         # Ruff formatting
   pixi run type-check     # Mypy type checking
   ```

### Branching Strategy

- **`main`**: Production-ready code, protected
- **`heet-dev`**: Development branch, current work-in-progress
- **`archiveflow-legacy`**: Frozen ArchiveFlow code (rollback reference)
- **Feature branches**: Short-lived, merge to `heet-dev` via PR

### Commit Conventions

Conventional commits format (enforced by pre-commit hooks):
- `feat:` New features
- `fix:` Bug fixes
- `refactor:` Code refactoring
- `docs:` Documentation updates
- `test:` Test additions/modifications
- `chore:` Maintenance tasks

---

## Configuration

### Environment Variables

Create `.env` file at project root (never commit this file!):

```bash
# ELN Configuration
ELN_BACKEND=labarchives          # or elabftw
LABARCHIVES_API_URL=https://api.labarchives.com
LABARCHIVES_ACCESS_KEY_ID=your_key_id
LABARCHIVES_ACCESS_PASSWORD=your_password
LABARCHIVES_SSL_CERT=/path/to/cacert.pem  # Optional: NIH ROOT cert

ELABFTW_API_URL=https://your-elabftw-instance.com
ELABFTW_API_KEY=your_api_key

# Storage Configuration
STORAGE_BACKEND=local            # local, onedrive, box
STORAGE_ROOT_PATH=/path/to/data/directory

# DANDI Configuration
DANDI_API_KEY=your_dandi_api_key
DANDI_DANDISET_ID=000123         # Target dandiset

# Redis Configuration (Celery)
REDIS_URL=redis://localhost:6379/0

# Application Configuration
APP_HOST=http://localhost:8501
FASTAPI_HOST=0.0.0.0
FASTAPI_PORT=8000
LOG_LEVEL=INFO
```

### Lab-Specific Configuration

Create `lab_config.yaml` for directory schemas and metadata mappings:

```yaml
lab_name: "Example Lab"
directory_schema:
  - Surgery
  - Behavior
  - Photometry
  - Histology
  - Metadata
cohort_pattern: "Cohort \\d+"
required_metadata:
  - subject_id
  - experiment_date
  - protocol_name
nwb_scope: configurable  # raw, processed, both, configurable
approval_gates:
  - before_nwb_generation
  - before_dandi_upload
```

---

## Monitoring & Observability

### Metrics to Track

- **Sync Latency**: Time from ELN entry creation to directory creation (target: <5 min)
- **Processing Time**: Time from data detection to NWB generation (target: <10 min for standard session)
- **Upload Success Rate**: % of DANDI uploads that succeed (target: >95%)
- **Error Rate**: % of pipeline runs that encounter errors (target: <5%)
- **Approval Wait Time**: Time from automation trigger to researcher approval (informational)

### Logging Format

Structured JSON logs with required fields:
```json
{
  "timestamp": "2025-10-29T14:23:45.123Z",
  "level": "INFO",
  "request_id": "uuid-1234",
  "subject_id": "M001",
  "session_id": "session-5678",
  "job_id": "job-9012",
  "event": "nwb_generation_started",
  "message": "Starting NWB file generation for subject M001 session 2025-10-29",
  "metadata": {
    "nwb_scope": "both",
    "code_version": "abc123def"
  }
}
```

---

## Security & Compliance

### Data Handling

- **NIH Data Boundary**: All research data stays in NIH-approved storage (local NAS, OneDrive Gov, Box Gov)
- **PII/PHI**: Researcher names, exact dates, and animal IDs included as-is (required for NWB compliance)
- **Secrets**: Environment variables + `.gitignore` for MVP, modular for future cloud migration
- **Audit Trail**: All operations logged with git commit SHA for provenance

### Network Security

- **ELN APIs**: HTTPS only, NIH ROOT certificate required for LabArchives
- **DANDI API**: Public internet access required, check NIH firewall rules
- **Webhooks**: If enabled, validate signatures and use HTTPS endpoints

---

## Next Steps

### Immediate (This Week)

1. ✅ **Specifications finalized** - Complete with stakeholder decisions
2. 📝 **Generate task breakdown** - Run `/tasks` command for detailed implementation tasks
3. 🔄 **Update PR description** - Reflect lab-agnostic approach and eLabFTW criticality
4. 👥 **Stakeholder review** - Share PROJECT_OVERVIEW.md with DSST and collaborating labs

### Phase -1 (Weeks 1-2)

1. Set up development environment with pixi
2. Create `archiveflow-legacy` frozen branch
3. Begin gradual uv→pixi migration (module-by-module)
4. Migrate to Python 3.13 and validate smoke tests
5. Implement eLabFTW adapter (CRITICAL)

### Milestone 1 (Weeks 3-6)

1. Refactor ArchiveFlow into new structure (app/, ui/, workers/)
2. Create shared business logic layer
3. Implement configurable NWB scope
4. Integrate NWB Inspector validation
5. Build manual approval UI

### Milestone 2 (Weeks 7-11)

1. Implement Celery background job queue
2. Add semi-automatic triggers with approval gates
3. Build DANDI upload with retry logic
4. Implement hybrid sync strategy
5. Add researcher pause capability

---

## Resources & Documentation

### Project Documentation
- [Feature Specification](specs/001-eln-to-dandi-pipeline/spec.md)
- [Implementation Plan](specs/001-eln-to-dandi-pipeline/plan.md)
- [Research Findings](specs/001-eln-to-dandi-pipeline/research.md)
- [Data Model](specs/001-eln-to-dandi-pipeline/data-model.md)
- [Developer Quickstart](specs/001-eln-to-dandi-pipeline/quickstart.md)
- [API Contracts](specs/001-eln-to-dandi-pipeline/contracts/)
- [Constitution](. specify/memory/constitution.md)
- [Technical Guardrails](claude.md)

### External Documentation
- [NWB Format](https://www.nwb.org/)
- [ndx-fiber-photometry](https://github.com/catalystneuro/ndx-fiber-photometry)
- [DANDI Archive](https://dandiarchive.org/)
- [LabArchives API](https://www.labarchives.com/api/)
- [eLabFTW API](https://doc.elabftw.net/api/)
- [pixi Documentation](https://pixi.sh/)

### GitHub Repository
- **Repo**: https://github.com/Python-AI-Solutions/elabftw-app
- **Current Branch**: `heet-dev`
- **Pull Request**: #1 (pending review)

---

## Credits

### Original Development
- **Josh Lawrimore, PhD** - ArchiveFlow prototype developer
- **NIMH DSST** - Development team and institutional support

### Current Team
- **Development Lead**: (to be assigned)
- **Contributors**: (to be added)

### External Collaborators
- Collaborating research laboratories conducting fiber photometry experiments
- NWB and DANDI community maintainers

---

## License

(To be determined - likely MIT or BSD for open-source components, with proprietary restrictions for lab-specific code)

---

## Contact & Support

- **Project Issues**: https://github.com/Python-AI-Solutions/elabftw-app/issues
- **DSST**: (contact information to be added)
- **Documentation**: This file and linked specification documents

---

**Document Version**: 1.0
**Last Updated**: 2025-10-29
**Status**: Planning Complete, Ready for Implementation
**Next Review**: After Phase -1 completion
