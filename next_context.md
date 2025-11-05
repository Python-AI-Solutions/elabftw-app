# Next Context - elabftw-app Project State

**Last Updated**: 2025-10-29
**Current Branch**: `heet-dev`
**Project Status**: Planning & Design Complete, Ready for Implementation

---

## Current Position

We have completed the **specification and planning phase** for the elabftw-app project. All design documents are finalized, lab-agnostic, and ready for implementation to begin.

### What We Just Completed

1. ✅ Created project constitution with 7 NON-NEGOTIABLE principles
2. ✅ Created comprehensive feature specification (spec.md)
3. ✅ Created detailed implementation plan (plan.md)
4. ✅ Analyzed existing ArchiveFlow prototype (~4,800 LOC by Josh Lawrimore)
5. ✅ Generated research findings, data model, contracts, and quickstart guide
6. ✅ Answered 23 stakeholder clarification questions
7. ✅ Applied all decisions to spec and plan
8. ✅ Made all documentation lab-agnostic (removed "Tejeda Lab" references)
9. ✅ Created PROJECT_OVERVIEW.md consolidating all work
10. ✅ Added ArchiveFlow.zip to .gitignore
11. ✅ All changes committed and pushed to `heet-dev` branch

---

## Key Files Created (All in Git)

### Core Documentation
- `.specify/memory/constitution.md` - 7 core principles (Python 3.13, pixi-only, E2E testing, etc.)
- `specs/001-eln-to-dandi-pipeline/spec.md` - Feature specification with 5 user stories, 20 FRs
- `specs/001-eln-to-dandi-pipeline/plan.md` - Implementation plan with Phase -1 through M4
- `PROJECT_OVERVIEW.md` - Comprehensive single-document overview (930 lines)

### Supporting Documentation
- `specs/001-eln-to-dandi-pipeline/research.md` - Phase 0 technical research (~10,000 words)
- `specs/001-eln-to-dandi-pipeline/data-model.md` - 8 entity definitions with Pydantic schemas
- `specs/001-eln-to-dandi-pipeline/quickstart.md` - Developer setup guide
- `specs/001-eln-to-dandi-pipeline/CLARIFICATION_QUESTIONS.md` - 23 answered decisions
- `specs/001-eln-to-dandi-pipeline/contracts/` - 4 API specification files
  - `eln-adapter.yaml` - ELN adapter OpenAPI spec
  - `storage-adapter.yaml` - Storage adapter OpenAPI spec
  - `api-endpoints.yaml` - FastAPI endpoints spec
  - `nwb-schema.json` - NWB schema mapping
- `specs/001-eln-to-dandi-pipeline/checklists/requirements.md` - Quality validation checklist

### Configuration
- `CLAUDE.md` - Technical guardrails (updated with tech stack)
- `.gitignore` - Updated to exclude ArchiveFlow.zip

---

## Project Overview (Quick Reference)

### Mission
Automate the protocol-to-publication workflow for neuroscience fiber photometry experiments:
**ELN → Structured Directory → NWB File → DANDI Archive**

### Key Components
1. **Multi-ELN Support**: LabArchives (NIH) + eLabFTW (open-source)
2. **Automated Directory Management**: Lab-specific schemas, cohort organization
3. **NWB File Generation**: Using ndx-fiber-photometry extension
4. **DANDI Upload**: Automatic with manual approval gates
5. **Semi-Automatic Workflow**: Manual approvals before NWB generation and DANDI upload

### Technology Stack (NON-NEGOTIABLE)
- **Runtime**: Python 3.13 only
- **Package Manager**: pixi only (no pip, conda, poetry)
- **Backend**: FastAPI + Celery + Redis
- **UI**: Streamlit
- **Testing**: pytest with real E2E (no mocks)

