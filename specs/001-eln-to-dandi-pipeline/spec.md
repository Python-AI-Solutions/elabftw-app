# Feature Specification: ELN to DANDI Pipeline Automation

**Feature Branch**: `heet-dev`
**Created**: 2025-10-27
**Status**: Draft
**Input**: User description: "NIH intramural investigators are required to transition to electronic records for all experiments. Dr. Tejeda's group currently uses LabArchives ELN to record fiber photometry behavioral experiments in mice. elabftw-app aims to semi-automate the pipeline from experimental recording to packaging in NWB format and uploading to the DANDI data repository. The system is developed by DSST with collaboration from MLT and should support both LabArchives and eLabFTW."

## Existing Implementation (ArchiveFlow Prototype)

**Development Credit**: Original prototype developed by Josh Lawrimore (NIMH DSST)
**Repository**: `nimh-dsst/ArchiveFlow` (private)
**Status**: Partially implemented Streamlit-based prototype for Tejeda Lab workflows

### Implemented Components

✅ **LabArchives Integration**
- Full REST/XML API client (`archiveflow/api.py`) with OAuth2 authentication
- Notebook/entry retrieval, directory traversal
- Custom widget parser for BehaviorFormV4/V6 schemas (`archiveflow/behavior_widget.py`)
- Trial table extraction and metadata parsing

✅ **Tejeda Directory Structure**
- Pydantic classes for Surgery/Behavior/Photometry/Histology/Metadata (`archiveflow/structure.py`)
- Cohort management with standardized naming conventions
- Directory creation and organization logic

✅ **TDT Stream Processing**
- Tank directory parser (`archiveflow/tejeda_schemas.py`)
- Stream extraction (TTL events, 405A isosbestic, 470D experimental signals)
- Signal processing pipelines (`archiveflow/photometry.py`, `archiveflow/signal_processing.py`)

✅ **Streamlit Multi-Page UI**
- Login with OAuth2 callback server (`Login.py`)
- 8 operational pages: experiment selection, status monitoring, manual extraction, data processing, behavior analysis, subject status, export
- Real-time status tracking and manual intervention interfaces

✅ **Dependencies Already in Place**
- `neuroconv`, `ndx-fiber-photometry`, `watchdog` already included
- Signal processing libraries configured

### Missing or Incomplete Components

❌ **eLabFTW Integration**: Only LabArchives implemented

❌ **NWB File Generation**: Libraries present but packaging code absent

❌ **DANDI Upload**: Mentioned in README but not implemented

❌ **Background Job Queue**: No Celery/Redis; all processing is synchronous/manual

❌ **FastAPI Backend**: Pure Streamlit architecture, no API layer

🟡 **Automated Workflows**: File watching exists but no automatic trigger to completion

### Migration Considerations

**CRITICAL CONFLICTS with Constitution**:
1. **Package Manager**: ArchiveFlow uses `uv`, constitution requires `pixi` (NON-NEGOTIABLE)
2. **Python Version**: ArchiveFlow requires Python >=3.11, constitution requires 3.13 (NON-NEGOTIABLE)
3. **Architecture**: Streamlit-only vs. required FastAPI + Streamlit microservices

**Integration Strategy**:
- Phase -1 (Migration) must handle `uv` → `pixi` conversion
- Refactor existing `archiveflow/` module into new structure (`app/`, `adapters/`, `nwb/`)
- Extract LabArchives API wrapper for separate PyPI package (reusability)
- Preserve existing Tejeda Lab-specific schemas and widget parsers
- Upgrade Python 3.11 → 3.13 (test for breaking changes)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - ELN Entry Sync to Structured Directory (Priority: P1)

A researcher completes an experiment entry in their ELN (LabArchives or eLabFTW). The system automatically detects the new entry, parses metadata (subject ID, experiment type, date, protocols), and creates a standardized directory structure on shared storage with appropriate subfolders for raw data, metadata spreadsheets, and analysis outputs.

**Why this priority**: This is the foundation of the entire pipeline. Without reliable metadata extraction and directory creation, no downstream automation is possible. It directly addresses the NIH electronic records mandate by establishing structured, traceable experimental records.

**Implementation Status**: 🟡 **Partially Implemented** (LabArchives only, needs eLabFTW and automation)

