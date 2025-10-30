# elabftw-app Project Timeline

**Project**: ELN to DANDI Pipeline Automation
**Total Duration**: 14-19 weeks
**Timeline Reduction**: 30-40% faster due to ArchiveFlow foundation
**Last Updated**: 2025-10-29

---

## Timeline Overview

| Phase | Duration | Status | Priority |
|-------|----------|--------|----------|
| **Phase -1: Codebase Migration** | 2 weeks | Not Started | CRITICAL |
| **Phase 0: Research** | 1 week | Completed (Documentation) | Done |
| **Milestone 1: MVP - Multi-ELN + Local NWB** | 3-4 weeks | Not Started | P1 |
| **Milestone 2: Automation + DANDI Upload** | 4-5 weeks | Not Started | P2 |
| **Milestone 3: Storage Backend Support** | 3-4 weeks | Not Started | P3 |
| **Milestone 4: Production Hardening** | 2-3 weeks | Not Started | P4 |
| **TOTAL** | **14-19 weeks** | Planning Complete | - |

---

## Phase -1: Codebase Migration & Architecture Refactoring

**Duration**: 2 weeks
**Weeks**: 1-2
**Status**: Not Started
**Priority**: CRITICAL (Constitutional Compliance)

### Objective
Migrate existing ArchiveFlow prototype (~4,800 LOC) to constitutional compliance

### Key Tasks
- **M-1**: Package manager migration (uv → pixi, gradual module-by-module)
- **M-2**: Python version upgrade (3.11 → 3.13, direct migration, HIGH RISK)
- **M-3**: Directory structure refactoring (`archiveflow/` → `app/`, `ui/`, `workers/`, `adapters/`)
- **M-4**: Create FastAPI backend skeleton with shared business logic layer
- **M-5**: Retrofit Streamlit UI to use shared business logic
- **M-6**: Extract LabArchives API wrapper for separate PyPI package
- **M-7**: Migrate tests to new structure
- **M-8**: **NEW** Implement eLabFTW adapter (CRITICAL, moved from M3)

### Migration Strategy
Incremental refactoring with parallel operation (both ArchiveFlow and new system running)

### Rollback Plan
Branch strategy - keep `archiveflow-legacy` frozen

### Risks
- **HIGH**: Python 3.13 compatibility issues (numerical instability in signal processing)
- **MEDIUM**: Data corruption during refactoring
- **MITIGATION**: Smoke tests, parallel operation, frozen legacy branch

---

## Phase 0: Research

**Duration**: 1 week
**Weeks**: 3 (overlaps with Phase -1)
**Status**: ✅ Completed (Documentation Phase)
**Priority**: Done

### Objective
Validate technical approaches and resolve implementation unknowns

### Research Areas
1. ✅ LabArchives API integration (VALIDATED by ArchiveFlow)
2. 🆕 eLabFTW API integration (NEW - critical for launch)
3. ✅ TDT tank data processing (VALIDATED by ArchiveFlow)
4. 🟡 NWB schema mapping (libraries present, packaging logic needed)
5. 🟡 File system watcher patterns (watchdog → watchfiles upgrade)
6. 🆕 DANDI upload best practices (not implemented in ArchiveFlow)
7. 🆕 Celery architecture for scientific pipelines (not in ArchiveFlow)
8. 🆕 Multi-storage backend patterns (OneDrive, Box)

### Output
`specs/001-eln-to-dandi-pipeline/research.md` (~10,000 words) ✅ Completed

---

## Milestone 1: MVP - Multi-ELN + Local NWB Generation

**Duration**: 3-4 weeks
**Weeks**: 3-6 (adjusted for eLabFTW addition)
**Status**: Not Started
**Priority**: P1 (CRITICAL)
**Timeline Note**: ACCELERATED due to ArchiveFlow foundation, EXTENDED by 1 week for eLabFTW

### Objective
Working pipeline from ELN to validated NWB file on local storage

### Key Deliverables
- ✅ LabArchives ELN adapter (ALREADY IMPLEMENTED in ArchiveFlow)
- 🆕 **eLabFTW adapter (MOVED FROM M3, CRITICAL FOR LAUNCH)**
- 🆕 Shared business logic layer (DRY architecture)
- ✅ Directory creation from metadata (ALREADY IMPLEMENTED)
- 🆕 Configurable NWB file generation (raw/processed/both)
- 🆕 NWB Inspector validation (no static golden dataset)
- 🆕 Manual approval UI for NWB generation
- 🟡 Manual upload trigger via UI (existing Streamlit pages retrofitted)

