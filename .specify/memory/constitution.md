<!--
SYNC IMPACT REPORT
==================
Version Change: Initial (template) → 1.0.0
Modified Principles: All principles newly defined
Added Sections: All sections newly populated
Removed Sections: None
Templates Status:
  ✅ plan-template.md - reviewed, no updates required (generic Constitution Check placeholder)
  ✅ spec-template.md - reviewed, no updates required (no constitution references)
  ✅ tasks-template.md - reviewed, no updates required (no constitution references)
  ⚠️  agent-file-template.md - not reviewed (generic template)
  ⚠️  checklist-template.md - not reviewed (generic template)
  ⚠️  commands/*.md - directory does not exist, no command files to update
Follow-up TODOs: None - all placeholders filled
-->

# elabftw-app Constitution

## Core Principles

### I. Mission-Driven Architecture

**The application MUST automate the protocol-to-publication pipeline for Tejeda-style neuroscience experiments.**

- All features MUST support the core workflow: ELN → structured directory → NWB (ndx-fiber-photometry) → DANDI upload
- Status synchronization back to ELN is mandatory for all pipeline stages
- Design decisions MUST prioritize the needs of neuroscience researchers conducting fiber photometry experiments

**Rationale**: This application exists to solve a specific workflow problem. Every technical decision must be evaluated against whether it advances this mission or introduces unnecessary complexity.

### II. Data Standards Compliance (NON-NEGOTIABLE)

**NWB (Neurodata Without Borders) format is mandatory for all neural data storage.**

- MUST use `pynwb` and `neuroconv` libraries for all NWB file operations
- MUST use `ndx-fiber-photometry` extension for fiber photometry data
- All NWB files MUST pass `pynwb` validation before upload
- DANDI upload automation is required; manual upload workarounds are not acceptable
- All transformations MUST be auditable and preserve data provenance

**Rationale**: NWB is the neuroscience community standard. Compliance ensures interoperability, reproducibility, and long-term data preservation. Non-compliant data cannot be shared via DANDI and fails the mission.

### III. Multi-ELN Support

**The application MUST support multiple Electronic Lab Notebook systems with modular adapters.**

- Supported ELNs: LabArchives (NIH instance via wrapper) and eLabFTW (open demo)
- ELN adapters MUST be pluggable modules with standardized interfaces
- New ELN integrations MUST NOT require changes to core pipeline logic
- Each ELN adapter MUST handle authentication, entry retrieval, and status updates independently

**Rationale**: Research institutions use different ELN systems. Modular design allows expansion without architectural rewrites and maintains separation of concerns.

### IV. Python 3.13 & Pixi-Only Dependency Management (NON-NEGOTIABLE)

**Python 3.13 is the required runtime everywhere: production, CI, notebooks, scripts.**

- MUST use pixi exclusively for environment management and task execution
- NO pip, conda, poetry, or other package managers may be used for dependency resolution
- All dependencies MUST be declared in `pixi.toml` and `pyproject.toml`
- Pixi tasks MUST be the sole interface for common operations (dev, test, lint, format, type-check)

**Rationale**: Python 3.13 provides the latest language features and performance improvements. Pixi ensures reproducible, cross-platform environments without the complexity of managing multiple tools. Single-source dependency management prevents conflicts.

### V. Testing Discipline

**Unit and integration tests may use fakes; end-to-end tests MUST use real systems.**

- E2E tests MUST exercise the complete happy path: ELN → directory → NWB → DANDI
- NO mocks or stubs are permitted in E2E tests for external system interactions (ELN APIs, DANDI API)
- If real system access is unavailable (credentials, network, etc.), E2E tests MUST be marked as *blocked*, not mocked
- Test failures are blocking; passing tests are required for merge

**Rationale**: Integration points with external systems (LabArchives, eLabFTW, DANDI) are the highest-risk areas. Mocked E2E tests give false confidence. Real system testing ensures the pipeline actually works in production.

### VI. Idempotency & Determinism

**All data packaging and transformation operations MUST be idempotent and deterministic.**

- Re-running the same pipeline with identical inputs MUST produce byte-identical NWB files (excluding timestamps)
- Directory watcher triggers MUST handle duplicate events gracefully
- Failed operations MUST be safely retryable without data corruption
- Code version hashes MUST be recorded in ELN logs for provenance

**Rationale**: Research data integrity is paramount. Idempotent operations prevent double-processing bugs. Determinism enables reproducibility audits and debugging.

### VII. Observability

**Structured logging, metrics, and monitoring are mandatory for production operations.**

- All ELN-to-NWB sync operations MUST emit structured logs (JSON format)
- Sync latency MUST be tracked (target: <5 minutes from ELN update to NWB generation)
- DANDI upload success rate MUST be monitored and alerted
- Analysis provenance (code version, input data versions) MUST be recorded back to ELN

**Rationale**: Silent failures in automated pipelines lead to data loss. Observability enables rapid incident response and performance tuning. Provenance enables reproducibility and compliance audits.

## Architecture Constraints

### Modular ELN Adapters

- LabArchives adapter MUST use the NIH-approved wrapper library
- eLabFTW adapter MUST use `elabapi-python` SDK
- Adapter interface MUST define: `authenticate()`, `get_entries()`, `update_entry_status()`, `get_attachments()`
- Adapters MUST handle rate limiting and retries internally

### Pluggable Storage Adapters

- Supported storage backends: local filesystem, OneDrive, Box
- Directory schema MUST be dictated by ELN entry types (Surgery, Behavior, Imaging, etc.)
- Storage adapter interface MUST define: `read()`, `write()`, `list()`, `watch()` operations
- All storage operations MUST support async I/O

### Service Architecture

- FastAPI backend for API endpoints and pipeline orchestration
- Streamlit operator UI for monitoring and manual interventions
- Background workers using asyncio/Celery for long-running tasks
- File system watcher triggers preprocessing/analysis on new data

## Security & Compliance

### Secrets Management

- API tokens and credentials MUST be stored in a secrets manager (never in code or environment files)
- `.env` files, `credentials.json`, and similar files MUST be gitignored
- Git commit hooks MUST block commits containing potential secrets

### Data Governance

- Research data MUST remain within NIH-approved storage locations
- No personally identifiable information (PII) may be exfiltrated to non-approved systems
- All data transformations MUST be auditable via logs and provenance records
- DANDI uploads MUST only include approved, de-identified datasets

## Tooling & Runtime

### Version Control

- Git with trunk-based development (short-lived feature branches)
- Semantic commit messages required (conventional commits format)
- Code version hash MUST be included in ELN log entries for all automated operations

### Service Stack

- **Backend**: FastAPI (async endpoints)
- **UI**: Streamlit (operator dashboard)
- **Workers**: Celery with Redis broker for background tasks
- **Task Runner**: Pixi tasks for all common operations

## Review Gates

**Pull requests CANNOT be merged unless all gates pass:**

1. **NWB Validation Gate**: Generated NWB files MUST pass `pynwb.validate()`
2. **DANDI Dry-Run Gate**: DANDI upload dry-run MUST succeed without errors
3. **Spec/Plan Alignment Gate**: Implementation MUST match approved feature specification
4. **Constitution Compliance Gate**: Code changes MUST satisfy all NON-NEGOTIABLE principles
5. **Python 3.13 Gate**: All code MUST run on Python 3.13 (no fallbacks to older versions)
6. **Pixi-Only Gate**: No pip, conda, or poetry commands in scripts or CI (pixi only)
7. **E2E Test Gate**: No mocked external systems in E2E tests (may mark as blocked if unavailable)

## Governance

### Amendment Procedure

- Constitution changes require a version bump and rationale documentation
- Breaking changes (removing/redefining principles) require MAJOR version bump
- Adding new principles or sections requires MINOR version bump
- Clarifications and wording improvements require PATCH version bump
- All amendments MUST update dependent templates (plan, spec, tasks) for consistency

### Version Policy

- Version format: MAJOR.MINOR.PATCH (semantic versioning)
- Version MUST be incremented with each amendment
- Ratification date is the original adoption date (immutable)
- Last Amended date MUST be updated to current date on any change

### Compliance Review

- All pull requests MUST include a constitution compliance checklist
- Design documents MUST reference relevant principles and justify any tensions
- Code reviews MUST verify adherence to NON-NEGOTIABLE principles
- Violations require explicit justification and architecture review approval

**Version**: 1.0.0 | **Ratified**: 2025-10-27 | **Last Amended**: 2025-10-27
