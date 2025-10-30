## /constitution — Project Rules (elabftw-app)

```
/constitution
Title: elabftw-app — Engineering Constitution

Always True
- Mission: Automate protocol-to-publication for Tejeda-style experiments: ELN → structured dir → NWB (ndx-fiber-photometry) → DANDI, with status synced back to ELN.
- Supported ELNs: LabArchives (NIH instance, via wrapper) and eLabFTW (for open demo).
- Data standards: NWB mandatory; use neuroconv/pynwb; DANDI upload automated.

Tooling & Runtime
- Python: **3.13** everywhere (runtime, CI, notebooks).
- Env/Deps: **pixi only** for dependency resolution and task runners (no pip/conda/poetry).
- Services: FastAPI backend; Streamlit operator UI; background workers (asyncio/Celery).
- VCS: Git + trunk-based branching; semantic commit messages; include code version hash in ELN logs.

Pipelines & Testing
- Unit/integration may use fakes; **E2E must hit real systems (no mocks)** for ELN → dir → NWB → DANDI happy-path. If external access is impossible, mark E2E as *blocked* rather than mocking.
- Determinism: All packaging steps are idempotent; re-runs must produce byte-stable NWB (minus timestamps).
- Observability: Structured logs, metrics for sync latency (<5 min), and DANDI upload success rate.

Architecture Constraints
- Modular ELN adapters: LabArchives wrapper + eLabFTW via `elabapi-python`.
- Pluggable storage adapters: local FS/OneDrive/Box; directory schema dictated by ELN entries (Surgery, Behavior, etc.).
- Watcher triggers preprocessing/analysis; record analysis provenance and code versions back to ELN.

Security & Compliance
- Store tokens in secrets manager; never commit credentials.
- Keep research data within NIH-approved storage; no PII/exfiltration; audit all transformations.

Review Gates (cannot merge without)
- NWB file passes pynwb validation; DANDI dry-run OK.
- Spec/plan alignment checked; constitution rules satisfied (Python 3.13, pixi, no E2E mocks).
```
