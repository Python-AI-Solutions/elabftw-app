# Data Model: ELN to DANDI Pipeline

**Version**: 1.0
**Date**: 2025-10-27
**Branch**: `heet-dev`
**Related**: `spec.md`, `plan.md`

## Overview

This document defines the 8 core entities that comprise the elabftw-app data model. Each entity supports the automated pipeline from Electronic Lab Notebook (ELN) recording through NWB packaging to DANDI archive upload. The model prioritizes:

- **Traceability**: Every data artifact links back to its source ELN entry
- **Provenance**: Code versions, timestamps, and processing history are first-class attributes
- **Idempotency**: Entities support deterministic recreation and retry-safe operations
- **Multi-backend**: ELN and storage adapters are polymorphic via abstract attributes

---

## Entity Catalog

### 1. Subject

Represents an experimental animal (mouse, rat, etc.) that participates in one or more experimental sessions.

**Attributes**:

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `subject_id` | `str` | Primary Key, Unique | Lab-specific subject identifier (e.g., "M001", "RAT-2024-03") |
| `species` | `str` | Required | Common name (e.g., "mouse", "rat") mapped to NCBI Taxon ID |
| `strain` | `str` | Optional | Genetic strain (e.g., "C57BL/6J", "Long-Evans") |
| `sex` | `enum` | Required, `{"M", "F", "U"}` | Biological sex (M=Male, F=Female, U=Unknown) |
| `date_of_birth` | `date` | Optional | Birth date for age calculation |
| `weight` | `float` | Optional | Weight in grams at most recent measurement |
| `surgery_history` | `list[str]` | Default `[]` | List of surgery IDs (foreign keys) |
| `notes` | `str` | Optional | Free-text notes from ELN |
| `created_at` | `datetime` | Auto | Timestamp of first ELN entry sync |
| `updated_at` | `datetime` | Auto | Timestamp of most recent update |

**Relationships**:
- `has many` **Surgery** (one-to-many)
- `has many` **Behavior Session** (one-to-many)
- `referenced by` **ELN Entry** (many-to-one)

**Lifecycle**:
1. Created when first ELN entry (Surgery or Behavior) references subject ID
2. Updated when new surgeries or sessions are added
3. Remains active until archived (manual operator action)

**Validation Rules**:
- `subject_id` must match regex `^[A-Z0-9\-_]+$` (alphanumeric, dash, underscore)
- `species` must map to valid NCBI Taxon ID (see NWB schema mapping)
- `sex` normalized to NWB vocabulary ("M", "F", "U")
- `date_of_birth` must be before any session dates

**Example (Pydantic Schema)**:
```python
from pydantic import BaseModel, Field
from datetime import date, datetime
from enum import Enum

class Sex(str, Enum):
    MALE = "M"
    FEMALE = "F"
    UNKNOWN = "U"

class Subject(BaseModel):
    subject_id: str = Field(..., pattern=r"^[A-Z0-9\-_]+$")
    species: str
    strain: str | None = None
    sex: Sex
    date_of_birth: date | None = None
    weight: float | None = Field(None, gt=0)
    surgery_history: list[str] = Field(default_factory=list)
    notes: str = ""
    created_at: datetime
    updated_at: datetime
```

---

### 2. Surgery

Represents a surgical procedure performed on a subject (e.g., fiber optic implantation).

**Attributes**:

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `surgery_id` | `str` | Primary Key, Unique | Generated from `{subject_id}_{surgery_date}` |
| `subject_id` | `str` | Foreign Key, Required | References Subject.subject_id |
| `surgery_date` | `date` | Required | Date procedure performed |
| `procedure_type` | `str` | Required | Type of surgery (e.g., "fiber_implant", "craniotomy") |
| `implant_details` | `str` | Optional | Description of implants/devices |
| `surgeon_name` | `str` | Required | Name of person performing surgery |
| `recovery_notes` | `str` | Optional | Post-surgical recovery observations |
| `eln_entry_id` | `str` | Foreign Key, Required | References ELN Entry.entry_id |
| `created_at` | `datetime` | Auto | Timestamp of ELN sync |