**Independent Test**: Can be fully tested by creating a test ELN entry with known metadata and verifying that the correct directory structure is created with accurate metadata files, without needing to upload any raw data or generate NWB files.

**Acceptance Scenarios**:

1. **Given** a researcher has completed a Surgery entry in LabArchives with subject ID "M001", **When** the system polls the LabArchives API, **Then** a directory `experiments/M001/surgery/YYYY-MM-DD/` is created with a metadata spreadsheet containing all parsed fields.

2. **Given** a researcher has completed a Behavior experiment entry in eLabFTW with subject "M002" and protocol "fear-conditioning", **When** the system detects the new entry, **Then** a directory `experiments/M002/behavior/fear-conditioning/YYYY-MM-DD/` is created with protocol files and metadata.

3. **Given** an ELN entry contains nested metadata (multiple timepoints, drug doses), **When** the system parses the entry, **Then** all nested fields are correctly extracted into structured metadata spreadsheet with proper hierarchy.

4. **Given** the directory structure already exists for a subject, **When** a new experiment entry is created for the same subject, **Then** the system adds a new timestamped subdirectory without overwriting existing data.

---

### User Story 2 - Raw Data Ingestion and Watcher Trigger (Priority: P2)

A researcher or lab technician drops raw experimental data files (TDT tank folders, protocol CSVs, video files) into the appropriate directory created by User Story 1. A file system watcher detects when all required files are present (based on experiment type) and triggers preprocessing pipelines.

**Why this priority**: This bridges manual data collection with automated processing. It enables hands-off pipeline execution once data is in place and ensures preprocessing only starts when complete datasets are available, preventing incomplete NWB file generation.

**Implementation Status**: 🟡 **Partially Implemented** (Watchdog library present, manual trigger exists, needs automation)

**Independent Test**: Can be tested by manually creating a directory structure (simulating User Story 1 output) and dropping test data files to verify watcher detects completion and triggers preprocessing without requiring ELN integration or DANDI upload.

**Acceptance Scenarios**:

1. **Given** a directory for a fiber photometry behavior session exists, **When** a researcher drops TDT tank folder and protocol CSV into the raw data subfolder, **Then** the watcher detects all required files are present and triggers preprocessing within 30 seconds.

2. **Given** only partial data has been uploaded (e.g., TDT tank but no protocol file), **When** the watcher scans the directory, **Then** preprocessing is NOT triggered and the status remains "awaiting data".

3. **Given** preprocessing has been triggered for a dataset, **When** the researcher adds additional files later, **Then** the watcher does not re-trigger preprocessing unless a specific "reprocess" flag file is added.

4. **Given** multiple experiment directories are populated simultaneously, **When** the watcher detects ready states, **Then** preprocessing tasks are queued appropriately without race conditions or data corruption.

---

### User Story 3 - NWB File Generation and Validation (Priority: P3)

The system packages experimental metadata and preprocessed data into an NWB-compliant file using the ndx-fiber-photometry extension. The NWB file passes pynwb validation and includes all required metadata fields, subject information, timestamps, and fiber photometry timeseries data.

**Why this priority**: NWB compliance is mandatory for DANDI upload and long-term data sharing. This story delivers the core scientific value—standardized, interoperable neuroscience data that can be reused by the community.

**Implementation Status**: ❌ **Not Implemented** (neuroconv + ndx-fiber-photometry present, packaging logic missing)

**Independent Test**: Can be tested by providing preprocessed data and metadata files (simulating User Story 2 output) and verifying that generated NWB files pass pynwb validation and contain all expected data structures, without requiring ELN integration or actual DANDI upload.

**Acceptance Scenarios**:

1. **Given** preprocessed fiber photometry data and metadata are available, **When** the NWB packaging function is called, **Then** an NWB file is created that passes `pynwb.validate()` without errors.

2. **Given** an NWB file has been generated, **When** it is inspected using pynwb, **Then** it contains subject metadata, session start time, fiber photometry timeseries with correct timestamps, and experiment protocol information.

3. **Given** multiple trials or timepoints exist in a single experiment, **When** the NWB file is generated, **Then** all trials are included as separate timeseries objects with correct temporal alignment.

