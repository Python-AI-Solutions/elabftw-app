## /specify — Functional Specification Prompt (elabftw-app)

```
/specify
You are drafting the functional specification for the elabftw-app.

Context:
NIH intramural investigators are required to transition to electronic records for all experiments. Dr. Tejeda’s group currently uses LabArchives ELN to record fiber photometry behavioral experiments in mice. elabftw-app aims to semi-automate the pipeline from experimental recording to packaging in NWB format and uploading to the DANDI data repository. The system is developed by DSST with collaboration from MLT and should support both LabArchives and eLabFTW.

Primary users:
- NIH researchers running experiments (Tejeda Lab and others).
- Data managers and ML engineers needing standardized inputs.
- External collaborators who require reproducible and structured data packaging.

Goals (ranked):
1. Automate syncing of experimental metadata from ELN to local/remote structured directory.
2. Automate creation of standardized project directories from ELN entries.
3. Package metadata and primary data into NWB-compliant datasets (e.g., ndx-fiber-photometry).
4. Automate upload of NWB files to DANDI archive.
5. Support multiple ELN backends (LabArchives and eLabFTW) through modular API interfaces.
6. Reduce manual entry time, increase reproducibility, and ensure regulatory compliance.

Non-goals / out of scope:
- Building a new ELN.
- Manual data entry replacement (we are augmenting, not replacing ELN).
- Creating a new data repository.

Key user journeys:
1. Researcher completes experiment in ELN widget.
2. App detects new entries via API → parses metadata.
3. App generates standardized folder structure on shared storage.
4. Researcher drops raw data in the right directory.
5. Watcher detects readiness → triggers preprocessing.
6. Metadata + data converted into NWB file → code version logged in ELN.
7. NWB uploaded to DANDI archive.
8. Project status synced back to ELN.

Inputs/Outputs & Entities:
- Inputs: ELN entries, raw data files (TDT tank, protocol files, videos).
- Outputs: structured directory, metadata spreadsheets, NWB files, DANDI upload records.
- Entities: Subject, Surgery, Behavior, Data Acquisition, Analysis Run, Dataset Package.

Constraints & policies:
- Must comply with NIH June 2024 electronic records mandate.
- Support ELN API authentication securely.
- Use NWB standard (ndx-fiber-photometry extension).
- Ensure reproducibility and versioning.

Success metrics:
- Reduce metadata handling time from minutes to seconds per experiment.
- 95% reduction in manual data packaging time.
- 100% NWB/DANDI compliance for supported experiments.
- Stable syncing between ELN and directory.

Risks & unknowns:
- LabArchives API is NIH-internal.
- Multi-storage support complexity.
- NWB schema evolution.
- External developer capacity for modularization.

Deliverables:
1. Functional app to sync ELN → directory → NWB → DANDI.
2. Modular ELN interface layer.
3. Basic support for both LabArchives and eLabFTW.
4. Automated data pipeline for fiber photometry.
5. Metadata traceability across full lifecycle.
```