**Relationships**:
- `belongs to` **Subject** (many-to-one)
- `linked to` **ELN Entry** (one-to-one)
- `referenced by` **Behavior Session** (one-to-many)

**Lifecycle**:
1. Created when ELN Surgery entry is synced
2. Immutable after creation (no updates allowed)
3. Referenced by future Behavior Sessions to track implant state

**Validation Rules**:
- `surgery_id` uniqueness enforced via `{subject_id}_{surgery_date}` composite
- `surgery_date` must be on or before any behavior session dates for subject
- `eln_entry_id` must exist in ELN Entry table
- `subject_id` must exist in Subject table

**Example (Pydantic Schema)**:
```python
class Surgery(BaseModel):
    surgery_id: str
    subject_id: str
    surgery_date: date
    procedure_type: str
    implant_details: str = ""
    surgeon_name: str
    recovery_notes: str = ""
    eln_entry_id: str
    created_at: datetime
```

---

### 3. Behavior Session

Represents a single behavioral experiment session (e.g., fear conditioning, operant task).

**Attributes**:

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `session_id` | `str` | Primary Key, Unique | Generated from `{subject_id}_{session_date}_{protocol_name}` |
| `subject_id` | `str` | Foreign Key, Required | References Subject.subject_id |
| `session_date` | `date` | Required | Date of experimental session |
| `protocol_name` | `str` | Required | Behavioral protocol (e.g., "fear_conditioning", "operant_lever_press") |
| `duration_minutes` | `int` | Optional | Total session duration in minutes |
| `trial_count` | `int` | Optional | Number of trials/repetitions |
| `environmental_conditions` | `dict` | Optional | Temp, humidity, lighting (JSON) |
| `eln_entry_id` | `str` | Foreign Key, Required | References ELN Entry.entry_id |
| `created_at` | `datetime` | Auto | Timestamp of ELN sync |
| `updated_at` | `datetime` | Auto | Timestamp of most recent update |

**Relationships**:
- `belongs to` **Subject** (many-to-one)
- `may reference` **Surgery** (many-to-one, optional)
- `has one` **Data Acquisition** (one-to-one)
- `has one` **Pipeline Status** (one-to-one)
- `has one` **NWB Dataset** (one-to-one, created after packaging)
- `linked to` **ELN Entry** (one-to-one)

**Lifecycle**:
1. Created when ELN Behavior entry is synced
2. Directory structure created (via Storage Adapter)
3. Data Acquisition record initialized (status: awaiting)
4. Pipeline Status initialized (stage: synced)
5. Progresses through pipeline stages until complete

**Validation Rules**:
- `session_id` uniqueness enforced via composite key
- `session_date` must be on or after subject's most recent surgery date
- `duration_minutes` must be positive integer if provided
- `trial_count` must be positive integer if provided

**Example (Pydantic Schema)**:
```python
class BehaviorSession(BaseModel):
    session_id: str
    subject_id: str
    session_date: date
    protocol_name: str
    duration_minutes: int | None = Field(None, gt=0)
    trial_count: int | None = Field(None, gt=0)
    environmental_conditions: dict = Field(default_factory=dict)
    eln_entry_id: str
    created_at: datetime
    updated_at: datetime
```

---

### 4. Data Acquisition

Represents the collection of raw data files for a behavior session (TDT tank, protocol CSVs, video files).