4. **Given** the NWB schema or ndx-fiber-photometry extension is updated, **When** the system regenerates existing NWB files, **Then** files comply with the new schema version and maintain backward compatibility metadata.

---

### User Story 4 - DANDI Archive Upload (Priority: P4)

The system automatically uploads validated NWB files to a designated DANDI archive dataset (dandiset). Upload includes metadata validation, checksum verification, and retry logic for network failures. Upload status and DANDI asset IDs are logged back to the original ELN entry.

**Why this priority**: This completes the data lifecycle from experiment to public archive, satisfying NIH data sharing requirements. It ensures reproducibility and enables external collaborators to access standardized datasets.

**Implementation Status**: ❌ **Not Implemented** (mentioned in README, no code present)

**Independent Test**: Can be tested by providing a valid NWB file (simulating User Story 3 output) and verifying successful upload to a test DANDI dandiset, status tracking, and ELN logging, without requiring live experiment execution.

**Acceptance Scenarios**:

1. **Given** a validated NWB file exists, **When** the DANDI upload process is initiated, **Then** the file is uploaded to the correct dandiset with all metadata fields populated and a DANDI asset ID is returned.

2. **Given** a network error occurs during upload, **When** the upload fails, **Then** the system retries up to 3 times with exponential backoff and logs the failure state if all retries are exhausted.

3. **Given** an NWB file has been successfully uploaded to DANDI, **When** the upload completes, **Then** the system writes the DANDI asset URL and upload timestamp back to the original ELN entry as a comment or status field.

4. **Given** multiple NWB files are queued for upload, **When** uploads are processed, **Then** they are handled sequentially or with rate limiting to avoid DANDI API throttling.

---

### User Story 5 - Multi-ELN Backend Support (Priority: P5)

The system supports both LabArchives (NIH instance via wrapper) and eLabFTW through modular API adapter interfaces. Users can configure which ELN backend to use via environment configuration. All pipeline features (metadata sync, status updates, logging) work identically regardless of backend.

**Why this priority**: Different NIH labs and external collaborators use different ELN systems. Modular support enables broader adoption and future extensibility without re-architecting the pipeline.

**Implementation Status**: 🟡 **Partially Implemented** (LabArchives complete, eLabFTW not started, adapter interface exists informally)

**Independent Test**: Can be tested by configuring the system to use eLabFTW instead of LabArchives and running the full pipeline (User Stories 1-4) to verify identical functionality with different authentication and API calls.

**Acceptance Scenarios**:

1. **Given** the system is configured to use LabArchives, **When** the ELN adapter authenticates, **Then** it uses the NIH-approved LabArchives wrapper library and retrieves entries via LabArchives API endpoints.

2. **Given** the system is configured to use eLabFTW, **When** the ELN adapter authenticates, **Then** it uses the elabapi-python SDK and retrieves entries via eLabFTW RESTful API.

3. **Given** an ELN adapter is called to update entry status, **When** the update request is made, **Then** the adapter translates the generic status update into the backend-specific API call (LabArchives comment vs. eLabFTW status field).

4. **Given** a new ELN backend needs to be added in the future, **When** a developer implements the adapter interface, **Then** no changes to core pipeline logic (directory creation, NWB generation, DANDI upload) are required.

---

### Edge Cases

- What happens when an ELN entry is edited or deleted after directory creation? (System should detect updates and log warnings but not auto-delete data)
- How does the system handle duplicate ELN entries with identical subject IDs and dates? (Generate unique suffixes or warn users)
- What if required metadata fields are missing from an ELN entry? (Log validation errors and mark directory as incomplete)
- What if TDT tank structure is malformed or corrupted? (Preprocessing fails gracefully with clear error messages logged to ELN)
- What if DANDI upload succeeds but ELN logging fails? (Queue retry for ELN update and maintain upload status in local database)
- What if NWB file exceeds DANDI size limits? (Split into multiple files or warn user before upload attempt)
- What if multiple researchers work on the same subject concurrently? (Use file locking or timestamp-based conflict resolution)
- What if the ELN API is temporarily unavailable? (Retry with exponential backoff and alert operators after threshold)

## Requirements *(mandatory)*

### Functional Requirements