### Cut Line
DANDI automation can be manual for MVP (Milestone 2 feature)

### Success Criteria
- Valid NWB file generated for test dataset
- Both LabArchives AND eLabFTW adapters working
- Manual approval workflow functional
- NWB validation passing

---

## Milestone 2: Automation - Watcher + DANDI Upload

**Duration**: 4-5 weeks
**Weeks**: 7-11
**Status**: Not Started
**Priority**: P2 (HIGH)
**Timeline Note**: PARTIALLY ACCELERATED (preprocessing exists, needs Celery wrapping)

### Objective
Automated pipeline with file watching, background jobs, and DANDI upload

### Key Deliverables
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

### Cut Line
Multi-storage backends (OneDrive/Box) can slip to Milestone 3

### Success Criteria
- End-to-end automation with approval gates working
- File watcher detecting data readiness
- Successful DANDI upload with retry logic
- <5 minute sync latency (ELN → Directory)
- >95% upload success rate

---

## Milestone 3: Storage Backend Support

**Duration**: 3-4 weeks
**Weeks**: 12-15
**Status**: Not Started
**Priority**: P3 (MEDIUM)
**Timeline Note**: Renamed (eLabFTW moved to M1)

### Objective
Add cloud storage backends (OneDrive, Box) for multi-institutional support

### Key Deliverables
- 🆕 OneDrive storage adapter (Microsoft Graph API)
- 🆕 Box storage adapter (Box SDK)
- 🆕 Storage backend selection via configuration
- 🆕 Async file operations for all backends
- ✅ Full E2E tests for both LabArchives and eLabFTW (multi-ELN validated)

### Cut Line
Advanced preprocessing pipelines can slip to post-launch

### Success Criteria
- OneDrive and Box adapters functional
- Configuration-driven storage backend selection
- E2E tests passing for all ELN/storage combinations

---

## Milestone 4: Production Hardening

**Duration**: 2-3 weeks
**Weeks**: 16-19
**Status**: Not Started
**Priority**: P4 (Launch Readiness)

### Objective
Performance optimization, monitoring, documentation, and security review

### Key Deliverables
- Performance optimization (signal processing, NWB generation)
- Error recovery and retry logic refinement
- Monitoring and alerting (Prometheus/Grafana integration)
- Documentation and operator training materials
- Security review (secrets management, NIH data boundary)
- Load testing (concurrent experiments, DANDI upload throughput)

### Success Criteria
- All 10 success criteria met (see PROJECT_OVERVIEW.md)
- Performance SLOs achieved
- Security review passed
- Operator documentation complete
- Production deployment ready

---

## Cumulative Timeline Breakdown

### Weeks 1-2: Phase -1 (Migration)
**Focus**: Constitutional compliance, architecture refactoring, eLabFTW adapter
**Output**: Migrated codebase on pixi + Python 3.13 with eLabFTW support

### Weeks 3-6: Milestone 1 (MVP)
**Focus**: Multi-ELN support, NWB generation, manual approval workflow
**Output**: Working ELN → NWB pipeline with LabArchives + eLabFTW

### Weeks 7-11: Milestone 2 (Automation)
**Focus**: File watching, background jobs, DANDI upload, retry logic
**Output**: Semi-automated pipeline with DANDI integration

### Weeks 12-15: Milestone 3 (Storage)
**Focus**: Cloud storage backends (OneDrive, Box)
**Output**: Multi-institutional storage support

### Weeks 16-19: Milestone 4 (Hardening)
**Focus**: Performance, monitoring, security, documentation
**Output**: Production-ready system

---

## Critical Path Dependencies

### Sequential Dependencies (BLOCKING)
1. **Phase -1 MUST complete** before M1 begins (pixi + Python 3.13 required)
2. **M1 MUST complete** before M2 begins (NWB generation required for DANDI upload)
3. **M2 SHOULD complete** before M3 begins (automation logic needed for cloud storage)
4. **M3 MUST complete** before M4 begins (all features needed for load testing)

### Parallel Opportunities
- Phase 0 research (already done) overlapped with early Phase -1
- eLabFTW adapter (M-8) can be developed in parallel with uv→pixi migration
- Documentation can be written throughout all phases