**Attributes**:

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `acquisition_id` | `str` | Primary Key, Unique | Generated from `{session_id}_acq` |
| `session_id` | `str` | Foreign Key, Required | References Behavior Session.session_id |
| `acquisition_date` | `datetime` | Required | Timestamp when data collection started |
| `file_paths` | `list[str]` | Default `[]` | List of all file paths (relative to storage root) |
| `file_types` | `list[str]` | Default `[]` | List of file types ("TDT", "CSV", "MP4", "AVI") |
| `tdt_tank_path` | `str` | Optional | Path to TDT tank folder (if applicable) |
| `protocol_csv_path` | `str` | Optional | Path to protocol CSV file |
| `video_paths` | `list[str]` | Default `[]` | Paths to video files |
| `acquisition_system_metadata` | `dict` | Default `{}` | System-specific metadata (sampling rate, channels, etc.) |
| `readiness_status` | `enum` | Required | `{"awaiting", "ready", "processing"}` |
| `created_at` | `datetime` | Auto | Timestamp of directory creation |
| `updated_at` | `datetime` | Auto | Timestamp of most recent file addition |

**Relationships**:
- `belongs to` **Behavior Session** (one-to-one)
- `has many` **Analysis Run** (one-to-many)

**Lifecycle**:
1. Created when directory structure is initialized (status: awaiting)
2. Updated as files are uploaded by researcher
3. Watcher detects completeness → status: ready
4. Preprocessing task starts → status: processing
5. Linked to Analysis Run records

**Validation Rules**:
- `acquisition_id` must be unique
- `session_id` must exist in Behavior Session table
- `acquisition_date` must be on or after session_date
- `readiness_status` transitions: `awaiting` → `ready` → `processing` (unidirectional)
- File paths must be within storage adapter root directory

**Readiness Detection Logic**:
- **Fiber Photometry Session**: Requires TDT tank folder + protocol CSV
- **Video Session**: Requires at least one video file (.mp4 or .avi)
- **Combined Session**: Requires all of the above

**Example (Pydantic Schema)**:
```python
from enum import Enum

class ReadinessStatus(str, Enum):
    AWAITING = "awaiting"
    READY = "ready"
    PROCESSING = "processing"

class DataAcquisition(BaseModel):
    acquisition_id: str
    session_id: str
    acquisition_date: datetime
    file_paths: list[str] = Field(default_factory=list)
    file_types: list[str] = Field(default_factory=list)
    tdt_tank_path: str | None = None
    protocol_csv_path: str | None = None
    video_paths: list[str] = Field(default_factory=list)
    acquisition_system_metadata: dict = Field(default_factory=dict)
    readiness_status: ReadinessStatus
    created_at: datetime
    updated_at: datetime
```

---

### 5. NWB Dataset

Represents a packaged NWB file generated from a behavior session's data and metadata.

**Attributes**:

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `nwb_id` | `str` | Primary Key, Unique | Generated from `{session_id}_nwb` |
| `session_id` | `str` | Foreign Key, Required | References Behavior Session.session_id |
| `file_path` | `str` | Required, Unique | Absolute path to NWB file |
| `creation_timestamp` | `datetime` | Auto | Timestamp when NWB file was generated |
| `validation_status` | `bool` | Required | True if `pynwb.validate()` passed |
| `validation_report_path` | `str` | Optional | Path to validation report (JSON) |
| `code_version_hash` | `str` | Required | Git commit SHA of packaging code |
| `pixi_lock_hash` | `str` | Required | Hash of pixi.lock (dependency fingerprint) |
| `dandi_asset_id` | `str` | Optional | DANDI asset ID after upload |
| `dandi_upload_timestamp` | `datetime` | Optional | Timestamp of successful DANDI upload |
| `created_at` | `datetime` | Auto | Timestamp of record creation |
| `updated_at` | `datetime` | Auto | Timestamp of most recent update |

**Relationships**:
- `belongs to` **Behavior Session** (one-to-one)
- `references` **Subject** (indirect via session)
- `references` **Surgery** (indirect via session)

**Lifecycle**:
1. Created when NWB packaging task completes
2. Validation status set after `pynwb.validate()`
3. If validation fails → status remains False, retry scheduled
4. If validation passes → proceeds to DANDI upload
5. DANDI asset ID logged after successful upload
6. Immutable after DANDI upload (no re-packaging unless force_repackage flag)

