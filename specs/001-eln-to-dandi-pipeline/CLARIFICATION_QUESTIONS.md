# Clarification Questions for ELN to DANDI Pipeline Specification

**Purpose**: Enrich the specification and implementation plan with stakeholder input
**Created**: 2025-10-29
**Status**: Awaiting Responses

---

## 1. ArchiveFlow Migration Strategy

### Q1.1: ArchiveFlow Migration Approach

**Context**: ArchiveFlow is a working prototype with ~4,800 lines of code. We need to migrate it to comply with the constitution (uv→pixi, Python 3.11→3.13, add FastAPI backend).

**Question**: What migration strategy should we use for ArchiveFlow during Phase -1?

**Options**:
- [ ] **Option A**: Freeze ArchiveFlow and build new system from scratch (preserves working system, slower timeline)
- [ ] **Option B**: Incremental refactoring with parallel operation (both systems running, gradual cutover)
- [ ] **Option C**: In-place migration with maintenance mode (faster, some downtime expected)
- [ ] **Option D**: Other approach (specify below)

**Notes**: Option B requires Josh Lawrimore consultation. Option C needs Tejeda Lab approval for downtime.

---

### Q1.2: Package Manager Migration (`uv` → `pixi`)

**Context**: ArchiveFlow uses `uv` for dependency management. Constitution requires `pixi` (NON-NEGOTIABLE).

**Question**: How should we handle the uv→pixi migration for ArchiveFlow dependencies?

**Options**:
- [ ] **Option A**: Hard cutover - remove uv entirely, pixi-only from Day 1 (clean break, higher risk)
- [ ] **Option B**: Parallel management - uv for legacy, pixi for new code (enables validation, more complex)
- [ ] **Option C**: Gradual migration - convert module by module with both systems (safest, slowest)
- [ ] **Option D**: Other approach (specify below)

**Notes**: ArchiveFlow has Git dependencies (`tdt-reader`, `neural-analysis`) that may need special handling in pixi.

---

### Q1.3: Python Version Upgrade (3.11 → 3.13)

**Context**: ArchiveFlow requires Python >=3.11. Constitution requires Python 3.13 (NON-NEGOTIABLE).

**Question**: What testing approach should we take before committing to Python 3.13?

**Options**:
- [ ] **Option A**: Test all dependencies and numerical outputs in 3.13 before migration (thorough, slower)
- [ ] **Option B**: Test only critical dependencies, assume rest compatible (faster, moderate risk)
- [ ] **Option C**: Use Python 3.12 as intermediate stable version (not constitution-compliant)
- [ ] **Option D**: Direct migration to 3.13 without pre-testing (fastest, highest risk)

**Notes**: Signal processing numerical outputs (TDT streams, fiber photometry calculations) should be validated for consistency.

---

## 2. Architecture & Scope Decisions

### Q2.1: FastAPI Backend Integration Strategy

**Context**: ArchiveFlow is pure Streamlit (synchronous UI). Plan calls for adding FastAPI backend + Celery workers.

**Question**: How should Streamlit UI and FastAPI backend be integrated?

**Options**:
- [ ] **Option A**: Streamlit + FastAPI microservices from Day 1 (clean separation, requires full refactor)
- [ ] **Option B**: Streamlit-first, add FastAPI endpoints incrementally as needed (gradual, less disruption)
- [ ] **Option C**: Shared business logic layer called by both Streamlit and FastAPI (DRY, moderate complexity)
- [ ] **Option D**: Keep Streamlit standalone, FastAPI for external integrations only (minimal changes)

**Notes**: Option A requires significant upfront refactoring. Option D may violate constitution's architectural vision.

---

### Q2.2: NWB File Generation Scope

**Context**: ArchiveFlow has `neuroconv` and `ndx-fiber-photometry` installed but no packaging code. This is User Story 3 (Priority P3).

**Question**: What data should be included in generated NWB files?

**Options**:
- [ ] **Option A**: Raw TDT streams only (minimal processing, large files)
- [ ] **Option B**: Preprocessed signals only (smaller files, loses raw data)
- [ ] **Option C**: Both raw and preprocessed data (comprehensive, largest files)
- [ ] **Option D**: Configurable per-experiment (flexible, requires UI/config)