| ID | Requirement | Status |
|---|---|---|
| **FR-001** | System MUST authenticate with LabArchives NIH instance using secure token-based authentication via approved wrapper library. | ✅ **Implemented** |
| **FR-002** | System MUST authenticate with eLabFTW using API key authentication via elabapi-python SDK. | ❌ **Not Implemented** |
| **FR-003** | System MUST poll ELN APIs at configurable intervals (default: every 5 minutes) to detect new or updated experimental entries. | 🟡 **Partial** (manual polling only) |
| **FR-004** | System MUST parse ELN entries to extract metadata fields including: subject ID, experiment type (Surgery, Behavior, Imaging), experiment date, protocol name, investigator name, and custom fields. | ✅ **Implemented** (LabArchives + custom widgets) |
| **FR-005** | System MUST create standardized directory structures based on experiment type with predefined subfolder hierarchy (raw/, processed/, metadata/, analysis/). | ✅ **Implemented** (Tejeda schema) |
| **FR-006** | System MUST generate metadata spreadsheets in CSV format containing all extracted ELN fields with timestamps and version information. | 🟡 **Partial** (metadata extraction exists, CSV generation needs work) |
| **FR-007** | System MUST watch designated directories for new files and trigger preprocessing when all required files for an experiment type are present. | 🟡 **Partial** (watchdog library present, automatic trigger missing) |
| **FR-008** | System MUST convert TDT tank folders and protocol CSVs into preprocessed timeseries data suitable for NWB packaging. | ✅ **Implemented** (TDT parsing + signal processing) |
| **FR-009** | System MUST generate NWB files using pynwb library with ndx-fiber-photometry extension for fiber photometry experiments. | ❌ **Not Implemented** |
| **FR-010** | System MUST validate all generated NWB files using pynwb.validate() before proceeding to upload. | ❌ **Not Implemented** |
| **FR-011** | System MUST upload validated NWB files to DANDI archive using dandi-cli or API with checksum verification. | ❌ **Not Implemented** |
| **FR-012** | System MUST log upload status, DANDI asset IDs, and timestamps back to the original ELN entry. | ❌ **Not Implemented** |
| **FR-013** | System MUST record code version hashes (git commit SHA) in both NWB file metadata and ELN log entries for provenance tracking. | ❌ **Not Implemented** |
| **FR-014** | System MUST handle preprocessing and upload failures gracefully with structured error logging and retry mechanisms. | 🟡 **Partial** (error handling exists, retry logic missing) |
| **FR-015** | System MUST support configuration of storage backends (local filesystem, OneDrive, Box) via environment variables or config files. | 🟡 **Partial** (local filesystem only) |
| **FR-016** | System MUST emit structured JSON logs for all pipeline operations including ELN sync, preprocessing, NWB generation, and DANDI upload. | 🟡 **Partial** (logging exists, not structured JSON) |
| **FR-017** | System MUST track sync latency (time from ELN entry creation to NWB generation) and expose metrics for monitoring. | 🟡 **Partial** (status tracking exists, metrics not exposed) |
| **FR-018** | System MUST produce idempotent NWB files (re-running with identical inputs produces byte-identical outputs excluding timestamps). | ❌ **Not Implemented** |
| **FR-019** | System MUST provide a Streamlit dashboard for operators to monitor pipeline status, view logs, and trigger manual interventions. | ✅ **Implemented** (8 pages with full UI) |
| **FR-020** | System MUST provide API endpoints (FastAPI) for programmatic access to pipeline status and manual job submission. | ❌ **Not Implemented** (no FastAPI backend) |

### Key Entities