**Validation Rules**:
- `nwb_id` must be unique
- `session_id` must exist in Behavior Session table
- `file_path` must exist on filesystem
- `validation_status=True` required before DANDI upload
- `code_version_hash` must match git SHA format (`^[0-9a-f]{40}$`)
- `dandi_asset_id` format must match DANDI asset ID pattern (if present)

**Idempotency Guarantee**:
- Re-running packaging with identical inputs produces byte-stable NWB file (excluding timestamps in metadata)
- Idempotency key: `{subject_id}_{session_date}_{protocol_name}_{code_version_hash}`

**Example (Pydantic Schema)**:
```python
class NWBDataset(BaseModel):
    nwb_id: str
    session_id: str
    file_path: str
    creation_timestamp: datetime
    validation_status: bool
    validation_report_path: str | None = None
    code_version_hash: str = Field(..., pattern=r"^[0-9a-f]{40}$")
    pixi_lock_hash: str
    dandi_asset_id: str | None = None
    dandi_upload_timestamp: datetime | None = None
    created_at: datetime
    updated_at: datetime
```

---

### 6. ELN Entry

Represents metadata from an Electronic Lab Notebook entry (LabArchives or eLabFTW).

**Attributes**:

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `entry_id` | `str` | Primary Key, Unique | ELN-specific entry ID (e.g., LabArchives entry ID) |
| `eln_backend` | `enum` | Required | `{"labarchives", "elabftw"}` |
| `entry_type` | `enum` | Required | `{"surgery", "behavior", "imaging"}` |
| `creation_date` | `datetime` | Required | Timestamp of entry creation in ELN |
| `last_modified_date` | `datetime` | Required | Timestamp of most recent ELN modification |
| `researcher_name` | `str` | Required | Name/username of researcher who created entry |
| `parsed_metadata` | `dict` | Default `{}` | Extracted structured metadata (JSON) |
| `raw_content` | `str` | Optional | Raw ELN content (HTML/Markdown) |
| `eln_backend` | `enum` | Required | `{"labarchives", "elabftw"}` |
| `created_at` | `datetime` | Auto | Timestamp of first sync |
| `updated_at` | `datetime` | Auto | Timestamp of most recent sync |

**Relationships**:
- `links to` **Subject** (many-to-one)
- `links to` **Surgery** (one-to-one, if entry_type=surgery)
- `links to` **Behavior Session** (one-to-one, if entry_type=behavior)

**Lifecycle**:
1. Fetched from ELN API during sync
2. Metadata parsed (via adapter-specific parser)
3. Subject/Surgery/Session entities created or updated
4. Status updates logged back to ELN
5. Re-synced if `last_modified_date` changes

**Validation Rules**:
- `entry_id` must be unique per ELN backend
- `entry_type` determines which entity is created
- `parsed_metadata` must contain required fields for entity type
- `last_modified_date` >= `creation_date`

**Parsed Metadata Structure (example for Behavior entry)**:
```json
{
  "subject_id": "M001",
  "session_date": "2025-10-27",
  "protocol_name": "fear_conditioning",
  "duration_minutes": 60,
  "trial_count": 10,
  "environmental_conditions": {
    "temperature_c": 22,
    "humidity_percent": 50
  }
}
```

**Example (Pydantic Schema)**:
```python
from enum import Enum

class ELNBackend(str, Enum):
    LABARCHIVES = "labarchives"
    ELABFTW = "elabftw"

class EntryType(str, Enum):
    SURGERY = "surgery"
    BEHAVIOR = "behavior"
    IMAGING = "imaging"

class ELNEntry(BaseModel):
    entry_id: str
    eln_backend: ELNBackend
    entry_type: EntryType
    creation_date: datetime
    last_modified_date: datetime
    researcher_name: str
    parsed_metadata: dict = Field(default_factory=dict)
    raw_content: str = ""
    created_at: datetime
    updated_at: datetime
```

---

### 7. Analysis Run

Represents a preprocessing, packaging, or upload job execution (via Celery task).