**Notes**: Need sample NWB schema from Tejeda Lab and list of mandatory metadata fields (subject, surgery, session, device, signals).

---

### Q2.3: DANDI Upload Workflow

**Context**: DANDI upload mentioned in ArchiveFlow README but not implemented. This is Priority P4.

**Question**: How should DANDI uploads be triggered and approved?

**Options**:
- [ ] **Option A**: Automatic upload after NWB validation passes (fully automated, requires trust)
- [ ] **Option B**: Manual operator approval required before upload (safe, slower)
- [ ] **Option C**: Batch upload with operator review (efficient for multiple files)
- [ ] **Option D**: Individual upload with status tracking (fine-grained control)

**Notes**: Clarify if Tejeda Lab has existing DANDI dandiset or if one needs to be created. Check NIH network restrictions on DANDI API access.

---

## 3. Directory Structure & Data Organization

### Q3.1: Tejeda Lab Directory Schema Flexibility

**Context**: ArchiveFlow uses hardcoded 5-folder structure: Surgery, Behavior, Photometry, Histology, Metadata with "Cohort N" subdirectories.

**Question**: How flexible should the directory schema be for supporting other labs?

**Options**:
- [ ] **Option A**: Fixed Tejeda schema only (hardcode 5 folders, cohort pattern - simplest)
- [ ] **Option B**: Semi-flexible - allow folder name variants but same 5-category structure (minor adaptability)
- [ ] **Option C**: Fully flexible - YAML/JSON config defines directory schema per lab (maximum adaptability)
- [ ] **Option D**: Unknown - need to research if this is NIH-wide standard first

**Notes**: Impacts maintainability and multi-lab support. Option C adds significant complexity.

---

### Q3.2: Cohort Naming Enforcement

**Context**: ArchiveFlow expects "Cohort N" pattern (e.g., "Cohort 1", "Cohort 2"). Other variants seen in code: "Cohort 01", "cohort_1", etc.

**Question**: How strict should cohort naming enforcement be?

**Options**:
- [ ] **Option A**: Strict enforcement - reject non-compliant names with error (prevents confusion, inflexible)
- [ ] **Option B**: Lenient - warn but allow non-standard names (flexible, may cause downstream issues)
- [ ] **Option C**: Auto-fix - suggest corrections and offer to rename (user-friendly, complex logic)
- [ ] **Option D**: No enforcement - accept any cohort naming (maximum flexibility, risky)

**Notes**: Consider whether cohort numbers have semantic meaning (chronological order, experimental conditions).

---

### Q3.3: File Organization and Validation

**Context**: ArchiveFlow creates subdirectories for behavior forms (CSV tables, metadata.json) and expects TDT tanks in `Photometry/Cohort N/Tanks/`.

**Question**: How should the system handle files placed in wrong locations?

**Options**:
- [ ] **Option A**: Strict validation - error and block processing until fixed (enforces discipline)
- [ ] **Option B**: Auto-organize - move files to correct locations with notification (convenient, may surprise users)
- [ ] **Option C**: Warn but process - log warnings and continue (lenient, may hide issues)
- [ ] **Option D**: Configurable per-lab - let labs choose enforcement level (flexible, complex)

**Notes**: Should system support non-TDT acquisition systems (Neurophotometrics, Doric) in the future? **[ ] Yes [ ] No [ ] Unknown**

---

## 4. Multi-ELN Support & Extensibility

### Q4.1: eLabFTW Priority and Timeline

**Context**: eLabFTW integration is User Story 5 (Priority P5), currently not implemented. Plan places it in Milestone 3 (weeks 9-12).

**Question**: What priority should eLabFTW support have for the initial launch?

**Options**:
- [ ] **Option A**: Critical for launch - move to M1/M2 (delays other features, required for specific labs)
- [ ] **Option B**: Important - keep in M3 as planned (balanced approach)
- [ ] **Option C**: Deferred - post-launch enhancement in M4+ (focus on LabArchives first)
- [ ] **Option D**: Unknown - need to identify labs waiting for eLabFTW support

**Notes**: Impacts timeline and resource allocation. Check if specific collaborators are blocked without eLabFTW.

---