---

## Milestones vs. Original Plan (Without ArchiveFlow)

| Phase | Original Estimate | With ArchiveFlow | Reduction |
|-------|-------------------|------------------|-----------|
| Phase -1 | N/A (not needed) | 2 weeks | +2 weeks (new phase) |
| Phase 0 | 2 weeks | 1 week | -50% (some research validated) |
| Milestone 1 | 5-6 weeks | 3-4 weeks | -40% (LabArchives + directory logic done) |
| Milestone 2 | 6-7 weeks | 4-5 weeks | -30% (preprocessing exists) |
| Milestone 3 | 4-5 weeks | 3-4 weeks | -25% (adapter pattern established) |
| Milestone 4 | 3-4 weeks | 2-3 weeks | -30% (Streamlit UI exists) |
| **TOTAL** | **20-28 weeks** | **14-19 weeks** | **-32% average** |

---

## Key Timeline Adjustments Made

### 1. Added Phase -1 (Migration) - +2 weeks
**Reason**: ArchiveFlow uses uv + Python 3.11, constitution requires pixi + Python 3.13
**Impact**: +2 weeks upfront, but saves 6-9 weeks overall

### 2. Moved eLabFTW from M3 to M1 - +1 week to M1
**Reason**: Collaborating labs blocked without eLabFTW support
**Impact**: M1 extended from 2-3 weeks to 3-4 weeks, but M3 reduced by 1 week

### 3. Reduced M1 from 5-6 weeks to 3-4 weeks - -2 weeks
**Reason**: LabArchives adapter and directory logic already implemented in ArchiveFlow
**Impact**: Faster MVP delivery

### 4. Reduced M2 from 6-7 weeks to 4-5 weeks - -2 weeks
**Reason**: TDT preprocessing already implemented in ArchiveFlow
**Impact**: Faster automation delivery

---

## Risk Buffer Allocation

### Phase -1: HIGH RISK (Python 3.13 migration)
**Buffer**: 0.5 weeks built into 2-week estimate
**Contingency**: If Python 3.13 incompatible, revert to 3.11 (requires constitution amendment)

### Milestone 1: MEDIUM RISK (eLabFTW adapter)
**Buffer**: 1 week built into 3-4 week estimate
**Contingency**: If eLabFTW blocked, ship M1 with LabArchives only (requires stakeholder approval)

### Milestone 2: MEDIUM RISK (DANDI upload reliability)
**Buffer**: 1 week built into 4-5 week estimate
**Contingency**: Manual upload workflow as fallback

### Milestone 3: LOW RISK
**Buffer**: 1 week built into 3-4 week estimate
**Contingency**: Ship with local storage only, defer cloud storage

### Milestone 4: LOW RISK
**Buffer**: 1 week built into 2-3 week estimate
**Contingency**: Defer non-critical monitoring features

---

## Timeline Assumptions

### Included in Estimates
- 1 full-time developer equivalent
- ArchiveFlow codebase available for reference and extraction
- LabArchives and eLabFTW API access available
- DANDI staging environment access available
- Standard development environment (no tooling setup delays)

### NOT Included in Estimates
- Stakeholder review and approval time
- External dependency delays (API downtime, version incompatibilities)
- Additional feature requests during implementation
- Production deployment and infrastructure setup
- Post-launch bug fixes and maintenance

### Working Assumptions
- 5-day work weeks
- Time for code review, testing, and documentation included
- CI/CD setup time included in Phase -1
- E2E test environment setup included in each milestone

---

## Next Steps: Week 1 Kickoff

### Day 1-2: Environment Setup
- Install pixi
- Create `archiveflow-legacy` branch
- Extract ArchiveFlow.zip
- Audit dependencies

### Day 3-5: pixi Migration Start
- Create `pixi.toml`
- Migrate core dependencies
- Set up pixi tasks
- Run smoke tests

### Week 2: Python 3.13 + eLabFTW
- Migrate to Python 3.13
- Validate numerical stability
- Begin eLabFTW adapter implementation
- Update tests

---

**End of Timeline Document**

**For Details**: See [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md), [plan.md](specs/001-eln-to-dandi-pipeline/plan.md)
**For Context**: See [next_context.md](next_context.md)
**For Tasks**: Run `/tasks` command to generate detailed task breakdown