**Attributes**:

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `run_id` | `str` | Primary Key, Unique | Generated from `{session_id}_{run_type}_{timestamp}` |
| `acquisition_id` | `str` | Foreign Key, Required | References Data Acquisition.acquisition_id |
| `run_type` | `enum` | Required | `{"preprocessing", "packaging", "upload"}` |
| `start_time` | `datetime` | Required | Timestamp when task started |
| `end_time` | `datetime` | Optional | Timestamp when task completed |
| `status` | `enum` | Required | `{"pending", "running", "completed", "failed"}` |
| `error_logs` | `list[str]` | Default `[]` | List of error messages (if failed) |
| `input_files` | `list[str]` | Default `[]` | List of input file paths |
| `output_files` | `list[str]` | Default `[]` | List of output file paths |
| `retry_count` | `int` | Default `0` | Number of retry attempts |
| `created_at` | `datetime` | Auto | Timestamp of record creation |
| `updated_at` | `datetime` | Auto | Timestamp of most recent update |

**Relationships**:
- `belongs to` **Data Acquisition** (many-to-one)

**Lifecycle**:
1. Created when Celery task is queued (status: pending)
2. Task starts execution → status: running
3. Task completes → status: completed (output_files populated)
4. Task fails → status: failed (error_logs populated, retry scheduled)
5. Retry attempted → retry_count incremented, new run_id created

**Validation Rules**:
- `run_id` must be unique
- `acquisition_id` must exist in Data Acquisition table
- `start_time` must be after created_at
- `end_time` must be after start_time (if present)
- `status=completed` requires non-empty output_files
- `status=failed` requires non-empty error_logs

**Retry Policy**:
- Max retries: 3 (configurable)
- Backoff: Exponential (2^retry_count * 60 seconds)
- Transient errors (network, API rate limit) → retry
- Validation errors (bad data, missing files) → no retry (manual intervention)

**Example (Pydantic Schema)**:
```python
from enum import Enum

class RunType(str, Enum):
    PREPROCESSING = "preprocessing"
    PACKAGING = "packaging"
    UPLOAD = "upload"

class RunStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class AnalysisRun(BaseModel):
    run_id: str
    acquisition_id: str
    run_type: RunType
    start_time: datetime
    end_time: datetime | None = None
    status: RunStatus
    error_logs: list[str] = Field(default_factory=list)
    input_files: list[str] = Field(default_factory=list)
    output_files: list[str] = Field(default_factory=list)
    retry_count: int = Field(0, ge=0)
    created_at: datetime
    updated_at: datetime
```

---

### 8. Pipeline Status

Represents the overall state of a behavior session's progression through the pipeline.

**Attributes**:

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `status_id` | `str` | Primary Key, Unique | Generated from `{session_id}_status` |
| `session_id` | `str` | Foreign Key, Required | References Behavior Session.session_id |
| `current_stage` | `enum` | Required | See State Diagram below |
| `last_updated` | `datetime` | Auto | Timestamp of most recent stage transition |
| `error_messages` | `list[str]` | Default `[]` | List of error messages from failed stages |
| `created_at` | `datetime` | Auto | Timestamp of record creation |
| `updated_at` | `datetime` | Auto | Timestamp of most recent update |

**Pipeline Stages (enum values)**:
- `eln_synced`: ELN entry synced, directory created
- `awaiting_data`: Waiting for researcher to upload raw data files
- `preprocessing`: Data preprocessing task running
- `packaging`: NWB packaging task running
- `uploading`: DANDI upload task running
- `completed`: All stages completed successfully
- `failed`: Pipeline failed at some stage (requires manual intervention)

**Relationships**:
- `belongs to` **Behavior Session** (one-to-one)

**Lifecycle**:
1. Initialized when Behavior Session is created (stage: eln_synced)
2. Directory created → stage: awaiting_data
3. Watcher detects readiness → stage: preprocessing
4. Preprocessing completes → stage: packaging
5. NWB validation passes → stage: uploading
6. DANDI upload completes → stage: completed
7. Any task failure → stage: failed