### Timeline: 14-19 weeks
- **Phase -1**: Migration (2 weeks) - ArchiveFlow uv→pixi, Python 3.11→3.13, eLabFTW adapter
- **M1**: MVP Multi-ELN + Local NWB (3-4 weeks)
- **M2**: Automation + DANDI Upload (4-5 weeks)
- **M3**: Storage Backends (3-4 weeks)
- **M4**: Production Hardening (2-3 weeks)

---

## Critical Decisions Applied

### 1. eLabFTW is CRITICAL for Launch
**Moved from M3 (P5) to M1 (P2)** - Collaborating labs blocked without it

### 2. Lab-Agnostic Design
**Removed ALL "Tejeda Lab" references** - System now universally applicable

### 3. Semi-Automatic Workflow
**Manual approval gates** before NWB generation and DANDI upload

### 4. ArchiveFlow Migration Strategy
**Incremental refactoring** with parallel operation (not rebuild from scratch)

### 5. Python 3.13 Migration (HIGH RISK)
**Direct migration without pre-testing** - Constitutional requirement, smoke tests for validation

### 6. Configurable NWB Scope
**Per-experiment selection** of raw/processed/both data

### 7. Hybrid Sync Strategy
**Webhooks preferred, polling fallback** (5-min delay acceptable)

### 8. NWB Validation
**Use NWB Inspector** (not static golden dataset)

---

## Repository State

### Current Branch: `heet-dev`
- All planning and design work committed
- Clean working directory (no uncommitted changes)
- ArchiveFlow.zip present but gitignored

### Pull Request Status
- **PR #1**: Open, `heet-dev` → `main`
- **PR Description**: May need update to reflect lab-agnostic approach and eLabFTW criticality

### Branch Strategy
- `main` - Empty production branch (ready for merge)
- `heet-dev` - Current development branch with all work
- `archiveflow-legacy` - To be created during Phase -1 (frozen rollback reference)

---

## What Needs to Happen Next

### Immediate Next Steps (In Priority Order)

#### 1. Generate Task Breakdown (RECOMMENDED NEXT)
**Command**: `/tasks`
**Purpose**: Convert plan.md milestones into specific, actionable implementation tasks
**Output**: `specs/001-eln-to-dandi-pipeline/tasks.md`
**Why**: Provides detailed task-by-task roadmap for implementation

#### 2. Update PR Description (Optional)
**Action**: Update PR #1 description to highlight:
- Lab-agnostic design (removed "Tejeda Lab" references)
- eLabFTW elevated to CRITICAL (P2, Milestone 1)
- PROJECT_OVERVIEW.md as comprehensive reference
- Timeline: 14-19 weeks with ArchiveFlow foundation

#### 3. Stakeholder Review (Before Implementation)
**Action**: Share PROJECT_OVERVIEW.md with:
- DSST team
- Josh Lawrimore (ArchiveFlow developer)
- Collaborating research laboratories
- NIH NIMH oversight

#### 4. Begin Phase -1 Migration (When Ready)
**First Tasks**:
- Set up pixi environment (`pixi init`)
- Create `archiveflow-legacy` frozen branch
- Extract and analyze ArchiveFlow codebase structure
- Begin gradual uv→pixi migration (module-by-module)

---

## Files to Work On Next (Implementation Phase)

### Phase -1: Migration (Weeks 1-2)

1. **pixi.toml** (to be created)
   - Define dependencies from ArchiveFlow's requirements
   - Create pixi tasks: `api`, `ui`, `worker`, `test`, `lint`, `fmt`, `typecheck`
   - Pin Python 3.13

2. **Directory Structure Refactoring**
   - Extract `archiveflow/` → new structure:
     - `app/` - FastAPI backend (new)
     - `ui/` - Streamlit UI (from existing)
     - `workers/` - Celery jobs (new)
     - `adapters/eln/labarchives/` - LabArchives wrapper (extract)
     - `adapters/eln/elabftw/` - eLabFTW adapter (NEW, CRITICAL)
     - `nwb/` - NWB packager (from existing preprocessing)
     - `dandi/` - DANDI uploader (new)