- **Subject**: Represents an experimental animal. Attributes: subject ID, species, strain, sex, date of birth, surgery history. Relationships: has many experiments.
- **Surgery**: Represents a surgical procedure. Attributes: surgery date, procedure type, implant details, surgeon name, recovery notes. Relationships: belongs to a subject.
- **Behavior Session**: Represents a behavioral experiment session. Attributes: session date, protocol name, duration, trial count, environmental conditions. Relationships: belongs to a subject, may reference surgery.
- **Data Acquisition**: Represents raw data files for a session. Attributes: acquisition date, file paths, file types (TDT tank, CSV, video), acquisition system metadata. Relationships: belongs to a behavior session.
- **NWB Dataset**: Represents a packaged NWB file. Attributes: NWB file path, creation timestamp, validation status, code version hash, DANDI asset ID. Relationships: belongs to a behavior session, references subject and surgery.
- **ELN Entry**: Represents metadata from ELN. Attributes: entry ID, entry type, creation date, last modified date, researcher, parsed metadata fields. Relationships: links to subject, surgery, or behavior session.
- **Analysis Run**: Represents a preprocessing or analysis job. Attributes: run ID, start time, end time, status (pending, running, completed, failed), error logs, input files, output files. Relationships: belongs to a data acquisition.
- **Pipeline Status**: Represents the overall state of a dataset in the pipeline. Attributes: current stage (synced, awaiting data, preprocessing, packaging, uploading, complete), last updated timestamp, error messages. Relationships: belongs to a behavior session.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Metadata handling time is reduced from 10+ minutes of manual spreadsheet entry to under 10 seconds automated extraction per experiment.
- **SC-002**: Manual data packaging time is reduced by 95% (from hours to minutes) through automated NWB generation.
- **SC-003**: 100% of fiber photometry experiments generate NWB files that pass pynwb validation.
- **SC-004**: 100% of NWB files uploaded to DANDI include complete metadata and pass DANDI validation.
- **SC-005**: Sync latency from ELN entry creation to NWB file generation averages under 5 minutes for standard fiber photometry sessions.
- **SC-006**: DANDI upload success rate exceeds 95% (allowing for transient network failures with retry).
- **SC-007**: All automated operations include provenance tracking (code versions logged in both NWB files and ELN entries).
- **SC-008**: System supports concurrent processing of at least 10 experiment sessions without data corruption or race conditions.
- **SC-009**: Researchers can view pipeline status for their experiments via dashboard within 10 seconds of accessing the interface.
- **SC-010**: System maintains stable operation with both LabArchives and eLabFTW backends without requiring separate codebases.

## Assumptions *(optional)*

**Inherited from ArchiveFlow Prototype**:
- LabArchives NIH instance API access is available with appropriate credentials and quota limits. ✅ **VALIDATED** (OAuth2 flow working)
- TDT tank folder structure follows standard TDT data organization conventions. ✅ **VALIDATED** (parser implemented for Tejeda Lab conventions)
- Tejeda Lab uses specific LabArchives custom widgets (BehaviorFormV4/V6) for structured metadata. ✅ **IMPLEMENTED** (widget parsers exist)
- Shared storage is local filesystem mounted with read/write permissions. ✅ **WORKING** (OneDrive/Box deferred)
- Fiber photometry experiments use TDT systems with 405A (isosbestic) and 470D (experimental) streams. ✅ **IMPLEMENTED** (stream extraction working)

**New Assumptions for Full Pipeline**:
- eLabFTW instances are accessible via standard RESTful API with API key authentication.
- DANDI archive dandiset exists and upload credentials are configured before system deployment.
- NWB schema and ndx-fiber-photometry extension versions are pinned in environment configuration.
- Network connectivity to ELN APIs and DANDI archive is generally reliable with occasional transient failures.
- System operates in a trusted environment where file system access and API credentials are secured.
- ArchiveFlow codebase can be migrated from `uv` to `pixi` and Python 3.11 to 3.13 without major breaking changes.
- Existing Tejeda Lab directory structure (Surgery/Behavior/Photometry/Histology/Metadata with cohorts) will be preserved or minimally adapted.

## Constraints & Policies *(optional)*

- **Regulatory Compliance**: System MUST comply with NIH June 2024 electronic records mandate for intramural research.
- **Security**: API tokens and credentials MUST be stored in secrets manager (never in code or version control).
- **Data Governance**: Research data MUST remain within NIH-approved storage locations. No personally identifiable information (PII) may be exfiltrated.
- **NWB Standard**: All neural data MUST use NWB format with ndx-fiber-photometry extension. Non-compliant formats are not acceptable.
- **Reproducibility**: All data transformations MUST be auditable via structured logs and provenance records.
- **Versioning**: Code version hashes MUST be recorded for all automated operations to enable reproducibility audits.

## Dependencies *(optional)*