**Validation Rules**:
- `status_id` must be unique
- `session_id` must exist in Behavior Session table
- `current_stage` transitions must follow state diagram (see below)
- `stage=failed` requires non-empty error_messages
- `stage=completed` requires successful NWB Dataset upload

**State Transition Diagram**:
```
┌─────────────┐
│ eln_synced  │
└─────┬───────┘
      │
      ▼
┌─────────────┐
│awaiting_data│◄─────┐
└─────┬───────┘      │
      │              │ (retry after failure)
      ▼              │
┌─────────────┐      │
│preprocessing├──────┤
└─────┬───────┘      │
      │              │
      ▼              │
┌─────────────┐      │
│  packaging  ├──────┤
└─────┬───────┘      │
      │              │
      ▼              │
┌─────────────┐      │
│  uploading  ├──────┤
└─────┬───────┘      │
      │              │
      ▼              │
┌─────────────┐      │
│  completed  │      │
└─────────────┘      │
                     │
      ┌──────────────┘
      │
      ▼
┌─────────────┐
│   failed    │
└─────────────┘
```

**Example (Pydantic Schema)**:
```python
from enum import Enum

class PipelineStage(str, Enum):
    ELN_SYNCED = "eln_synced"
    AWAITING_DATA = "awaiting_data"
    PREPROCESSING = "preprocessing"
    PACKAGING = "packaging"
    UPLOADING = "uploading"
    COMPLETED = "completed"
    FAILED = "failed"

class PipelineStatus(BaseModel):
    status_id: str
    session_id: str
    current_stage: PipelineStage
    last_updated: datetime
    error_messages: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
```

---

## Relationships Summary

**Entity Relationship Diagram (ERD)**:
```
┌──────────┐         ┌──────────┐         ┌─────────────┐
│ Subject  │◄───────┤ Surgery  │◄───────┤ ELN Entry   │
└────┬─────┘    1:N  └──────────┘    1:1  └─────────────┘
     │                      │                     │
     │ 1:N                  │                     │ 1:1
     │                      │                     │
     ▼                      ▼                     ▼
┌─────────────────┐   ┌─────────────────┐   ┌─────────────┐
│Behavior Session │◄──┤ Pipeline Status │   │             │
└────┬────────────┘1:1└─────────────────┘   │             │
     │                                        │             │
     │ 1:1                                    │             │
     ▼                                        │             │
┌──────────────────┐                         │             │
│Data Acquisition  │                         │             │
└────┬─────────────┘                         │             │
     │                                        │             │
     │ 1:N                                    │             │
     ▼                                        │             │
┌──────────────┐                             │             │
│Analysis Run  │                             │             │
└──────────────┘                             │             │
                                              │             │
┌──────────────┐         ┌─────────────────┐ │             │
│ NWB Dataset  │◄───────┤Behavior Session │◄┤             │
└──────────────┘    1:1  └─────────────────┘              │
```

**Foreign Key Constraints**:
- `Surgery.subject_id` → `Subject.subject_id` (CASCADE on delete)
- `BehaviorSession.subject_id` → `Subject.subject_id` (CASCADE on delete)
- `DataAcquisition.session_id` → `BehaviorSession.session_id` (CASCADE on delete)
- `NWBDataset.session_id` → `BehaviorSession.session_id` (CASCADE on delete)
- `PipelineStatus.session_id` → `BehaviorSession.session_id` (CASCADE on delete)
- `AnalysisRun.acquisition_id` → `DataAcquisition.acquisition_id` (CASCADE on delete)
- `ELNEntry.linked_entity_id` → `Subject|Surgery|BehaviorSession` (polymorphic, SET NULL on delete)

---

## JSON Schema Examples

### Complete Behavior Session Record (with relationships)