### Q4.2: ELN Adapter Interface Design

**Context**: Plan calls for modular ELN adapters with `authenticate()`, `get_entries()`, `update_entry_status()`, `get_attachments()` methods.

**Question**: How should ELN adapters handle data transformation and parsing?

**Options**:
- [ ] **Option A**: Thin adapters - return ELN-specific data, parsing in business logic (simple adapters, complex business layer)
- [ ] **Option B**: Thick adapters - parse and return standardized models, ELN-agnostic business logic (complex adapters, simple business layer)
- [ ] **Option C**: Hybrid - standard interface with optional ELN-specific extensions (balanced, moderate complexity both layers)
- [ ] **Option D**: Per-lab parsers - custom parsing configs per lab regardless of ELN (maximum flexibility, maintenance burden)

**Notes**: Consider who builds parsers for custom LabArchives widgets - lab configs or built into adapters?

---

## 5. Automation & Workflow

### Q5.1: End-to-End Automation Level

**Context**: ArchiveFlow requires manual steps (login, select experiment, sync, place files, extract, process). Plan calls for full automation.

**Question**: What level of automation should the pipeline target?

**Options**:
- [ ] **Option A**: Full automation - ELN entry → DANDI upload with zero manual intervention (hands-off, requires robust error handling)
- [ ] **Option B**: Semi-automatic - auto-detect/sync, manual approval before NWB generation and upload (safer, slower)
- [ ] **Option C**: Assisted manual - system prepares everything, operator triggers each step (maximum control, defeats automation goal)
- [ ] **Option D**: Configurable per-experiment - researchers choose automation level (flexible, complex)

**Notes**: How should ambiguous cases (missing metadata, file errors) be handled? Should researchers be able to pause pipeline for specific experiments?

---

### Q5.2: ELN Synchronization Strategy

**Context**: Plan mentions polling ELN APIs every 5 minutes. LabArchives may support webhooks (unclear).

**Question**: What mechanism should trigger ELN synchronization?

**Options**:
- [ ] **Option A**: Polling - check ELN API every N minutes (simple, predictable, may be slow)
- [ ] **Option B**: Webhooks - LabArchives/eLabFTW POST to our API on new entries (real-time, requires webhook support)
- [ ] **Option C**: Hybrid - webhooks preferred, polling as fallback (best of both, more complex)
- [ ] **Option D**: On-demand - operator-triggered sync only (simple, not automated)

**Notes**: Need to verify if LabArchives supports webhooks. What is acceptable sync delay - 5 minutes, 1 hour, real-time?

---

### Q5.3: Error Handling and Retry Configuration

**Context**: Plan requires retry logic with exponential backoff for DANDI uploads and ELN API calls.

**Question**: What retry and failure handling strategy should be implemented?

**Options**:
- [ ] **Option A**: Conservative - 3 retries, 1-60s backoff, dead-letter queue, email alerts (safe, may give up too early)
- [ ] **Option B**: Aggressive - 10 retries, 1-300s backoff, dead-letter queue, dashboard only (persistent, may delay failure detection)
- [ ] **Option C**: Moderate - 5 retries, 1-120s backoff, dead-letter queue, Slack alerts (balanced approach)
- [ ] **Option D**: Configurable - allow operators to set retry policies per job type (flexible, complex)

**Notes**: How should partial success be handled (e.g., 8 of 10 NWB files uploaded)? **Retry failed only [ ] or Retry all [ ]**

---

## 6. Testing & Validation

### Q6.1: E2E Testing Environment Access

**Context**: Constitution requires E2E tests with **real** LabArchives/eLabFTW/DANDI APIs (no mocks).

**Question**: What testing environments are available for E2E tests?

**Options**:
- [ ] **Option A**: Full sandbox access - separate LabArchives, eLabFTW, and DANDI staging instances (ideal, may not exist)
- [ ] **Option B**: Partial sandbox - DANDI staging only, production LabArchives with test entries (compromise)
- [ ] **Option C**: Production with safeguards - use production systems with clearly marked test data (risky, realistic)
- [ ] **Option D**: No E2E until launch - mark as blocked, rely on integration tests (constitution violation)

**Notes**: Can we create automated test ELN entries without disrupting real research? Should E2E tests run on every commit or nightly?