- LabArchives NIH instance API availability and approved wrapper library.
- eLabFTW API and elabapi-python SDK.
- pynwb library and ndx-fiber-photometry extension.
- DANDI CLI or API access with upload credentials.
- Shared storage infrastructure (local, OneDrive, or Box).
- Preprocessing libraries for TDT tank data and fiber photometry signal processing.
- Celery and Redis for background task management.
- FastAPI and Streamlit for operator interface.

## Risks & Unknowns *(optional)*

**Reduced Risks (due to ArchiveFlow)**:
- ~~**LabArchives API Access**~~: ✅ VALIDATED - OAuth2 flow working, rate limits tested informally
- ~~**TDT Processing**~~: ✅ IMPLEMENTED - Parser and signal processing validated for Tejeda Lab
- ~~**Custom Widget Parsing**~~: ✅ IMPLEMENTED - BehaviorFormV4/V6 parsers working

**Remaining Risks**:
- **Migration Complexity**: `uv` → `pixi` and Python 3.11 → 3.13 may uncover dependency conflicts or breaking changes
- **Architecture Refactoring**: Extracting business logic from Streamlit UI to FastAPI may introduce regressions
- **Multi-Storage Complexity**: Supporting multiple storage backends (OneDrive, Box) may introduce authentication and permission challenges
- **NWB Schema Evolution**: NWB schema or ndx-fiber-photometry extension updates may require file regeneration or migration scripts
- **External Collaboration**: Modularization may depend on external developer capacity and timeline alignment with DSST
- **Data Volume**: Scaling to hundreds of experiments with large video files may require storage optimization strategies
- **ELN Customization**: Custom ELN templates or fields used by different labs may require adapter customization beyond Tejeda Lab widgets

**New Risks (Migration-Specific)**:
- **ArchiveFlow Code Preservation**: Risk of breaking existing functionality during refactoring
- **Dual Maintenance**: Need to maintain compatibility with Tejeda Lab workflows during transition
- **Test Coverage Gaps**: Existing tests may not cover all edge cases, migration may expose untested paths

---

## Summary: ArchiveFlow Integration Impact

**What We Have** (thanks to Josh Lawrimore's ArchiveFlow prototype):
- ✅ Complete LabArchives OAuth2 integration with custom widget parsing (BehaviorFormV4/V6)
- ✅ Production-tested TDT tank processing with stream extraction (405A, 470D, TTL)
- ✅ Tejeda Lab-specific directory structure with Surgery/Behavior/Photometry/Histology/Metadata organization
- ✅ 8-page Streamlit operator UI with manual intervention capabilities
- ✅ Signal processing pipelines for fiber photometry data
- ✅ File watching infrastructure (watchdog library)
- ✅ Basic status tracking and experiment selection workflows

**What We Need to Build**:
- ❌ NWB file generation (packaging preprocessed data into NWB format)
- ❌ DANDI archive upload (validation, chunked uploads, retry logic)
- ❌ eLabFTW ELN adapter (multi-backend support)
- ❌ FastAPI backend (API endpoints for programmatic access)
- ❌ Celery + Redis task queue (background job automation)
- ❌ Automatic end-to-end pipeline (currently requires manual steps)
- ❌ Structured JSON logging and observability metrics
- ❌ Provenance tracking (Git SHA → NWB + ELN)

**Critical Migration Steps**:
1. **Phase -1**: Migrate `uv` → `pixi`, Python 3.11 → 3.13, refactor architecture
2. **Preserve**: All existing Tejeda Lab workflows, custom parsers, directory structure
3. **Extract**: LabArchives API wrapper as reusable component
4. **Extend**: Add FastAPI backend, NWB packaging, DANDI upload, eLabFTW support

**Timeline Impact**: Estimated 30-40% reduction in implementation time due to existing:
- LabArchives integration (would take 3-4 weeks to build from scratch)
- TDT processing (would take 2-3 weeks to build from scratch)
- Streamlit UI (would take 2-3 weeks to build from scratch)

**Stakeholder Acknowledgment**: This specification builds upon ArchiveFlow prototype developed by Josh Lawrimore (NIMH DSST). Original code repository: `nimh-dsst/ArchiveFlow` (private).

---

**Document Version**: 2.0 (Updated for ArchiveFlow Integration)
**Last Updated**: 2025-10-29
**Original Spec Author**: Claude (via /specify command)
**ArchiveFlow Developer**: Josh Lawrimore (NIMH DSST)