```json
{
  "subject": {
    "subject_id": "M001",
    "species": "mouse",
    "strain": "C57BL/6J",
    "sex": "M",
    "date_of_birth": "2024-06-15",
    "weight": 25.3,
    "surgery_history": ["M001_2024-09-01"],
    "notes": "Healthy male mouse for fiber photometry experiments",
    "created_at": "2024-09-01T10:00:00Z",
    "updated_at": "2025-10-27T14:30:00Z"
  },
  "surgery": {
    "surgery_id": "M001_2024-09-01",
    "subject_id": "M001",
    "surgery_date": "2024-09-01",
    "procedure_type": "fiber_implant",
    "implant_details": "400um fiber in NAc (AP +1.2, ML +0.8, DV -4.5)",
    "surgeon_name": "Dr. Jane Smith",
    "recovery_notes": "Normal recovery, active after 24h",
    "eln_entry_id": "LA_20240901_001",
    "created_at": "2024-09-01T10:00:00Z"
  },
  "behavior_session": {
    "session_id": "M001_2025-10-27_fear_conditioning",
    "subject_id": "M001",
    "session_date": "2025-10-27",
    "protocol_name": "fear_conditioning",
    "duration_minutes": 60,
    "trial_count": 10,
    "environmental_conditions": {
      "temperature_c": 22,
      "humidity_percent": 50,
      "lighting_lux": 100
    },
    "eln_entry_id": "LA_20251027_005",
    "created_at": "2025-10-27T09:00:00Z",
    "updated_at": "2025-10-27T14:00:00Z"
  },
  "data_acquisition": {
    "acquisition_id": "M001_2025-10-27_fear_conditioning_acq",
    "session_id": "M001_2025-10-27_fear_conditioning",
    "acquisition_date": "2025-10-27T10:00:00Z",
    "file_paths": [
      "experiments/M001/behavior/fear_conditioning/2025-10-27/raw/TDT_Tank/",
      "experiments/M001/behavior/fear_conditioning/2025-10-27/raw/protocol.csv",
      "experiments/M001/behavior/fear_conditioning/2025-10-27/raw/video_01.mp4"
    ],
    "file_types": ["TDT", "CSV", "MP4"],
    "tdt_tank_path": "experiments/M001/behavior/fear_conditioning/2025-10-27/raw/TDT_Tank/",
    "protocol_csv_path": "experiments/M001/behavior/fear_conditioning/2025-10-27/raw/protocol.csv",
    "video_paths": ["experiments/M001/behavior/fear_conditioning/2025-10-27/raw/video_01.mp4"],
    "acquisition_system_metadata": {
      "tdt_sampling_rate_hz": 1017.3,
      "tdt_channels": ["GCaMP", "TdTomato"],
      "video_fps": 30,
      "video_resolution": "1920x1080"
    },
    "readiness_status": "ready",
    "created_at": "2025-10-27T09:00:00Z",
    "updated_at": "2025-10-27T11:30:00Z"
  },
  "pipeline_status": {
    "status_id": "M001_2025-10-27_fear_conditioning_status",
    "session_id": "M001_2025-10-27_fear_conditioning",
    "current_stage": "packaging",
    "last_updated": "2025-10-27T14:00:00Z",
    "error_messages": [],
    "created_at": "2025-10-27T09:00:00Z",
    "updated_at": "2025-10-27T14:00:00Z"
  },
  "nwb_dataset": {
    "nwb_id": "M001_2025-10-27_fear_conditioning_nwb",
    "session_id": "M001_2025-10-27_fear_conditioning",
    "file_path": "/storage/experiments/M001/behavior/fear_conditioning/2025-10-27/processed/M001_2025-10-27_fear_conditioning.nwb",
    "creation_timestamp": "2025-10-27T14:30:00Z",
    "validation_status": true,
    "validation_report_path": "/storage/experiments/M001/behavior/fear_conditioning/2025-10-27/processed/validation_report.json",
    "code_version_hash": "0af5abb3e8d9f72c1b4a5e6d7f8c9d0e1f2a3b4c",
    "pixi_lock_hash": "sha256:abcdef1234567890",
    "dandi_asset_id": "dandiset/000123/asset/456789",
    "dandi_upload_timestamp": "2025-10-27T15:00:00Z",
    "created_at": "2025-10-27T14:30:00Z",
    "updated_at": "2025-10-27T15:00:00Z"
  },
  "eln_entry": {
    "entry_id": "LA_20251027_005",
    "eln_backend": "labarchives",
    "entry_type": "behavior",
    "creation_date": "2025-10-27T08:30:00Z",
    "last_modified_date": "2025-10-27T08:45:00Z",
    "researcher_name": "Dr. John Doe",
    "parsed_metadata": {
      "subject_id": "M001",
      "session_date": "2025-10-27",
      "protocol_name": "fear_conditioning",
      "duration_minutes": 60,
      "trial_count": 10
    },
    "raw_content": "<html><p>Fear conditioning experiment...</p></html>",
    "created_at": "2025-10-27T09:00:00Z",
    "updated_at": "2025-10-27T09:00:00Z"
  },
  "analysis_runs": [
    {
      "run_id": "M001_2025-10-27_fear_conditioning_preprocessing_1730026800",
      "acquisition_id": "M001_2025-10-27_fear_conditioning_acq",
      "run_type": "preprocessing",
      "start_time": "2025-10-27T12:00:00Z",
      "end_time": "2025-10-27T13:30:00Z",
      "status": "completed",
      "error_logs": [],
      "input_files": [
        "experiments/M001/behavior/fear_conditioning/2025-10-27/raw/TDT_Tank/"
      ],
      "output_files": [
        "experiments/M001/behavior/fear_conditioning/2025-10-27/processed/preprocessed_timeseries.h5"
      ],
      "retry_count": 0,
      "created_at": "2025-10-27T12:00:00Z",
      "updated_at": "2025-10-27T13:30:00Z"
    },
    {
      "run_id": "M001_2025-10-27_fear_conditioning_packaging_1730030800",
      "acquisition_id": "M001_2025-10-27_fear_conditioning_acq",
      "run_type": "packaging",
      "start_time": "2025-10-27T14:00:00Z",
      "end_time": "2025-10-27T14:30:00Z",
      "status": "completed",
      "error_logs": [],
      "input_files": [
        "experiments/M001/behavior/fear_conditioning/2025-10-27/processed/preprocessed_timeseries.h5",
        "experiments/M001/behavior/fear_conditioning/2025-10-27/metadata/metadata.csv"
      ],
      "output_files": [
        "experiments/M001/behavior/fear_conditioning/2025-10-27/processed/M001_2025-10-27_fear_conditioning.nwb"
      ],
      "retry_count": 0,
      "created_at": "2025-10-27T14:00:00Z",
      "updated_at": "2025-10-27T14:30:00Z"
    }
  ]
}
```

---

## Implementation Notes

### Database Technology (Future Consideration)

This data model is currently documented as logical entities with Pydantic schemas. Future implementation may use:
- **SQLite** (development/single-lab deployments)
- **PostgreSQL** (production/multi-lab deployments)
- **SQLAlchemy ORM** (Python database abstraction layer)

For MVP (Milestone 1-2), entities may be stored as:
- JSON manifest files (`.elabftw-manifest.json`) in experiment directories
- In-memory data structures (FastAPI service)
- Redis cache (for pipeline status and job state)

### Versioning and Migrations

- NWB schema mappings are versioned (`nwb/schemas/v1.0-fiber-photometry.json`)
- Entity schema changes require migration scripts
- Backward compatibility maintained for ELN field parsing

### Concurrency and Locking

- Celery idempotency keys prevent duplicate job execution
- File system locking for directory creation (storage adapters)
- Optimistic locking for pipeline status updates (compare-and-swap on `last_updated`)

---

**Document Status**: Complete
**Next Steps**: Review with stakeholders, proceed to `contracts/` definitions