---

### Q6.2: Golden Dataset for NWB Validation

**Context**: Plan mentions using a "golden dataset" for NWB validation CI checks.

**Question**: What should the golden dataset be and where should it be stored?

**Options**:
- [ ] **Option A**: Synthetic small dataset in Git LFS (<10 MB, fast CI, not realistic)
- [ ] **Option B**: Real anonymized medium dataset in S3/Cloud (~100 MB, realistic, requires cloud setup)
- [ ] **Option C**: Real anonymized large dataset locally (>1 GB, most realistic, slow CI)
- [ ] **Option D**: Both synthetic and real - synthetic for fast CI, real for nightly validation (comprehensive, doubles work)

**Notes**: Does Tejeda Lab have a reference experiment to use? Should we version the golden dataset and track changes over time?

---

## 7. Performance & Scalability

### Q7.1: Concurrent Experiment Capacity

**Context**: Success criteria SC-008 states "support at least 10 concurrent experiments."

**Question**: What concurrent processing capacity should the system target?

**Options**:
- [ ] **Option A**: Tejeda Lab only - 10 concurrent experiments, largest dataset 50 GB (meet minimum criteria)
- [ ] **Option B**: Small multi-lab - 25 concurrent experiments, largest dataset 100 GB (some growth headroom)
- [ ] **Option C**: NIH-wide scale - 100+ concurrent experiments, largest dataset 500 GB (future-proof, over-engineering risk)
- [ ] **Option D**: Unknown - need to research actual usage patterns first

**Notes**: Should system throttle/queue beyond limit, or scale up (more workers)? What peak upload rate to DANDI is realistic?

---

### Q7.2: Video File Handling Strategy

**Context**: Behavior experiments include video files which can be very large (GB-sized).

**Question**: How should video files be handled in the NWB packaging and DANDI upload workflow?

**Options**:
- [ ] **Option A**: Include in NWB - embed videos directly (simple, very large NWB files)
- [ ] **Option B**: External storage - link to videos in separate storage (keeps NWB small, requires coordination)
- [ ] **Option C**: DANDI separate upload - videos as separate assets in dandiset (DANDI best practice, complex)
- [ ] **Option D**: Not uploaded - videos stay local only (simplest, may lose data)

**Notes**: Are videos required for DANDI or optional? Should system compress videos (lossy/lossless)? What formats are used (MP4, AVI, proprietary)?

---

## 8. Security & Compliance

### Q8.1: Secrets Management Implementation

**Context**: Constitution requires secrets manager (never hardcode tokens). ArchiveFlow uses `.env` files.

**Question**: What secrets management solution should be implemented?

**Options**:
- [ ] **Option A**: Environment variables + `.env` with `.gitignore` (simple, acceptable for MVP, less secure)
- [ ] **Option B**: Cloud secrets manager - AWS Secrets Manager, Azure Key Vault, or GCP Secret Manager (secure, requires cloud)
- [ ] **Option C**: HashiCorp Vault self-hosted (secure, NIH-controlled, complex setup)
- [ ] **Option D**: NIH-specific solution (need to research NIH policy requirements)

**Notes**: Do NIH policies mandate a specific secrets management solution? How should secrets be rotated - manual or automated?

---

### Q8.2: PII/PHI Handling and Data Governance

**Context**: Constitution prohibits PII exfiltration. Research data must stay in NIH-approved storage.

**Question**: How should potentially sensitive information be handled in NWB files and DANDI uploads?

**Options**:
- [ ] **Option A**: Include all - researcher names, exact dates, animal IDs as-is (simple, may violate policies)
- [ ] **Option B**: Minimal redaction - use researcher IDs, keep dates and animal IDs (balanced)
- [ ] **Option C**: Aggressive anonymization - hash IDs, relative timepoints, omit names (most secure, loses context)
- [ ] **Option D**: Configurable - lab chooses PII handling policy per experiment (flexible, complex)

**Notes**: Do ELN entries contain PHI/PII? Are animal subject IDs considered sensitive? **Approved storage**: Local NAS [ ], OneDrive Gov [ ], Box Gov [ ], Other: _______

---

## 9. Collaboration & Stakeholders