3. **Shared Business Logic Layer** (NEW)
   - `app/services/` - Shared services called by both Streamlit and FastAPI
   - Refactor Streamlit UI to use shared logic (DRY principle)

4. **Tests Migration**
   - Move existing tests to `tests/unit/`, `tests/integration/`, `tests/e2e/`
   - Update test structure for new architecture

5. **eLabFTW Adapter Implementation** (CRITICAL)
   - `adapters/eln/elabftw/adapter.py`
   - Follow ELN adapter protocol from `contracts/eln-adapter.yaml`
   - Use `elabapi-python` SDK

---

## Files Currently Tracked (Do Not Create Again)

These files already exist and are committed:
- `.specify/memory/constitution.md`
- `specs/001-eln-to-dandi-pipeline/spec.md`
- `specs/001-eln-to-dandi-pipeline/plan.md`
- `specs/001-eln-to-dandi-pipeline/research.md`
- `specs/001-eln-to-dandi-pipeline/data-model.md`
- `specs/001-eln-to-dandi-pipeline/quickstart.md`
- `specs/001-eln-to-dandi-pipeline/CLARIFICATION_QUESTIONS.md`
- `specs/001-eln-to-dandi-pipeline/contracts/*.yaml` (4 files)
- `specs/001-eln-to-dandi-pipeline/checklists/requirements.md`
- `PROJECT_OVERVIEW.md`
- `CLAUDE.md`
- `.gitignore`

---

## Important Context for Next Session

### 1. ArchiveFlow Prototype
- **Location**: `ArchiveFlow.zip` (gitignored, available locally)
- **Size**: ~4,800 LOC
- **Developer**: Josh Lawrimore, PhD (NIMH DSST)
- **Status**: Working prototype with LabArchives integration and TDT processing
- **Conflicts**: Uses `uv` (not pixi), Python 3.11 (not 3.13)
- **Value**: Foundation that reduces timeline by 30-40%

### 2. Constitutional Requirements (HARD CONSTRAINTS)
- **Python 3.13 ONLY** - No other versions allowed
- **pixi ONLY** - Never emit pip, conda, poetry, requirements.txt
- **E2E Real Systems** - No mocks in E2E tests; mark as "blocked" if unavailable
- **NWB Compliance** - All files must pass `pynwb.validate()`
- **Idempotency** - Re-running produces byte-identical NWB files

### 3. Migration Risks
- **HIGH RISK**: Direct Python 3.13 migration without pre-testing
  - Mitigation: Smoke tests, validation of signal processing outputs
- **MEDIUM RISK**: LabArchives API rate limits
  - Mitigation: Exponential backoff, polling interval tuning
- **LOW RISK**: Data corruption during refactoring
  - Mitigation: Parallel operation, frozen legacy branch

### 4. Multi-ELN Priority
- **LabArchives**: NIH instance, OAuth2, already implemented in ArchiveFlow
- **eLabFTW**: CRITICAL for launch (P2), moved from M3 to M1, extends M1 by 1 week

### 5. Approval Workflow
- **Semi-Automatic**: NOT fully automatic
- **Manual Gates**: Before NWB generation AND before DANDI upload
- **Researcher Control**: Can pause pipeline for specific experiments

---

## Commands to Remember

### Speckit Commands (Already Used)
- `/constitution` - Create/update constitution ✅ Done
- `/specify` - Create feature specification ✅ Done
- `/plan` - Generate implementation plan ✅ Done
- `/tasks` - Generate task breakdown 🔜 **Next Step**
- `/clarify` - Identify underspecified areas ✅ Done (manual Q&A)
- `/analyze` - Cross-artifact consistency analysis (optional)
- `/implement` - Execute implementation plan (future)

