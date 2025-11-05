# ELN-to-DANDI Pipeline: Technical Research Document

**Version**: 1.0
**Date**: 2025-10-27
**Status**: Complete
**Purpose**: Comprehensive technical research to inform Phase 1 design and implementation decisions

---

## Table of Contents

1. [LabArchives API Integration](#1-labarchives-api-integration)
2. [eLabFTW API Integration](#2-elabftw-api-integration)
3. [TDT Tank Data Processing](#3-tdt-tank-data-processing)
4. [NWB Schema Mapping](#4-nwb-schema-mapping)
5. [File System Watcher Patterns](#5-file-system-watcher-patterns)
6. [DANDI Upload Best Practices](#6-dandi-upload-best-practices)
7. [Celery Architecture for Scientific Pipelines](#7-celery-architecture-for-scientific-pipelines)
8. [Multi-Storage Backend Patterns](#8-multi-storage-backend-patterns)

---

## 1. LabArchives API Integration

### Decision

**Use `labarchives-py` wrapper library** with REST API authentication using app authentication tokens, implementing polling-based synchronization with exponential backoff retry logic via `tenacity`.

### Rationale

1. **NIH Compliance**: LabArchives is NIH-approved and supports the 2023 Data Management and Sharing (DMS) policy
2. **Existing Python Wrapper**: The `labarchives-py` library (https://github.com/mcmero/labarchives-py) provides a clean abstraction over the REST API
3. **Mature REST API**: LabArchives provides a documented REST API with predictable endpoint patterns (`https://<baseurl>/api/<api_class>/<api_method>`)
4. **SSO Support**: Supports institutional SSO with app authentication tokens, critical for NIH deployments

### Alternatives Considered

1. **Direct REST API calls with `requests`**
   - **Rejected**: More verbose, requires manual session management and error handling
   - Lower-level control not needed for standard ELN operations

2. **Official LabArchives SDK**
   - **Rejected**: No official Python SDK exists; only REST API documentation available
   - Community wrapper provides sufficient abstraction

3. **Selenium/Web Scraping**
   - **Rejected**: Brittle, violates terms of service, no API access control
   - Not suitable for production automation

### Implementation Notes

#### Authentication Flow

```python
# Configuration-based authentication
config = {
    "api_url": "https://<instance>.labarchives.com/api",
    "access_key_id": os.environ["LABARCHIVES_ACCESS_KEY"],
    "access_password": os.environ["LABARCHIVES_ACCESS_PASSWORD"]
}

# For SSO users: obtain app authentication token from
# User Profile > LA App authentication
```

#### Polling Strategy

- **Initial poll interval**: 60 seconds (configurable)
- **Backoff strategy**: Exponential with jitter to avoid thundering herd
- **Rate limit handling**: Monitor for HTTP 429 responses, respect `Retry-After` headers
- **Change detection**: Track last sync timestamp per project; query notebooks modified since last poll

#### Key API Endpoints

| Operation | Endpoint Pattern | Response |
|-----------|-----------------|----------|
| List notebooks | `/api/notebooks/list` | Array of notebook metadata |
| Get notebook tree | `/api/notebooks/get_tree` | Hierarchical structure |
| Get entry | `/api/entries/get_entry` | Entry HTML + attachments list |
| Download attachment | `/api/attachments/download` | Binary stream |
| Add note | `/api/entries/add_note` | Entry update confirmation |

#### Metadata Extraction Patterns

LabArchives stores data in HTML format with attachments. Key extraction patterns:

1. **Parse HTML entries** using `BeautifulSoup` to extract:
   - Subject metadata (subject ID, session date, experiment type)
   - Structured tables (parameters, equipment settings)
   - Links to attachments (TDT tank references, video file names)

2. **Attachment metadata** from JSON responses:
   ```json
   {
     "attachment_id": "12345",
     "filename": "subject_001_20250101_tank.zip",
     "size": 1048576,
     "upload_date": "2025-01-01T10:00:00Z"
   }
   ```

3. **Custom fields**: Look for standardized HTML `<div>` sections with `data-field` attributes

#### Rate Limits

- **Documented limits**: Not publicly specified; observe response times
- **Best practice**: Limit to 10 concurrent requests per instance
- **Backoff on 429**: Use exponential backoff with `tenacity` library
- **Monitoring**: Track API latency and error rates; alert on sustained 5xx errors

#### Gotchas

1. **HTML parsing brittleness**: Users can format entries arbitrarily; implement robust HTML parsing with fallbacks
2. **Attachment size**: Large TDT tanks can exceed API timeout limits; implement chunked/resumable downloads
3. **Entry versions**: LabArchives maintains version history; always fetch latest version explicitly
4. **Concurrent modifications**: Implement optimistic locking or last-write-wins strategy with conflict detection

### References

- **LabArchives API Docs**: https://mynotebook.labarchives.com/share/LabArchives%20API/
- **labarchives-py wrapper**: https://github.com/mcmero/labarchives-py
- **NIH DMS Policy Support**: https://www.labarchives.com/blog/labarchives-supports-nih-data-management-and-sharing-policy
- **Authentication Guide**: Login via https://auth-service.labarchives.com/ for app token generation

---

## 2. eLabFTW API Integration

### Decision

**Use `elabapi-python` official SDK (v5.3.0+)** with API key authentication, leveraging REST API v2 for all operations.

### Rationale

1. **Official SDK**: Maintained by eLabFTW team, guaranteed compatibility with REST API v2
2. **Type-safe API**: Generated OpenAPI client provides IntelliSense and compile-time checks
3. **Active Development**: Latest release October 2025 (v5.3.0), actively maintained
4. **Simple Authentication**: API key-based auth, simpler than OAuth2 for server-to-server communication
5. **Open Source**: Self-hosted option gives full control over instance, important for sensitive research data

### Alternatives Considered

1. **elabapy (legacy library)**
   - **Rejected**: Older library targeting REST API v1, not recommended for new projects
   - Official `elabapi-python` supersedes it

2. **Direct REST API calls**
   - **Rejected**: SDK provides better error handling, retries, and type safety
   - Manual API versioning management required

3. **GraphQL API**
   - **Rejected**: eLabFTW does not expose GraphQL endpoint
   - REST API v2 is the official interface

### Implementation Notes

#### Authentication Setup

```python
import elabapi_python

# Configuration
configuration = elabapi_python.Configuration()
configuration.host = "https://eln.example.org/api/v2"

# API client with key
api_client = elabapi_python.ApiClient(configuration)
api_client.set_default_header(
    header_name='Authorization',
    header_value=os.environ['ELABFTW_API_KEY']  # Format: "5-abc123..."
)

# Instantiate specific API clients
experiments_api = elabapi_python.ExperimentsApi(api_client)
items_api = elabapi_python.ItemsApi(api_client)
```

#### API Key Generation

1. Navigate to user Settings page in eLabFTW
2. Create new API key with descriptive name (e.g., "DANDI-Pipeline-Production")
3. Set appropriate access level (read-only for sync, write for status updates)
4. Store key securely; treat like password (never commit to git)

#### Key Operations

| Operation | SDK Method | Notes |
|-----------|------------|-------|
| List experiments | `experiments_api.read_experiments()` | Supports filtering by date, category |
| Get experiment details | `experiments_api.read_experiment(id)` | Returns full metadata + body HTML |
| List items | `items_api.read_items()` | Query by category (e.g., "Fiber Photometry Data") |
| Update experiment | `experiments_api.patch_experiment(id, body)` | Add status updates (e.g., "NWB packaging complete") |
| Download attachment | `experiments_api.read_experiment_upload(id, upload_id)` | Binary response |
| Upload attachment | `experiments_api.post_experiment_upload(id, file)` | Returns upload metadata |

#### Metadata Parsing

eLabFTW stores structured metadata in:

1. **Custom fields** (JSON): Access via `experiment.metadata` as structured dict
   ```python
   subject_id = experiment.metadata.get('subject_id')
   session_date = experiment.metadata.get('session_date')
   ```

2. **Body HTML**: Parse with `BeautifulSoup` for unstructured notes
3. **Tags**: Use for categorization (e.g., `#fiber-photometry`, `#ready-for-packaging`)
4. **Status**: Track workflow stages (e.g., "Data Collected", "NWB Created", "Uploaded to DANDI")

#### Status Update Mechanism

Implement two-way communication:

1. **Poll for ready entries**: Query experiments with specific tag/status indicating readiness
2. **Update status on progress**:
   ```python
   experiments_api.patch_experiment(
       id=entry_id,
       body={
           'custom_id': f'DANDI-{dandiset_id}',
           'metadata': {
               'nwb_file': nwb_filepath,
               'dandi_url': f'https://dandiarchive.org/dandiset/{dandiset_id}',
               'processing_timestamp': datetime.utcnow().isoformat()
           }
       }
   )
   ```

3. **Append notes**: Use `experiments_api.post_experiment_comment()` to log pipeline events

#### Rate Limits and Performance

- **Self-hosted**: No external rate limits; respect server capacity
- **Batch queries**: SDK supports pagination; fetch in reasonable chunks (50-100 entries)
- **Connection pooling**: SDK manages connection pool automatically
- **Timeouts**: Configure request timeouts for large file downloads (default 60s may be insufficient)

#### Gotchas

1. **API versioning**: URL includes `/v2`; ensure compatibility with future v3
2. **Experiment vs Item**: eLabFTW distinguishes "Experiments" (data) from "Items" (resources); our data lives in Experiments
3. **Permissions**: API key inherits user permissions; use dedicated service account
4. **HTML sanitization**: Body content may contain user-supplied HTML; sanitize before displaying

### References

- **Official SDK**: https://github.com/elabftw/elabapi-python
- **PyPI Package**: https://pypi.org/project/elabapi-python/
- **REST API v2 Docs**: https://doc.elabftw.net/api/elabapi-html/
- **API Documentation**: https://doc.elabftw.net/api.html
- **Example Scripts**: Check `examples/` folder in GitHub repo (e.g., `00-getting-started.py`)

---

## 3. TDT Tank Data Processing

### Decision

**Use TDT's official Python package** for tank data reading, supplemented by **GuPPy** for standardized signal processing and dFF calculation.

### Rationale

1. **Official Support**: TDT provides Python SDK for offline data analysis with documented tank structure
2. **Standard Format**: Tank/Block structure is well-defined across TDT systems
3. **Community Tools**: GuPPy provides validated dFF methods from published research (Martianova et al.)
4. **Compatibility**: Works with TDT Synapse-generated data, the primary acquisition software for fiber photometry
5. **NIH Acceptance**: TDT is widely used in NIH-funded neuroscience labs

### Alternatives Considered

1. **MATLAB TDT SDK + MATLAB runtime**
   - **Rejected**: Requires MATLAB license or runtime, deployment complexity
   - Python-first approach preferred for consistency

2. **Custom tank parser**
   - **Rejected**: Tank binary format is complex; official SDK handles edge cases
   - Reinventing wheel increases maintenance burden

3. **Directly use Andrews Lab GUI**
   - **Rejected**: GUI-based tool, not suitable for automated pipeline
   - Good reference implementation for validation

4. **phototdt package**
   - **Considered**: Lightweight alternative for photometry-specific parsing
   - **Limitation**: Less actively maintained than GuPPy; use as fallback

### Implementation Notes

#### TDT Tank Structure

```
Tank/
├── Block-1/                 # Recording session
│   ├── TDT_header           # Metadata
│   ├── Store1_Ch1_*.sev     # Continuous data streams
│   ├── Store2_Ch1_*.sev
│   └── ...
├── Block-2/
└── ...
```

**Key concepts:**
- **Tank**: Container for all recordings (typically one per subject)
- **Block**: Individual recording session (one per day/experiment)
- **Store**: Data stream (e.g., 465nm signal, 405nm isosbestic control)
- **Epocs**: Event markers (TTL pulses, behavior timestamps)

#### Python TDT Package Usage

```python
import tdt

# Read block data
data = tdt.read_block('/path/to/Tank', block='Block-1')

# Access stores
signal_465 = data.streams['_465A'].data  # GCaMP signal
signal_405 = data.streams['_405A'].data  # Isosbestic control
sampling_rate = data.streams['_465A'].fs

# Access event markers
epocs = data.epocs
behavior_ttl = epocs['PC0_'].onset  # Example behavior event
```

#### Fiber Photometry Signal Extraction

Standard TDT fiber photometry setup records:
1. **465nm channel**: GCaMP fluorescence (Ca2+ indicator)
2. **405nm channel**: Isosbestic control (motion/bleaching artifact)
3. **560nm channel** (optional): Tdtomato or other red indicator

**Store naming conventions** (TDT Synapse defaults):
- `_465A`, `_405A`, `_560A` for single fiber
- `_465B`, `_405B` for second fiber (multi-fiber rigs)

#### GuPPy Integration for dFF

```python
from guppy.photometry import dff_calculator

# Calculate dFF using standardized method
dff, baseline = dff_calculator(
    signal=signal_465,
    control=signal_405,
    method='martianova',  # Published method
    smooth_window=10,      # 10Hz smoothing
    baseline_percentile=10
)
```

**dFF methods available:**
- **martianova**: Polynomial fitting of control to signal (recommended)
- **exponential**: Exponential decay correction
- **sliding_percentile**: Rolling baseline calculation

#### Best Practices

1. **Validate tank integrity**: Check for missing blocks, corrupted SEV files
   ```python
   if not os.path.exists(os.path.join(tank_path, 'Block-1', 'TDT_header')):
       raise ValueError("Invalid tank structure")
   ```

2. **Extract session metadata**: Parse TDT_header for sampling rates, start time, duration
3. **Handle multi-block tanks**: Iterate blocks if multiple sessions in one tank (rare)
4. **Artifact detection**: Flag periods with extreme signal values (saturation, disconnect)
5. **Align epocs with behavior**: Correlate TDT TTL timestamps with AnyMaze/behavior timestamps

#### Processing Pipeline Sequence

1. **Read tank**: `tdt.read_block()`
2. **Extract stores**: Separate signal and control channels
3. **Preprocess**: Smooth, detrend, correct for bleaching
4. **Calculate dFF**: Apply GuPPy method
5. **Extract epocs**: Map event markers to behavior
6. **Export to NWB**: Use `FiberPhotometryResponseSeries`

#### Gotchas

1. **Large files**: TDT tanks can be 10+ GB; read_block loads entire block into memory
   - **Mitigation**: Stream processing for long recordings, or subsample for initial NWB
2. **SEV vs TDT format**: Older systems use TDT format; newer use SEV (both supported)
3. **Store name variability**: Users can customize store names; implement flexible parsing
4. **Timestamp alignment**: TDT timestamps are in seconds since block start; align to session start
5. **Multi-fiber rigs**: Handle variable channel counts (1-4 fibers common)

### References

- **TDT Python SDK**: https://www.tdt.com/docs/sdk/offline-data-analysis/offline-data-python/
- **Fiber Photometry User Guide**: https://www.tdt.com/docs/fiber-photometry-user-guide/data-analysis/
- **GuPPy Publication**: https://www.nature.com/articles/s41598-021-03626-9 (Scientific Reports, 2021)
- **GuPPy GitHub**: https://github.com/LernerLab/GuPPy
- **TDT Example Code**: https://www.tdt.com/docs/sdk/offline-data-analysis/offline-data-python/examples/FibPhoEpocAveraging/
- **Andrews Lab GUI**: https://github.com/Andrews-Lab/Fiber_photometry_analysis (reference implementation)
- **phototdt package**: https://github.com/matiasandina/phototdt (lightweight alternative)

---

## 4. NWB Schema Mapping

### Decision

**Use `ndx-fiber-photometry` extension** with `pynwb` for NWB file creation, leveraging `neuroconv` for automated conversion from TDT format to NWB structure.

### Rationale

1. **Official Extension**: `ndx-fiber-photometry` is catalogued in NWB Extension Catalog, ensuring long-term support
2. **Community Standard**: Developed by CatalystNeuro, leaders in NWB ecosystem
3. **Comprehensive Metadata**: Supports device models, experimental setup, and provenance tracking
4. **DANDI Compatibility**: DANDI Archive expects NWB files; this extension is DANDI-ready
5. **Future-proof**: Aligned with NWB 2.x schema evolution

### Alternatives Considered

1. **Core NWB without extension**
   - **Rejected**: No native fiber photometry structures; would require custom DynamicTable
   - Less discoverable and interpretable by community tools

2. **ndx-photometry (alternative extension)**
   - **Rejected**: Less mature, fewer adopters than ndx-fiber-photometry
   - ndx-fiber-photometry is more actively maintained

3. **Custom NWB extension**
   - **Rejected**: Unnecessary duplication; ndx-fiber-photometry covers our needs
   - Custom extensions reduce interoperability

### Implementation Notes

#### Key Data Structures

**Hierarchical organization:**

```
NWBFile
├── general/
│   ├── subject (Subject)
│   ├── FiberPhotometryViruses (container)
│   ├── FiberPhotometryVirusInjections (container)
│   ├── FiberPhotometryIndicators (container)
│   └── devices/ (ExcitationSource, Photodetector, OpticalFiber)
├── acquisition/
│   └── FiberPhotometryResponseSeries (time series data)
└── processing/
    └── FiberPhotometry (analysis results, dFF)
```

#### Core Classes and Metadata Fields

##### 1. Device Model-Instance Pattern

**ExcitationSourceModel** (specification):
- `model_name`: e.g., "Thorlabs M470F3"
- `wavelength_center`: 470 (nm)
- `wavelength_range`: [460, 480]
- `power_max`: 50 (mW)

**ExcitationSource** (instance):
- References model
- `power`: Actual power used (mW)
- `intensity`: Light intensity at fiber tip

**PhotodetectorModel**:
- `model_name`: e.g., "Newport 2151"
- `type`: "PMT" or "photodiode"
- `wavelength_min`, `wavelength_max`: Detection range

**Photodetector** (instance):
- `gain`: Detector gain setting
- `sampling_rate`: Hz

**OpticalFiberModel**:
- `core_diameter`: micrometers
- `numerical_aperture`: e.g., 0.39

**OpticalFiber** (instance):
- Stereotactic coordinates:
  - `anterior_posterior`: mm from bregma
  - `medial_lateral`: mm from bregma
  - `dorsal_ventral`: mm from brain surface
  - `angle_pitch`, `angle_yaw`, `angle_roll`: degrees
  - `hemisphere`: "left" or "right"
  - `reference_point`: "Bregma" (default)

**DichroicMirrorModel**:
- `reflection_band_center`, `reflection_band_width`: nm
- `transmission_band_center`, `transmission_band_width`: nm

**BandOpticalFilterModel**:
- `center_wavelength`: nm (e.g., 525 for emission filter)
- `bandwidth`: nm (e.g., 50 for 525/50)

**EdgeOpticalFilterModel**:
- `cutoff_wavelength`: nm
- `cutoff_type`: "longpass" or "shortpass"

##### 2. Experimental Metadata Containers

**FiberPhotometryViruses**:
- Each virus entry contains:
  - `viral_vector`: e.g., "AAV9-CaMKII-GCaMP6f"
  - `serotype`: e.g., "AAV9"
  - `titer`: Viral titer (vg/ml)
  - `manufacturer`: e.g., "Addgene"
  - `lot_number`: Batch tracking

**FiberPhotometryVirusInjections**:
- `injection_volume`: microliters
- `injection_rate`: uL/min
- `coordinates`: AP, ML, DV
- `virus`: Reference to virus entry

**FiberPhotometryIndicators**:
- `indicator_name`: e.g., "GCaMP6f"
- `fluorophore`: e.g., "GFP"
- `excitation_wavelength`: nm
- `emission_wavelength`: nm

##### 3. Data Storage

**FiberPhotometryTable**:
- Central organizational structure (DynamicTable)
- Each row = one fiber/channel:
  - `location`: Brain region (e.g., "VTA", "NAc")
  - `excitation_wavelength`: nm
  - `emission_wavelength`: nm
  - `indicator`: Reference to indicator
  - `optical_fiber`: Reference to fiber instance
  - `excitation_source`: Reference to light source
  - `photodetector`: Reference to detector
  - `dichroic_mirror`: Optional reference
  - `emission_filter`: Optional reference
  - `commanded_voltage_series`: Reference to control signal

**FiberPhotometryResponseSeries**:
- Time series data (extends TimeSeries)
- `data`: Array of fluorescence values (dFF or raw)
- `timestamps`: Aligned timestamps (seconds)
- `fiber_photometry_table_region`: Links to specific fiber in table
- `unit`: "dF/F" or "a.u." (arbitrary units)

**CommandedVoltageSeries**:
- Control signal to LED/laser
- `data`: Voltage values
- `frequency`: Modulation frequency (Hz)

#### Field Mappings: ELN → NWB

| ELN Field (Example) | NWB Location | Type | Notes |
|---------------------|--------------|------|-------|
| Subject ID | `NWBFile.subject.subject_id` | string | Unique identifier |
| Subject Species | `NWBFile.subject.species` | string | "Mus musculus" (Latin binomial) |
| Subject Age | `NWBFile.subject.age` | string | ISO 8601 duration (e.g., "P90D") |
| Subject Sex | `NWBFile.subject.sex` | string | "F", "M", "U", "O" |
| Subject Weight | `NWBFile.subject.weight` | string | e.g., "25g" |
| Session Date/Time | `NWBFile.session_start_time` | datetime | ISO 8601 with timezone |
| Experimenter | `NWBFile.experimenter` | list[string] | ["Last, First"] |
| Lab | `NWBFile.lab` | string | Lab name |
| Institution | `NWBFile.institution` | string | Full name |
| Virus Type | `FiberPhotometryViruses.viral_vector` | string | Full AAV construct name |
| Injection Coordinates | `FiberPhotometryVirusInjections.coordinates` | tuple | (AP, ML, DV) |
| Fiber Location | `OpticalFiber.anterior_posterior` (etc.) | float | Stereotactic coordinates |
| Brain Region | `FiberPhotometryTable['location']` | string | Abbreviated (e.g., "VTA") |
| LED Wavelength | `ExcitationSource.wavelength_center` | float | nm |
| LED Power | `ExcitationSource.power` | float | mW |
| PMT Gain | `Photodetector.gain` | float | Detector-specific units |
| Sampling Rate | `FiberPhotometryResponseSeries.rate` | float | Hz |

#### pynwb Usage Patterns

```python
from pynwb import NWBFile, NWBHDF5IO
from pynwb.file import Subject
from ndx_fiber_photometry import (
    FiberPhotometry,
    FiberPhotometryTable,
    FiberPhotometryResponseSeries,
    ExcitationSource,
    Photodetector,
    OpticalFiber,
    # ... other classes
)
from datetime import datetime
from dateutil.tz import tzlocal

# Create NWB file
nwbfile = NWBFile(
    session_description="Fiber photometry recording in VTA during reward task",
    identifier=f"{subject_id}_{session_date}",  # Unique identifier
    session_start_time=datetime(2025, 1, 15, 10, 0, 0, tzinfo=tzlocal()),
    experimenter=["Doe, Jane"],
    lab="Smith Lab",
    institution="NIH",
    subject=Subject(
        subject_id=subject_id,
        age="P90D",
        sex="M",
        species="Mus musculus",
        weight="25g"
    )
)

# Add device models
excitation_model = ExcitationSourceModel(
    name="LED_470nm_model",
    model_name="Thorlabs M470F3",
    wavelength_center=470.0,
    wavelength_range=[460.0, 480.0],
    power_max=50.0
)

# Add device instance
excitation_source = ExcitationSource(
    name="LED_470nm",
    model=excitation_model,
    power=20.0  # Actual power used
)
nwbfile.add_device(excitation_source)

# Add fiber metadata
optical_fiber = OpticalFiber(
    name="optical_fiber_VTA",
    model=OpticalFiberModel(...),
    anterior_posterior=-3.2,  # mm from bregma
    medial_lateral=0.5,
    dorsal_ventral=-4.5,
    hemisphere="left",
    reference_point="Bregma"
)
nwbfile.add_device(optical_fiber)

# Create photometry table
fiber_photometry_table = FiberPhotometryTable(
    name="fiber_photometry_table",
    description="Fiber photometry metadata"
)
fiber_photometry_table.add_row(
    location="VTA",
    excitation_wavelength=470.0,
    emission_wavelength=525.0,
    indicator=gcamp_indicator,
    optical_fiber=optical_fiber,
    excitation_source=excitation_source,
    photodetector=photodetector
)

# Add time series data
response_series = FiberPhotometryResponseSeries(
    name="fiber_photometry_response_series",
    description="dFF signal from VTA",
    data=dff_data,  # Numpy array
    timestamps=timestamps,  # Seconds since session start
    fiber_photometry_table_region=fiber_photometry_table.create_table_region(
        region=[0],  # First row
        description="VTA fiber"
    ),
    unit="dF/F"
)
nwbfile.add_acquisition(response_series)

# Write to file
with NWBHDF5IO("subject_001_20250115.nwb", mode="w") as io:
    io.write(nwbfile)
```

#### Validation Best Practices

1. **Use pynwb validation tool**:
   ```bash
   python -m pynwb.validate subject_001_20250115.nwb
   ```

2. **Validate against cached namespace** (includes extensions):
   ```bash
   python -m pynwb.validate subject_001_20250115.nwb
   # Output: "no errors found" if valid
   ```

3. **Validate against specific NWB version**:
   ```bash
   python -m pynwb.validate --no-cached-namespace subject_001_20250115.nwb
   ```

4. **Metadata conventions**:
   - Age: ISO 8601 duration (e.g., "P90D" for 90 days)
   - Species: Latin binomial (e.g., "Mus musculus", not "mouse")
   - Sex: "F", "M", "U" (unknown), "O" (other)
   - Coordinates: Always specify reference point (e.g., "Bregma")

5. **Provenance tracking**:
   - Store Git commit SHA in `NWBFile.source_script`
   - Record processing parameters in `NWBFile.notes`
   - Use `NWBFile.related_publications` for protocol DOIs

#### NeuroConv Integration

NeuroConv can automate conversion from TDT to NWB:

```python
from neuroconv import NWBConverter
from neuroconv.datainterfaces import TDTDataInterface

# Define data interface
class FiberPhotometryConverter(NWBConverter):
    data_interface_classes = {
        'TDT': TDTDataInterface
    }

# Run conversion
converter = FiberPhotometryConverter(
    source_data={'TDT': {'folder_path': '/path/to/tank'}}
)
metadata = converter.get_metadata()
# Update metadata with ELN fields
metadata['NWBFile']['session_description'] = eln_session_description
metadata['Subject'] = eln_subject_metadata

converter.run_conversion(
    nwbfile_path='output.nwb',
    metadata=metadata,
    overwrite=True
)
```

**Benefits**:
- Handles chunk optimization automatically
- Applies compression for large datasets
- Validates schema during conversion

#### Gotchas

1. **Extension installation**: Install ndx-fiber-photometry in Python environment:
   ```bash
   pixi add ndx-fiber-photometry
   ```

2. **Datetime timezone**: Always specify timezone for `session_start_time` (use `dateutil.tz.tzlocal()`)

3. **Unit consistency**: NWB expects SI units; convert ELN values (e.g., g to kg if needed)

4. **Table regions**: Must create table region references for linking series to table rows

5. **Large datasets**: Use chunking and compression:
   ```python
   response_series = FiberPhotometryResponseSeries(
       ...,
       data=H5DataIO(data=dff_data, compression='gzip', compression_opts=4)
   )
   ```

6. **Validation fails on custom fields**: Use `allow_extra_fields=True` for flexibility

### References

- **ndx-fiber-photometry GitHub**: https://github.com/catalystneuro/ndx-fiber-photometry
- **PyPI Package**: https://pypi.org/project/ndx-photometry/
- **NWB Extension Catalog**: https://github.com/nwb-extensions/ndx-photometry-record
- **PyNWB Documentation**: https://pynwb.readthedocs.io/
- **PyNWB Validation Guide**: https://pynwb.readthedocs.io/en/stable/validation.html
- **NWB Specification**: https://nwb-schema.readthedocs.io/
- **NeuroConv**: https://neuroconv.readthedocs.io/
- **NWB Overview Tutorial**: https://nwb-overview.readthedocs.io/en/latest/conversion_tutorial/02_format_conversions.html
- **CatalystNeuro GitHub**: https://github.com/catalystneuro

---

## 5. File System Watcher Patterns

### Decision

**Use `watchfiles` (Rust-based)** for high-performance file system monitoring with custom completion detection logic based on **file size stability** and **manifest file patterns**.

### Rationale

1. **Performance**: watchfiles uses Rust `notify` library with native OS file system events (inotify on Linux, FSEvents on macOS, ReadDirectoryChangesW on Windows)
2. **Modern Design**: Addresses watchdog's limitations (threading issues, debouncing challenges)
3. **Lower Resource Usage**: Minimal CPU and memory overhead vs polling-based approaches
4. **Active Development**: Maintained by Samuel Colvin (Pydantic author), strong community support
5. **Async Support**: Native asyncio integration for non-blocking monitoring

### Alternatives Considered

1. **watchdog**
   - **Rejected**: Threading-based concurrency is less efficient
   - Reports of scalability issues with large directory trees (100k+ files)
   - More complex debouncing required

2. **watchgod** (predecessor to watchfiles)
   - **Rejected**: Deprecated in favor of watchfiles
   - Migration guide available; watchfiles is direct successor

3. **Polling with `os.scandir()`**
   - **Rejected**: High CPU usage, poor latency for large directories
   - Misses rapid changes between poll intervals

4. **inotify/pyinotify (Linux-specific)**
   - **Rejected**: Not cross-platform
   - watchfiles abstracts OS-specific APIs

### Implementation Notes

#### Basic watchfiles Usage

```python
from watchfiles import watch

for changes in watch('/path/to/watched/dir'):
    # changes is a set of (Change enum, path) tuples
    for change_type, file_path in changes:
        if change_type == Change.added:
            handle_new_file(file_path)
        elif change_type == Change.modified:
            handle_file_update(file_path)
```

**Change types**:
- `Change.added`: New file created
- `Change.modified`: File content changed
- `Change.deleted`: File removed

#### Completion Detection Strategies

File system events fire during writes, not after completion. Implement completion detection:

##### Strategy 1: File Size Stability

```python
import time
from pathlib import Path

def wait_for_completion(file_path: Path, stable_duration: float = 3.0, poll_interval: float = 0.5):
    """Wait until file size is stable for stable_duration seconds."""
    last_size = -1
    stable_since = None

    while True:
        try:
            current_size = file_path.stat().st_size
        except FileNotFoundError:
            return False  # File disappeared

        if current_size == last_size:
            if stable_since is None:
                stable_since = time.time()
            elif time.time() - stable_since >= stable_duration:
                return True  # Stable long enough
        else:
            stable_since = None  # Size changed, reset

        last_size = current_size
        time.sleep(poll_interval)
```

**When to use**: Large files (TDT tanks, video files) that copy over network

##### Strategy 2: Manifest File Pattern

```python
def watch_with_manifest(watch_dir: Path, manifest_name: str = ".complete"):
    """Wait for manifest file indicating completion."""
    for changes in watch(watch_dir):
        for change_type, file_path in changes:
            if change_type == Change.added and file_path.name == manifest_name:
                # Manifest detected, process directory
                process_completed_session(watch_dir)
```

**Manifest examples**:
- `.complete` marker file
- `MANIFEST.json` with file checksums
- `session_ready.flag`

**When to use**: Controlled upload scenarios where source can signal completion

##### Strategy 3: Timeout-Based with File Count

```python
from datetime import datetime, timedelta

def watch_with_timeout(watch_dir: Path, expected_files: set[str], timeout: timedelta = timedelta(minutes=5)):
    """Wait for expected files with timeout."""
    detected_files = set()
    last_change = datetime.now()

    for changes in watch(watch_dir):
        for change_type, file_path in changes:
            if change_type == Change.added:
                detected_files.add(file_path.name)
                last_change = datetime.now()

        # Check completion
        if expected_files.issubset(detected_files):
            return True  # All expected files present

        # Check timeout
        if datetime.now() - last_change > timeout:
            raise TimeoutError(f"Timeout waiting for files: {expected_files - detected_files}")
```

**When to use**: Predictable session structures (e.g., TDT tank + AnyMaze CSV + 2 videos)

#### Debouncing Pattern

Prevent redundant processing during rapid changes:

```python
import asyncio
from collections import defaultdict
from datetime import datetime, timedelta

class DebouncedWatcher:
    def __init__(self, watch_dir: Path, debounce_delay: timedelta = timedelta(seconds=2)):
        self.watch_dir = watch_dir
        self.debounce_delay = debounce_delay
        self.pending_changes: dict[Path, datetime] = {}

    async def watch(self):
        async for changes in watchfiles.awatch(self.watch_dir):
            for change_type, file_path in changes:
                self.pending_changes[Path(file_path)] = datetime.now()

            # Process debounced changes
            await self.process_pending()

    async def process_pending(self):
        now = datetime.now()
        to_process = [
            path for path, timestamp in self.pending_changes.items()
            if now - timestamp >= self.debounce_delay
        ]

        for path in to_process:
            await self.handle_file(path)
            del self.pending_changes[path]
```

#### Handling Network Drives

Network file systems (OneDrive, Box sync clients) present challenges:

1. **Delayed events**: Cloud sync introduces latency; increase stable_duration
2. **Partial uploads**: Files may appear before fully synced; use size stability
3. **Temporary files**: Sync clients create `.tmp` or `.partial` files; filter by extension

```python
def is_temp_file(path: Path) -> bool:
    """Detect temporary sync files."""
    temp_suffixes = {'.tmp', '.partial', '.crdownload', '.!ut'}
    temp_prefixes = {'~', '.~'}

    return (
        path.suffix in temp_suffixes or
        any(path.name.startswith(prefix) for prefix in temp_prefixes)
    )
```

#### Reliability Patterns

1. **Graceful degradation**: If watchfiles fails, fall back to polling
   ```python
   try:
       for changes in watch(watch_dir):
           process(changes)
   except Exception as e:
       logger.error(f"Watchfiles failed: {e}, falling back to polling")
       poll_directory(watch_dir)
   ```

2. **Restart on error**: watchfiles can raise on directory deletion/unmount
   ```python
   while True:
       try:
           for changes in watch(watch_dir):
               process(changes)
       except Exception as e:
           logger.error(f"Watcher error: {e}, restarting in 10s")
           time.sleep(10)
   ```

3. **Filter unwanted events**: Reduce noise by filtering hidden files, system files
   ```python
   for changes in watch(watch_dir):
       for change_type, file_path in changes:
           if file_path.name.startswith('.') or file_path.name == 'Thumbs.db':
               continue  # Skip
           process_change(change_type, file_path)
   ```

#### Gotchas

1. **Event order**: File system events are not guaranteed to be ordered; handle out-of-order events
2. **Duplicate events**: Same file may trigger multiple `modified` events; deduplicate
3. **Directory moves**: Moving directory may trigger `deleted` + `added`; track by inode (not supported by watchfiles API)
4. **Recursive watching**: watchfiles watches recursively by default; use `watch_filter` to exclude subdirectories
5. **Large directories**: Initial scan on startup can take time for 100k+ files; show progress indicator

### References

- **watchfiles GitHub**: https://github.com/samuelcolvin/watchfiles
- **watchfiles PyPI**: https://pypi.org/project/watchfiles/
- **Migration from watchgod**: https://watchfiles.helpmanual.io/migrating/
- **Rust notify library**: https://github.com/notify-rs/notify (underlying implementation)
- **watchdog (alternative)**: https://github.com/gorakhargosh/watchdog
- **watchdog vs watchfiles comparison**: https://piptrends.com/compare/watchdog-vs-watchfiles
- **FileLock library**: https://py-filelock.readthedocs.io/ (for file locking strategy)

---

## 6. DANDI Upload Best Practices

### Decision

**Use DANDI Python SDK (dandi-cli)** with custom retry logic via **tenacity**, implementing chunked resumable uploads with exponential backoff, checksum verification, and structured error logging.

### Rationale

1. **Official SDK**: Maintained by DANDI team, guaranteed API compatibility
2. **Resumable Uploads**: SDK supports resuming interrupted uploads via multipart S3 uploads
3. **Validation**: Built-in NWB validation before upload prevents invalid files
4. **Metadata Management**: Handles dandiset.yaml generation and validation
5. **Community Standard**: Widely adopted by neuroscience labs uploading to DANDI Archive

### Alternatives Considered

1. **DANDI CLI (command-line tool)**
   - **Rejected for automation**: CLI requires shell invocation; SDK provides programmatic control
   - **Keep for testing**: CLI useful for manual uploads and debugging

2. **Direct S3 API**
   - **Rejected**: DANDI uses custom authentication and metadata; SDK abstracts complexity
   - Lower-level control not needed

3. **Custom multipart upload**
   - **Rejected**: Reinventing SDK functionality increases maintenance burden
   - DANDI SDK already implements best practices

### Implementation Notes

#### DANDI SDK Architecture

DANDI uses a two-stage upload process:
1. **Register asset**: POST metadata to DANDI Archive, receive upload URLs
2. **Upload to S3**: Multipart upload to S3 bucket, finalize asset

SDK handles this flow via `RemoteDandiset.upload()`.

#### Basic Upload Pattern

```python
from dandi.dandiapi import DandiAPIClient
from pathlib import Path

# Authenticate
client = DandiAPIClient()
client.authenticate()  # Uses DANDI_API_KEY environment variable

# Get dandiset
dandiset = client.get_dandiset('000001', version='draft')

# Upload NWB file
nwb_path = Path('subject_001_20250115.nwb')
asset = dandiset.upload(
    paths=[nwb_path],
    metadata={
        'schemaVersion': '0.6.0',
        'name': 'Fiber photometry in VTA during reward task',
        # ... additional metadata
    },
    jobs=4  # Concurrent upload threads
)
```

#### Chunking Strategy

DANDI SDK uses **multipart S3 uploads** with configurable chunk size:

- **Default chunk size**: 64 MiB (optimized for S3)
- **Minimum chunk size**: 5 MiB (S3 requirement)
- **Maximum parts**: 10,000 (S3 limit)

**Recommended configuration** for large NWB files (>10 GB):

```python
# Calculate optimal chunk size
file_size = nwb_path.stat().st_size
chunk_size = max(64 * 1024 * 1024, file_size // 5000)  # Stay under 10k parts

# SDK handles chunking internally via boto3
```

**SDK implementation detail** (from source inspection):
- Uses `boto3` for S3 multipart uploads
- Chunks are uploaded concurrently with thread pool
- Failed chunks are retried automatically by boto3

#### Retry Logic with Tenacity

DANDI SDK has basic retries, but wrap critical operations with `tenacity` for robustness:

```python
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)
import logging
from requests.exceptions import RequestException, Timeout
from dandi.exceptions import UploadError

logger = logging.getLogger(__name__)

@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=2, min=4, max=120),
    retry=retry_if_exception_type((RequestException, Timeout, UploadError)),
    before_sleep=before_sleep_log(logger, logging.WARNING)
)
def upload_with_retry(dandiset, nwb_path, metadata):
    """Upload with exponential backoff retry."""
    return dandiset.upload(paths=[nwb_path], metadata=metadata)
```

**Retry strategy breakdown**:
- **Max attempts**: 5 retries (6 total attempts)
- **Backoff**: 4s, 8s, 16s, 32s, 64s (capped at 120s)
- **Retry conditions**: Network errors, timeouts, upload errors
- **Logging**: Log warning before each retry with attempt number

#### Rate Limiting

DANDI Archive has rate limits to prevent abuse:

- **Documented limits**: Not publicly specified (subject to change)
- **429 responses**: Server returns `Retry-After` header
- **Best practice**: Respect `Retry-After`, implement adaptive backoff

**Handle 429 with tenacity**:

```python
from requests.exceptions import HTTPError

def is_rate_limited(exception):
    """Check if exception is 429 rate limit."""
    if isinstance(exception, HTTPError):
        return exception.response.status_code == 429
    return False

@retry(
    stop=stop_after_attempt(10),
    wait=wait_exponential(multiplier=2, min=10, max=300),
    retry=retry_if_exception(is_rate_limited),
    before_sleep=before_sleep_log(logger, logging.WARNING)
)
def upload_with_rate_limit_handling(dandiset, nwb_path, metadata):
    try:
        return dandiset.upload(paths=[nwb_path], metadata=metadata)
    except HTTPError as e:
        if e.response.status_code == 429:
            retry_after = int(e.response.headers.get('Retry-After', 60))
            logger.warning(f"Rate limited, waiting {retry_after}s")
            time.sleep(retry_after)
        raise
```

#### Checksum Verification

DANDI SDK computes and verifies checksums automatically:

1. **Pre-upload**: Compute SHA256 digest of NWB file
2. **Metadata**: Include digest in asset metadata
3. **Post-upload**: DANDI Archive verifies digest on S3 object
4. **Validation**: Upload fails if checksums mismatch

**Explicit checksum calculation** (for provenance logging):

```python
import hashlib

def compute_sha256(file_path: Path) -> str:
    """Compute SHA256 checksum."""
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    return sha256.hexdigest()

checksum = compute_sha256(nwb_path)
logger.info(f"NWB file checksum: {checksum}")
# Store checksum in ELN for audit trail
```

#### Error Handling Patterns

Classify errors for appropriate recovery:

```python
from dandi.exceptions import UploadError, ValidationError

try:
    asset = upload_with_retry(dandiset, nwb_path, metadata)
except ValidationError as e:
    # NWB file invalid, do not retry
    logger.error(f"NWB validation failed: {e}")
    # Log to ELN, mark session as "validation failed"
    raise
except UploadError as e:
    # Transient upload error, already retried
    logger.error(f"Upload failed after retries: {e}")
    # Enqueue for manual review
    raise
except Exception as e:
    # Unexpected error
    logger.exception(f"Unexpected error during upload: {e}")
    raise
```

#### Resumable Upload Implementation

DANDI SDK resumes uploads automatically if interrupted:

1. **Track upload state**: SDK stores multipart upload IDs in temporary files
2. **Resume on restart**: If process crashes, re-running upload resumes from last completed chunk
3. **Timeout handling**: Set long timeout for large files (adjust boto3 config)

**Force resume behavior**:

```python
# SDK automatically resumes; no explicit resume API
# If upload crashes, simply re-run:
asset = dandiset.upload(paths=[nwb_path], metadata=metadata)
# SDK detects in-progress multipart upload and resumes
```

**Note**: Resumption is transparent; SDK checks for existing multipart upload ID in cache.

#### Metadata Validation

Validate dandiset metadata before upload:

```python
from dandi.metadata import validate_dandiset_yaml

metadata_path = Path('dandiset.yaml')
errors = validate_dandiset_yaml(metadata_path)
if errors:
    logger.error(f"Metadata validation failed: {errors}")
    raise ValueError(f"Invalid dandiset.yaml: {errors}")
```

**Key metadata fields**:
- `schemaVersion`: "0.6.0" (current DANDI schema version)
- `name`: Dandiset title
- `description`: Detailed description
- `contributor`: List of contributors with roles
- `license`: e.g., "spdx:CC-BY-4.0"
- `assetsSummary`: Auto-generated by SDK

#### Performance Optimization

1. **Concurrent uploads**: Use `jobs` parameter for multiple files
   ```python
   dandiset.upload(paths=nwb_files, metadata=metadata, jobs=4)
   ```

2. **Async upload**: Run uploads in background with asyncio
   ```python
   import asyncio

   async def upload_async(dandiset, nwb_path, metadata):
       loop = asyncio.get_event_loop()
       return await loop.run_in_executor(
           None, dandiset.upload, [nwb_path], metadata
       )
   ```

3. **Skip existing assets**: Check if asset already uploaded
   ```python
   existing_assets = {asset.path for asset in dandiset.get_assets()}
   if nwb_path.name in existing_assets:
       logger.info(f"Asset {nwb_path.name} already uploaded, skipping")
       return
   ```

#### Provenance Logging

Record upload provenance in ELN:

```python
provenance = {
    'dandi_asset_id': asset.identifier,
    'dandi_asset_url': f'https://dandiarchive.org/dandiset/{dandiset.identifier}/draft/files/{asset.identifier}',
    'upload_timestamp': datetime.utcnow().isoformat(),
    'nwb_checksum': checksum,
    'dandi_schema_version': metadata['schemaVersion'],
    'pipeline_version': git_commit_sha
}

# Append to ELN entry
eln_adapter.append_note(entry_id, f"DANDI upload complete: {provenance}")
```

#### Gotchas

1. **Authentication**: Set `DANDI_API_KEY` environment variable (get from https://dandiarchive.org/)
2. **Draft vs published**: Always upload to `draft` version; publish separately via web UI
3. **Large file timeout**: Set boto3 timeout for files >10 GB:
   ```python
   import boto3
   from botocore.config import Config

   boto3_config = Config(read_timeout=600)  # 10 minutes
   ```
4. **NWB validation overhead**: Validation reads entire file; can be slow for large files
5. **Concurrency limit**: Don't exceed 10 concurrent uploads to avoid rate limiting
6. **Multipart upload cleanup**: Failed uploads leave partial data on S3; SDK cleans up automatically after 7 days

### References

- **DANDI CLI GitHub**: https://github.com/dandi/dandi-cli
- **DANDI CLI Documentation**: https://dandi.readthedocs.io/
- **DANDI Upload Command**: https://dandi.readthedocs.io/en/latest/cmdline/upload.html
- **DANDI API Client**: https://dandi.readthedocs.io/en/latest/modref/dandiapi.html
- **DANDI Archive**: https://dandiarchive.org/
- **DANDI Schema**: https://github.com/dandi/dandi-schema
- **tenacity library**: https://tenacity.readthedocs.io/
- **boto3 multipart upload**: https://boto3.amazonaws.com/v1/documentation/api/latest/guide/s3-uploading-files.html

---

## 7. Celery Architecture for Scientific Pipelines

### Decision

**Use Celery with Redis as broker** and result backend, implementing task idempotency via composite keys (subject+session), exponential backoff retries with `tenacity`, and dead-letter queue pattern for terminal failures.

### Rationale

1. **Mature Framework**: Celery is battle-tested for distributed task queues in Python
2. **Redis Performance**: Redis is faster than RabbitMQ for our use case (fewer features, higher throughput)
3. **Idempotency Support**: Task IDs can be customized to prevent duplicate processing
4. **Retry Flexibility**: Configurable retry policies with exponential backoff
5. **Monitoring**: Flower and other tools provide visibility into queue state

### Alternatives Considered

1. **RabbitMQ as broker**
   - **Rejected**: More complex setup, lower throughput than Redis
   - **When to reconsider**: If strict message delivery guarantees required (AMQP transactions)
   - Redis is sufficient for our reliability requirements

2. **Celery with SQS broker**
   - **Rejected**: Higher latency (AWS API overhead), potential costs
   - **When to reconsider**: If deploying on AWS with existing SQS infrastructure

3. **Pure asyncio (no Celery)**
   - **Rejected**: Requires custom queue, retry, and monitoring implementation
   - Celery provides these out-of-the-box

4. **Dramatiq**
   - **Rejected**: Smaller community, fewer integrations than Celery
   - Similar feature set but less mature

5. **Prefect/Airflow**
   - **Rejected**: Designed for DAGs and workflow orchestration, not real-time task queues
   - Overkill for our simple sequential pipeline (ELN → package → upload)

### Implementation Notes

#### Basic Celery Setup

```python
# app/celery_app.py
from celery import Celery

app = Celery(
    'eln_to_dandi',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/1',  # Separate DB for results
)

app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,  # Track when task starts execution
    task_time_limit=3600,      # Hard time limit: 1 hour
    task_soft_time_limit=3300, # Soft time limit: 55 minutes
)
```

**Start worker**:
```bash
pixi run celery -A app.celery_app worker --loglevel=info
```

#### Task Idempotency with Composite Keys

Prevent duplicate processing of same session:

```python
from celery import Task
import hashlib

def generate_task_id(subject_id: str, session_date: str, task_name: str) -> str:
    """Generate deterministic task ID from subject+session."""
    key = f"{task_name}:{subject_id}:{session_date}"
    return hashlib.sha256(key.encode()).hexdigest()

@app.task(bind=True, name='package_nwb')
def package_nwb(self: Task, subject_id: str, session_date: str, data_path: str):
    """Package NWB file for subject+session."""
    # Task ID already set via apply_async
    logger.info(f"Packaging {subject_id} session {session_date}")
    # ... packaging logic ...
    return nwb_filepath

# Invoke with custom task ID
task_id = generate_task_id(subject_id, session_date, 'package_nwb')
task = package_nwb.apply_async(
    args=[subject_id, session_date, data_path],
    task_id=task_id
)

# Second invocation with same task_id will be rejected (idempotent)
# Celery returns existing task result
```

**Check if task already exists**:

```python
from celery.result import AsyncResult

task_id = generate_task_id(subject_id, session_date, 'package_nwb')
result = AsyncResult(task_id, app=app)

if result.state == 'PENDING':
    # Task not started, safe to enqueue
    task = package_nwb.apply_async(args=[...], task_id=task_id)
elif result.state in ['SUCCESS', 'FAILURE']:
    # Task completed (success or failure)
    logger.info(f"Task {task_id} already completed: {result.state}")
else:
    # Task in progress (STARTED, RETRY)
    logger.info(f"Task {task_id} already running: {result.state}")
```

#### Retry Strategy with Exponential Backoff

Celery built-in retries:

```python
@app.task(
    bind=True,
    name='upload_to_dandi',
    autoretry_for=(RequestException, Timeout),
    retry_kwargs={'max_retries': 5},
    retry_backoff=True,       # Enable exponential backoff
    retry_backoff_max=600,    # Max 10 minutes
    retry_jitter=True         # Add jitter to prevent thundering herd
)
def upload_to_dandi(self: Task, nwb_filepath: str, dandiset_id: str):
    """Upload NWB to DANDI with automatic retries."""
    # ... upload logic ...
    return dandi_asset_id
```

**Manual retry control**:

```python
@app.task(bind=True, name='package_nwb')
def package_nwb(self: Task, subject_id: str, session_date: str, data_path: str):
    try:
        # ... packaging logic ...
        return nwb_filepath
    except TransientError as e:
        # Retry with exponential backoff
        countdown = 2 ** self.request.retries  # 2, 4, 8, 16, ...
        raise self.retry(exc=e, countdown=countdown, max_retries=5)
    except TerminalError as e:
        # Do not retry, send to dead-letter queue
        send_to_dlq(self.request.id, e)
        raise
```

#### Dead-Letter Queue Pattern

Handle terminal failures:

```python
# Define dead-letter queue
DLQ_QUEUE = 'dead_letter_queue'

def send_to_dlq(task_id: str, exception: Exception):
    """Send failed task to dead-letter queue for manual review."""
    dlq_task = {
        'task_id': task_id,
        'timestamp': datetime.utcnow().isoformat(),
        'exception': str(exception),
        'traceback': traceback.format_exc(),
    }

    # Store in Redis list
    redis_client = redis.StrictRedis.from_url('redis://localhost:6379/2')
    redis_client.lpush(DLQ_QUEUE, json.dumps(dlq_task))

    # Alert via logging/email/Slack
    logger.error(f"Task {task_id} sent to DLQ: {exception}")

# Task-level error callback
@app.task(
    bind=True,
    on_failure=send_to_dlq_callback
)
def risky_task(self: Task, ...):
    # ... task logic ...
    pass

def send_to_dlq_callback(self, exc, task_id, args, kwargs, einfo):
    """Callback invoked on task failure."""
    send_to_dlq(task_id, exc)
```

**Monitor and retry DLQ tasks**:

```python
def process_dlq():
    """Manual intervention: review and retry failed tasks."""
    redis_client = redis.StrictRedis.from_url('redis://localhost:6379/2')

    while True:
        dlq_item = redis_client.rpop(DLQ_QUEUE)
        if not dlq_item:
            break

        task_data = json.loads(dlq_item)
        task_id = task_data['task_id']

        # Review exception, decide if retriable
        if should_retry(task_data):
            # Re-enqueue original task
            retry_task(task_id)
        else:
            # Log for permanent failure
            logger.error(f"Task {task_id} permanently failed")
```

#### Redis vs RabbitMQ Trade-offs

| Feature | Redis | RabbitMQ |
|---------|-------|----------|
| **Performance** | Higher throughput (10k+ msg/s) | Moderate (5k msg/s) |
| **Persistence** | Optional (AOF/RDB) | Built-in (durable queues) |
| **Message Delivery** | At-most-once (fire-and-forget) | At-least-once (ACK-based) |
| **Complexity** | Simpler setup | More configuration |
| **Reliability** | Good (with AOF persistence) | Excellent (AMQP guarantees) |
| **Use Case** | Fast, ephemeral tasks | Mission-critical workflows |

**Decision rationale for Redis**:
- Our tasks are idempotent (safe to retry)
- Redis persistence (AOF) provides sufficient reliability
- Higher throughput supports busy labs with many sessions
- Simpler operations (fewer moving parts)

**When to switch to RabbitMQ**:
- If message loss is unacceptable (even with Redis AOF)
- If need complex routing (exchanges, bindings)
- If integrating with non-Python services (AMQP is language-agnostic)

#### Result Backend Considerations

Celery stores task results in backend:

- **Redis**: Fast, ephemeral results (TTL-based expiration)
- **Database** (PostgreSQL): Persistent results, queryable via SQL
- **No backend**: Use for fire-and-forget tasks (lower overhead)

**Recommendation**: Use Redis backend with TTL:

```python
app.conf.update(
    result_backend='redis://localhost:6379/1',
    result_expires=86400,  # Results expire after 24 hours
)
```

**Why not database backend**:
- Redis is faster for transient results
- We log final state to ELN (permanent record)
- Database adds complexity (migrations, schema management)

#### Task Routing and Prioritization

Route different task types to separate queues:

```python
app.conf.task_routes = {
    'package_nwb': {'queue': 'packaging'},
    'upload_to_dandi': {'queue': 'upload'},
    'sync_eln': {'queue': 'sync'},
}

# Start workers for specific queues
# Worker 1: packaging (CPU-intensive)
# celery -A app.celery_app worker -Q packaging --concurrency=4

# Worker 2: upload (I/O-intensive)
# celery -A app.celery_app worker -Q upload --concurrency=10
```

**Priority queues** (Celery 4.x+):

```python
task = package_nwb.apply_async(
    args=[subject_id, session_date, data_path],
    priority=9  # 0-9, higher is more urgent
)
```

#### Monitoring with Flower

```bash
pixi add flower
pixi run celery -A app.celery_app flower
# Access at http://localhost:5555
```

**Flower features**:
- Real-time task monitoring
- Worker management (restart, shutdown)
- Task filtering and search
- Metrics (throughput, latency)

#### Scientific Pipeline-Specific Patterns

1. **Long-running tasks**: Set high time limits for NWB packaging
   ```python
   @app.task(time_limit=7200)  # 2 hours
   def package_large_nwb(...):
       pass
   ```

2. **Task chaining**: Sequential pipeline (ELN → package → upload)
   ```python
   from celery import chain

   workflow = chain(
       sync_eln.s(project_id),
       package_nwb.s(subject_id, session_date),
       upload_to_dandi.s(dandiset_id)
   )
   result = workflow.apply_async()
   ```

3. **Progress tracking**: Update ELN during long tasks
   ```python
   @app.task(bind=True)
   def package_nwb(self: Task, subject_id: str, ...):
       # Update progress
       self.update_state(state='PROGRESS', meta={'step': 'Extracting TDT tank'})
       extract_tdt(...)

       self.update_state(state='PROGRESS', meta={'step': 'Calculating dFF'})
       compute_dff(...)

       # ... continue ...
   ```

4. **Resource limits**: Prevent worker overload
   ```python
   # Limit concurrent packaging tasks (CPU-bound)
   @app.task(rate_limit='2/m')  # Max 2 per minute
   def package_nwb(...):
       pass
   ```

#### Gotchas

1. **Task serialization**: Only JSON-serializable arguments allowed; don't pass complex objects
2. **Import order**: Import tasks after creating Celery app to avoid circular imports
3. **acks_late**: Use `task_acks_late=True` for idempotent tasks to survive worker crashes
   ```python
   app.conf.task_acks_late = True
   ```
4. **Visibility timeout** (Redis): Task is redelivered if worker crashes; set < task time limit
5. **Pickle security**: Never use pickle serializer (`task_serializer='pickle'`) in production (security risk)

### References

- **Celery Documentation**: https://docs.celeryq.dev/en/stable/
- **Celery Tasks Guide**: https://docs.celeryq.dev/en/stable/userguide/tasks.html
- **Celery FAQ**: https://docs.celeryq.dev/en/stable/faq.html
- **Celery Retries Deep Dive**: https://blog.gitguardian.com/celery-tasks-retries-errors/
- **Dead-Letter Queue Tutorial**: https://medium.com/@hengfeng/how-to-create-a-dead-letter-queue-in-celery-rabbitmq-401b17c72cd3
- **Redis as Celery Broker**: https://docs.celeryq.dev/en/stable/getting-started/backends-and-brokers/redis.html
- **RabbitMQ Comparison**: https://medium.com/ca/asynchronous-distributed-task-execution-via-python-celery-using-redis-and-rabbitmq-855a282f9e
- **Flower Monitoring**: https://flower.readthedocs.io/

---

## 8. Multi-Storage Backend Patterns

### Decision

**Implement adapter pattern** with storage backends for local filesystem (async via `aiofiles`), OneDrive (Microsoft Graph API), and Box (Box Python SDK), using OAuth2 for cloud authentication and async operations for I/O-bound tasks.

### Rationale

1. **Adapter Pattern**: Decouples storage logic from business logic; easy to add new backends
2. **Protocol-based Design**: Python Protocol (PEP 544) ensures type safety and consistent API
3. **Async I/O**: `aiofiles` enables non-blocking file operations for better concurrency
4. **Official SDKs**: Use Microsoft Graph and Box SDKs for reliability and OAuth2 support
5. **OAuth2 Standard**: Industry-standard authentication for delegated access to cloud storage

### Alternatives Considered

1. **boto3 for S3-compatible storage**
   - **Rejected for now**: OneDrive and Box are not S3-compatible
   - **Keep as option**: Add S3 backend later if needed (e.g., MinIO, AWS S3)

2. **WebDAV protocol**
   - **Rejected**: OneDrive supports WebDAV but Graph API is more feature-rich
   - WebDAV has limited metadata support

3. **Sync clients (OneDrive sync, Box Drive)**
   - **Rejected**: Requires desktop apps, not suitable for server deployment
   - No programmatic control over sync state

4. **Direct REST API calls**
   - **Rejected**: SDKs provide error handling, retries, and pagination
   - Reinventing SDK functionality

### Implementation Notes

#### Adapter Interface (Protocol)

```python
from typing import Protocol, List
from pathlib import Path

class StorageAdapter(Protocol):
    """Storage backend interface."""

    async def ensure_structure(self, manifest: dict) -> None:
        """Create directory structure from manifest."""
        ...

    async def put(self, src: Path, dst: Path) -> None:
        """Upload file from src (local) to dst (remote)."""
        ...

    async def get(self, src: Path, dst: Path) -> None:
        """Download file from src (remote) to dst (local)."""
        ...

    async def exists(self, path: Path) -> bool:
        """Check if path exists."""
        ...

    async def list(self, path: Path) -> List[Path]:
        """List contents of directory."""
        ...

    async def delete(self, path: Path) -> None:
        """Delete file or directory."""
        ...
```

#### Local Storage Adapter (with aiofiles)

```python
import aiofiles
import aiofiles.os
from pathlib import Path
from typing import List

class LocalStorageAdapter:
    """Local filesystem storage with async operations."""

    def __init__(self, base_path: Path):
        self.base_path = base_path

    async def ensure_structure(self, manifest: dict) -> None:
        """Create directory tree."""
        for dir_path in manifest.get('directories', []):
            full_path = self.base_path / dir_path
            await aiofiles.os.makedirs(full_path, exist_ok=True)

    async def put(self, src: Path, dst: Path) -> None:
        """Copy file asynchronously."""
        dst_full = self.base_path / dst
        await aiofiles.os.makedirs(dst_full.parent, exist_ok=True)

        async with aiofiles.open(src, 'rb') as src_file:
            async with aiofiles.open(dst_full, 'wb') as dst_file:
                while chunk := await src_file.read(8192):
                    await dst_file.write(chunk)

    async def get(self, src: Path, dst: Path) -> None:
        """Copy from storage to local path."""
        src_full = self.base_path / src
        await self.put(src_full, dst)  # Same operation locally

    async def exists(self, path: Path) -> bool:
        """Check if path exists."""
        full_path = self.base_path / path
        return await aiofiles.os.path.exists(full_path)

    async def list(self, path: Path) -> List[Path]:
        """List directory contents."""
        full_path = self.base_path / path
        entries = await aiofiles.os.listdir(full_path)
        return [Path(entry) for entry in entries]

    async def delete(self, path: Path) -> None:
        """Delete file or directory."""
        full_path = self.base_path / path
        if await aiofiles.os.path.isdir(full_path):
            await aiofiles.os.rmdir(full_path)
        else:
            await aiofiles.os.remove(full_path)
```

**Why aiofiles**:
- Non-blocking file I/O (threads under the hood)
- Compatible with asyncio event loop
- Simple drop-in replacement for built-in `open()`

**Limitations**:
- Still uses thread pool (file I/O is always blocking at OS level)
- Minimal performance gain for small files
- Most beneficial for many concurrent file operations

#### OneDrive Storage Adapter (Microsoft Graph API)

```python
from msgraph.core import GraphClient
from azure.identity import ClientSecretCredential
from pathlib import Path
import aiohttp

class OneDriveStorageAdapter:
    """OneDrive storage via Microsoft Graph API."""

    def __init__(self, tenant_id: str, client_id: str, client_secret: str, drive_id: str):
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.drive_id = drive_id
        self.client = None

    async def _get_client(self) -> GraphClient:
        """Initialize Graph API client with OAuth2."""
        if not self.client:
            credential = ClientSecretCredential(
                tenant_id=self.tenant_id,
                client_id=self.client_id,
                client_secret=self.client_secret
            )
            self.client = GraphClient(credential=credential)
        return self.client

    async def ensure_structure(self, manifest: dict) -> None:
        """Create folder structure in OneDrive."""
        client = await self._get_client()

        for dir_path in manifest.get('directories', []):
            # Create folder via Graph API
            folder_data = {'name': dir_path, 'folder': {}}
            await client.post(
                f'/drives/{self.drive_id}/root/children',
                json=folder_data
            )

    async def put(self, src: Path, dst: Path) -> None:
        """Upload file to OneDrive."""
        client = await self._get_client()

        # For files <4MB, use simple upload
        file_size = src.stat().st_size
        if file_size < 4 * 1024 * 1024:
            async with aiofiles.open(src, 'rb') as f:
                content = await f.read()

            await client.put(
                f'/drives/{self.drive_id}/root:/{dst}:/content',
                data=content
            )
        else:
            # For large files, use resumable upload session
            await self._upload_large_file(src, dst)

    async def _upload_large_file(self, src: Path, dst: Path) -> None:
        """Resumable upload for files >4MB."""
        client = await self._get_client()

        # Create upload session
        session_data = {
            'item': {'@microsoft.graph.conflictBehavior': 'replace'}
        }
        response = await client.post(
            f'/drives/{self.drive_id}/root:/{dst}:/createUploadSession',
            json=session_data
        )
        upload_url = response.json()['uploadUrl']

        # Upload in 10MB chunks
        chunk_size = 10 * 1024 * 1024
        file_size = src.stat().st_size

        async with aiofiles.open(src, 'rb') as f:
            for chunk_start in range(0, file_size, chunk_size):
                chunk_end = min(chunk_start + chunk_size, file_size)
                chunk = await f.read(chunk_size)

                headers = {
                    'Content-Length': str(len(chunk)),
                    'Content-Range': f'bytes {chunk_start}-{chunk_end-1}/{file_size}'
                }

                async with aiohttp.ClientSession() as session:
                    await session.put(upload_url, data=chunk, headers=headers)

    async def get(self, src: Path, dst: Path) -> None:
        """Download file from OneDrive."""
        client = await self._get_client()

        # Get download URL
        response = await client.get(
            f'/drives/{self.drive_id}/root:/{src}:/content'
        )

        # Stream download
        async with aiohttp.ClientSession() as session:
            async with session.get(response.url) as download_response:
                async with aiofiles.open(dst, 'wb') as f:
                    async for chunk in download_response.content.iter_chunked(8192):
                        await f.write(chunk)

    async def exists(self, path: Path) -> bool:
        """Check if item exists."""
        client = await self._get_client()
        try:
            await client.get(f'/drives/{self.drive_id}/root:/{path}')
            return True
        except Exception:
            return False

    async def list(self, path: Path) -> List[Path]:
        """List folder contents."""
        client = await self._get_client()
        response = await client.get(
            f'/drives/{self.drive_id}/root:/{path}:/children'
        )
        items = response.json()['value']
        return [Path(item['name']) for item in items]
```

**OAuth2 Authentication Flow**:

1. **App Registration** (Azure Portal):
   - Register app in Azure AD
   - Grant permissions: `Files.ReadWrite.All`
   - Generate client secret

2. **Authentication Methods**:
   - **Client Credentials** (app-only): Used above for service account
   - **Device Flow**: For interactive authentication
   - **Authorization Code Flow**: For user delegation (web app)

**Key Considerations**:
- **Upload limits**: 4MB simple upload, 60MB REST API limit, resumable for larger
- **Rate limits**: 10,000 requests per 10 minutes per app
- **Path encoding**: Use `:/{path}:` syntax for special characters
- **Conflict behavior**: Set `@microsoft.graph.conflictBehavior` to `replace` or `fail`

#### Box Storage Adapter (Box Python SDK)

```python
from boxsdk import Client, OAuth2
from boxsdk.object.folder import Folder
from pathlib import Path
from typing import List
import aiofiles

class BoxStorageAdapter:
    """Box storage via Box Python SDK."""

    def __init__(self, client_id: str, client_secret: str, access_token: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = access_token
        self.client = None

    async def _get_client(self) -> Client:
        """Initialize Box client with OAuth2."""
        if not self.client:
            oauth2 = OAuth2(
                client_id=self.client_id,
                client_secret=self.client_secret,
                access_token=self.access_token
            )
            self.client = Client(oauth2)
        return self.client

    async def ensure_structure(self, manifest: dict) -> None:
        """Create folder structure in Box."""
        client = await self._get_client()
        root_folder = client.folder(folder_id='0')  # Root folder

        for dir_path in manifest.get('directories', []):
            parts = Path(dir_path).parts
            current_folder = root_folder

            for part in parts:
                # Check if subfolder exists
                items = current_folder.get_items()
                existing = next((item for item in items if item.name == part), None)

                if existing:
                    current_folder = client.folder(folder_id=existing.id)
                else:
                    new_folder = current_folder.create_subfolder(part)
                    current_folder = new_folder

    async def put(self, src: Path, dst: Path) -> None:
        """Upload file to Box."""
        client = await self._get_client()

        # Get parent folder
        parent_folder_id = await self._get_folder_id(dst.parent)
        folder = client.folder(folder_id=parent_folder_id)

        # Upload file (Box SDK handles chunking for large files)
        folder.upload(str(src), file_name=dst.name)

    async def _get_folder_id(self, path: Path) -> str:
        """Get Box folder ID from path."""
        client = await self._get_client()

        if path == Path('.'):
            return '0'  # Root folder

        parts = path.parts
        current_id = '0'

        for part in parts:
            folder = client.folder(folder_id=current_id)
            items = folder.get_items()
            next_folder = next((item for item in items if item.name == part), None)

            if not next_folder:
                raise FileNotFoundError(f"Folder {path} not found")

            current_id = next_folder.id

        return current_id

    async def get(self, src: Path, dst: Path) -> None:
        """Download file from Box."""
        client = await self._get_client()

        # Find file ID
        file_id = await self._get_file_id(src)
        file_obj = client.file(file_id=file_id)

        # Download to local path
        async with aiofiles.open(dst, 'wb') as f:
            await f.write(file_obj.content())

    async def _get_file_id(self, path: Path) -> str:
        """Get Box file ID from path."""
        folder_id = await self._get_folder_id(path.parent)
        folder = self.client.folder(folder_id=folder_id)

        items = folder.get_items()
        file_obj = next((item for item in items if item.name == path.name), None)

        if not file_obj:
            raise FileNotFoundError(f"File {path} not found")

        return file_obj.id

    async def exists(self, path: Path) -> bool:
        """Check if item exists."""
        try:
            if path.suffix:  # File
                await self._get_file_id(path)
            else:  # Folder
                await self._get_folder_id(path)
            return True
        except FileNotFoundError:
            return False

    async def list(self, path: Path) -> List[Path]:
        """List folder contents."""
        folder_id = await self._get_folder_id(path)
        folder = self.client.folder(folder_id=folder_id)

        items = folder.get_items()
        return [Path(item.name) for item in items]
```

**OAuth2 Authentication Flow** (Box):

1. **App Registration** (Box Developer Console):
   - Create app, choose "Server Authentication (OAuth 2.0)"
   - Grant scopes: `root_readwrite`
   - Generate client ID and secret

2. **Token Management**:
   - **Access token**: Short-lived (60 minutes)
   - **Refresh token**: Use to obtain new access token
   ```python
   oauth2 = OAuth2(
       client_id=CLIENT_ID,
       client_secret=CLIENT_SECRET,
       access_token=ACCESS_TOKEN,
       refresh_token=REFRESH_TOKEN
   )
   oauth2.refresh(None)  # Refresh access token
   ```

**Key Considerations**:
- **Chunked upload**: Box SDK handles automatically for files >20MB
- **Concurrency**: Box API allows 10 concurrent requests per user
- **Rate limits**: 10 API calls per second per user
- **Webhooks**: Box supports webhooks for change notifications (future enhancement)

#### Adapter Pattern Usage

```python
# Dependency injection
class DataSyncService:
    def __init__(self, storage: StorageAdapter):
        self.storage = storage

    async def sync_session(self, session_data: dict):
        """Sync session data to storage."""
        manifest = generate_manifest(session_data)
        await self.storage.ensure_structure(manifest)

        for file_info in session_data['files']:
            await self.storage.put(
                src=Path(file_info['local_path']),
                dst=Path(file_info['remote_path'])
            )

# Instantiate with specific backend
if storage_type == 'local':
    storage = LocalStorageAdapter(base_path=Path('/data'))
elif storage_type == 'onedrive':
    storage = OneDriveStorageAdapter(
        tenant_id=os.environ['AZURE_TENANT_ID'],
        client_id=os.environ['AZURE_CLIENT_ID'],
        client_secret=os.environ['AZURE_CLIENT_SECRET'],
        drive_id=os.environ['ONEDRIVE_DRIVE_ID']
    )
elif storage_type == 'box':
    storage = BoxStorageAdapter(
        client_id=os.environ['BOX_CLIENT_ID'],
        client_secret=os.environ['BOX_CLIENT_SECRET'],
        access_token=os.environ['BOX_ACCESS_TOKEN']
    )

sync_service = DataSyncService(storage=storage)
await sync_service.sync_session(session_data)
```

#### Testing Strategy

Use protocol-based mocks for testing:

```python
class MockStorageAdapter:
    """In-memory storage for testing."""

    def __init__(self):
        self.files = {}  # path -> content

    async def put(self, src: Path, dst: Path) -> None:
        async with aiofiles.open(src, 'rb') as f:
            self.files[str(dst)] = await f.read()

    async def get(self, src: Path, dst: Path) -> None:
        content = self.files[str(src)]
        async with aiofiles.open(dst, 'wb') as f:
            await f.write(content)

    # ... implement other methods ...

# Test with mock
async def test_sync_session():
    mock_storage = MockStorageAdapter()
    service = DataSyncService(storage=mock_storage)
    await service.sync_session(test_data)

    assert 'subject_001/session_20250115/data.nwb' in mock_storage.files
```

#### Gotchas

1. **aiofiles limitation**: Still uses thread pool internally (no true async file I/O in Python)
2. **OAuth2 token expiry**: Implement token refresh logic; handle 401 responses
3. **Path separators**: OneDrive/Box use `/`, Windows uses `\`; use `Path` for normalization
4. **Cloud API rate limits**: Implement exponential backoff with `tenacity`
5. **Large file uploads**: OneDrive/Box have different thresholds for resumable uploads
6. **Concurrent uploads**: Limit concurrency to respect API rate limits (use `asyncio.Semaphore`)

### References

- **aiofiles GitHub**: https://github.com/Tinche/aiofiles
- **aiofiles PyPI**: https://pypi.org/project/aiofiles/
- **aiofiles Tutorial**: https://krython.com/tutorial/python/aiofiles-async-file-i-o/
- **Microsoft Graph API**: https://learn.microsoft.com/en-us/graph/api/overview
- **OneDrive API Overview**: https://learn.microsoft.com/en-us/onedrive/developer/rest-api/
- **OneDrive Upload**: https://learn.microsoft.com/en-us/graph/api/driveitem-put-content
- **Microsoft Graph Python Examples**: https://github.com/pranabdas/Access-OneDrive-via-Microsoft-Graph-Python
- **Box Python SDK**: http://opensource.box.com/box-python-sdk/
- **Box API Docs**: https://developer.box.com/guides/
- **Box OAuth2**: https://developer.box.com/guides/authentication/oauth2/with-sdk/
- **Adapter Pattern**: https://refactoring.guru/design-patterns/adapter
- **Python Protocol**: https://peps.python.org/pep-0544/

---

## Summary and Next Steps

This research document provides comprehensive technical guidance for Phase 1 design decisions. Key takeaways:

### Technology Stack Finalized

| Component | Technology | Justification |
|-----------|-----------|---------------|
| **ELN Integration** | `labarchives-py` + `elabapi-python` | Official/community-supported libraries for NIH-approved ELNs |
| **TDT Processing** | Official TDT SDK + GuPPy | Standard tools for fiber photometry signal extraction |
| **NWB Packaging** | `ndx-fiber-photometry` + `pynwb` + `neuroconv` | DANDI-compatible, community-standard extension |
| **File Watching** | `watchfiles` (Rust-based) | High-performance, low-resource monitoring |
| **DANDI Upload** | `dandi-cli` SDK + `tenacity` | Official SDK with robust retry logic |
| **Task Queue** | Celery + Redis | Mature, high-throughput task queue |
| **Storage Backends** | `aiofiles` + Graph API + Box SDK | Async I/O with cloud provider SDKs |

### Design Patterns Established

1. **Adapter Pattern**: Storage backends (local, OneDrive, Box)
2. **Protocol-based Interfaces**: Type-safe, testable abstractions
3. **Retry with Exponential Backoff**: `tenacity` for transient failures
4. **Idempotency**: Composite task IDs (subject+session) prevent duplicate processing
5. **Dead-Letter Queue**: Manual review of terminal failures
6. **Completion Detection**: Size stability, manifest files, timeout-based strategies

### Critical Implementation Notes

- **Python 3.13 only**: Enforced by project constitution
- **pixi for all dependencies**: No pip/conda allowed
- **No mocks in E2E tests**: Real ELN/DANDI integration required
- **Structured logging**: JSON lines with request/subject/session IDs
- **Provenance tracking**: Git SHA, processing params, checksums in NWB and ELN

### Risks and Mitigations

| Risk | Mitigation |
|------|-----------|
| LabArchives rate limits | Exponential backoff, respect `Retry-After` headers |
| Large TDT file uploads | Resumable uploads, chunking, timeout adjustments |
| Network instability | Retry logic, dead-letter queue, file size stability checks |
| NWB validation failures | Validate early in pipeline, log to ELN, halt processing |
| Cloud storage API changes | Adapter pattern isolates changes, SDK abstractions |

### Phase 1 Ready Deliverables

With this research complete, Phase 1 can proceed with:

1. **Adapter interfaces** defined in `adapters/eln/base.py` and `adapters/storage/base.py`
2. **LabArchives and eLabFTW adapters** implemented with authentication stubs
3. **TDT tank parser** using official SDK and GuPPy integration
4. **NWB packager** with `ndx-fiber-photometry` schema mapping
5. **File watcher service** using `watchfiles` with completion detection
6. **Celery tasks** for packaging and upload with retry logic
7. **DANDI uploader** with `tenacity`-wrapped SDK calls
8. **Local storage adapter** as baseline (cloud adapters can be stubs initially)

### Open Questions for Implementation

1. **LabArchives HTML parsing**: Need to define standardized field markers (data attributes) for robust extraction
2. **Session manifest format**: Define JSON schema for expected files (TDT tank, videos, behavior CSVs)
3. **ELN field mappings**: Create mapping tables (ELN fields → NWB fields) as JSON schemas in `nwb/schemas/`
4. **Operator UI**: Decide on Streamlit dashboard features (monitoring, manual retry, DLQ review)
5. **Observability**: Choose structured logging library (structlog vs python-json-logger)

**Document Status**: Complete and ready for Phase 1 design reference.

---

**Document Metadata**:
- **Research Completed**: 2025-10-27
- **Technologies Evaluated**: 8 major areas, 20+ libraries
- **References Cited**: 50+ documentation sources
- **Next Document**: `design.md` (Phase 1 architecture and API contracts)