### Q9.1: Josh Lawrimore Role and Involvement

**Context**: Josh Lawrimore built ArchiveFlow prototype. He's credited in spec but unclear on ongoing role.

**Question**: What will Josh Lawrimore's role be during the Phase -1 migration and beyond?

**Options**:
- [ ] **Option A**: Active contributor - regular commits, code reviews, direct involvement (ensures continuity, requires availability)
- [ ] **Option B**: Consultant - available for questions and handoff meetings, not coding (knowledge transfer, less time commitment)
- [ ] **Option C**: Handoff complete - documentation only, no ongoing involvement (independent development, risk of knowledge loss)
- [ ] **Option D**: Unknown - need to clarify with Josh and DSST

**Notes**: Is Josh responsible for extracting LabArchives API wrapper as separate PyPI package? Who owns ArchiveFlow maintenance during transition?

---

### Q9.2: Tejeda Lab Stakeholder Engagement

**Context**: This system is being built for/with Tejeda Lab. Unknown how involved they are in development.

**Question**: What level of engagement should Tejeda Lab have during development?

**Options**:
- [ ] **Option A**: High engagement - weekly meetings, active feedback, UAT at each milestone (ensures alignment, time-intensive)
- [ ] **Option B**: Medium engagement - monthly demos, UAT at major milestones (balanced approach)
- [ ] **Option C**: Low engagement - occasional check-ins, post-launch feedback only (faster development, risk of misalignment)
- [ ] **Option D**: Unknown - need to discuss with Dr. Tejeda and lab members

**Notes**: Can we access Tejeda Lab LabArchives notebooks for testing (read-only)? Are there other lab members (students, postdocs) who should be involved?

---

## 10. Migration Risk Mitigation

### Q10.1: Rollback Strategy for Phase -1

**Context**: Phase -1 migration involves substantial refactoring. If things break, we need a rollback plan.

**Question**: What rollback strategy should be in place during ArchiveFlow migration?

**Options**:
- [ ] **Option A**: Branch strategy - keep `archiveflow-legacy` branch frozen (simple rollback, no parallel testing)
- [ ] **Option B**: Parallel deployment - run both systems until validation complete (safest, doubles infrastructure)
- [ ] **Option C**: Feature flags - toggle between old/new implementations (flexible, adds complexity)
- [ ] **Option D**: No rollback - forward-only migration with high confidence (fastest, highest risk)

**Notes**: What is acceptable downtime for Tejeda Lab during migration? How do we validate "migration success" before decommissioning ArchiveFlow?

---

### Q10.2: Pre-Migration Test Coverage Strategy

**Context**: ArchiveFlow has `tests/` directory but unclear coverage. Refactoring without tests is risky.

**Question**: What testing strategy should be used before migrating ArchiveFlow?

**Options**:
- [ ] **Option A**: Test-first - achieve 80%+ unit test coverage before any refactoring (safest, significant time investment)
- [ ] **Option B**: Smoke tests - cover critical paths only, refactor carefully (balanced, moderate risk)
- [ ] **Option C**: Characterization tests - record current behavior as golden outputs for regression testing (pragmatic for legacy code)
- [ ] **Option D**: Manual testing - rely on Tejeda Lab UAT to catch regressions (fastest, highest risk)

**Notes**: What is current test coverage percentage for ArchiveFlow? Should we extract key workflows as validation smoke tests?

---

## Instructions

Please review and mark **one option per question**. Add notes or specifications in the sections provided where needed. For questions marked "Unknown," please identify the person or group who can provide the answer.

**Priority Levels**:
- **MUST ANSWER before Phase -1**: Q1.1, Q1.2, Q2.1, Q2.2, Q2.3, Q3.1, Q5.1, Q9.1
- **SHOULD ANSWER before Phase 0**: Q4.1, Q4.2, Q5.2, Q6.1, Q6.2, Q7.2, Q8.1
- **CAN ANSWER during implementation**: Q3.2, Q3.3, Q5.3, Q7.1, Q8.2, Q9.2, Q10.1, Q10.2

---

**Document Version**: 2.0 (Multiple Choice Format)
**Created by**: Claude (via clarification task)
**Last Updated**: 2025-10-29