### Development Commands (Future)
```bash
pixi run api      # Start FastAPI backend
pixi run ui       # Start Streamlit UI
pixi run worker   # Start Celery worker
pixi run test     # Run all tests
pixi run e2e      # Run E2E tests (requires credentials)
pixi run lint     # Ruff linting
pixi run fmt      # Ruff formatting
```

---

## Success Criteria (How We'll Know We're Done)

1. ✅ **SC-001**: Metadata handling <10 seconds (from 10+ minutes)
2. ✅ **SC-002**: Manual data packaging time reduced by 95%
3. ✅ **SC-003**: 100% of fiber photometry experiments generate valid NWB
4. ✅ **SC-004**: 100% of uploads pass DANDI validation
5. ✅ **SC-005**: Sync latency <5 minutes (ELN → NWB)
6. ✅ **SC-006**: DANDI upload success rate >95%
7. ✅ **SC-007**: All operations include provenance tracking
8. ✅ **SC-008**: Dynamic scaling for concurrent experiments
9. ✅ **SC-009**: Pipeline status visible within 10 seconds
10. ✅ **SC-010**: Stable operation with both LabArchives and eLabFTW

---

## Key Stakeholders

- **DSST (Division of Scientific and Statistical Tools)**: Development team
- **Josh Lawrimore, PhD**: ArchiveFlow developer, consultation during migration
- **Collaborating Research Laboratories**: End users conducting fiber photometry experiments
- **NIH NIMH**: Institutional sponsor, compliance oversight

---

## External Dependencies & Access Requirements

### Required for E2E Testing
- **LabArchives**: NIH instance API access (OAuth2 credentials)
- **eLabFTW**: Demo/sandbox instance API access (API key)
- **DANDI**: Staging environment access (API key)

### Required for Implementation
- **TDT SDK**: Tucker-Davis Technologies signal processing library
- **GuPPy**: Fiber photometry analysis library
- **Microsoft Graph API**: OneDrive storage adapter (M3)
- **Box SDK**: Box storage adapter (M3)

---

## Questions to Resolve (Future)

1. **Directory Schema Flexibility**: Is there an NIH-wide standard, or per-lab customization?
   - Status: Need to research (marked in decisions as "need to research")

2. **ArchiveFlow Extraction Rights**: Can we extract LabArchives wrapper as separate PyPI package?
   - Status: Consult with Josh Lawrimore and DSST legal

3. **DANDI Staging Access**: Do we have access to DANDI staging environment for E2E tests?
   - Status: Need to request from DANDI maintainers

---

## How to Resume Next Session

### Option 1: Continue with Task Generation (RECOMMENDED)
**Prompt**: "Generate detailed implementation tasks using `/tasks` command"
**Expected Output**: `specs/001-eln-to-dandi-pipeline/tasks.md` with dependency-ordered tasks

### Option 2: Begin Phase -1 Migration
**Prompt**: "Begin Phase -1 migration: create pixi.toml and set up Python 3.13 environment"
**First Actions**: Initialize pixi, define dependencies, create task commands

### Option 3: Update PR Description
**Prompt**: "Update PR #1 description to reflect lab-agnostic design and eLabFTW criticality"
**Action**: Use GitHub CLI to update PR description with PROJECT_OVERVIEW.md summary

### Option 4: Stakeholder Review Preparation
**Prompt**: "Prepare stakeholder review materials from PROJECT_OVERVIEW.md"
**Action**: Create presentation/summary for DSST and collaborating labs

---

## Summary: Where We Are

**✅ COMPLETED**: Planning and Design Phase
**🔜 NEXT**: Task Generation (`/tasks`) → Implementation Phase
**📍 POSITION**: Ready to begin Phase -1 migration or generate detailed task breakdown
**⏱️ TIMELINE**: 14-19 weeks of implementation ahead
**🎯 GOAL**: Automated ELN → NWB → DANDI pipeline for fiber photometry experiments

---

**End of Context Document**
**To Resume**: Share this file with Claude and specify which option (1-4) you'd like to pursue.
