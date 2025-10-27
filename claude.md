# elabftw-app — claude.md (Technical Guardrails & Authoring Policy)

**Purpose.** This document constrains how code, configs, and docs are generated for **elabftw-app**. It complements the project **Constitution** with strict, low-level rules so any assistant/tooling (including Claude) produces compliant, production-quality changes.

---

## 0) Golden Rules (hard requirements)

1. **Runtime**: Python **3.13 only** (runtime, CI, scripts, notebooks).
2. **Dependencies**: **pixi only** for resolution and task running.  
   - ❌ Do not emit `pip`, `conda`, `poetry`, `pipenv`, `requirements.txt`, or `environment.yml`.
3. **E2E Testing**: **No mocks** for the ELN→Dir→NWB→DANDI happy path. If external access is unavailable, mark E2E **blocked**; do not fake.
4. **Standards**: NWB (with `ndx-fiber-photometry`), DANDI uploads via CLI/SDK, ELN via LabArchives wrapper & `elabapi-python`.
5. **Security**: Never output real secrets, tokens, or credentials. Emit secret *names* and retrieval stubs only.

---

## 1) Project Structure & Paths (must adhere)

```
app/                       # FastAPI backend
  main.py
  routes/
  services/
  schemas/
ui/                        # Streamlit operator UI
workers/                   # async jobs (packaging/upload)
adapters/
  eln/
    labarchives/
    elabftw/
  storage/
    local/
    onedrive/
    box/
nwb/                       # NWB packager and schema mapping
dandi/                     # DANDI uploader and manifest logic
tests/
  unit/
  integration/
  e2e/
infra/                     # deployment & ops scripts (no secrets)
.speckit/inputs/           # /constitution, /specify, /plan, /tasks, claude.md
.github/workflows/
scripts/
pixi.toml
ruff.toml
mypy.ini
.pre-commit-config.yaml
```

**Never** create additional top-level folders without justification.

---

## 2) Language, Typing, Style

- **Typing**: 100% public API type-annotated. No `Any` in public interfaces.
- **Docstrings**: Google style.
- **Imports**: absolute imports; group stdlib / third-party / first-party.
- **Lint/Format**:
  - `ruff` with `line-length = 100`, select: `B,I,N,UP,FURB,W,E`.
  - `ruff format` is the **only** formatter.
- **Mypy**: `python_version = 3.13`, `strict_optional = True`, `ignore_missing_imports = True`.

**Do not** disable lints broadly; fix causes or apply the narrowest ignore with justification.

---

## 3) pixi Tasks (canonical commands)

All runnable commands must be defined in **pixi**:

```toml
# pixi.toml
[tasks]
api = "uvicorn app.main:app --reload --port 8000"
ui = "streamlit run ui/Home.py"
test = "pytest -q"
unit = "pytest -q tests/unit"
integration = "pytest -q tests/integration"
e2e = "pytest -q -m e2e"
lint = "ruff check ."
fmt = "ruff format ."
typecheck = "mypy app adapters workers nwb dandi"
package_one = "python -m nwb.package_one --subject $SUBJECT_ID"
upload = "python -m dandi.upload --path $ARTIFACT"
```

> Emit **only** `pixi run …` in docs/scripts. Never `python -m pip …` or `poetry …`.

---

## 4) API & Schema Contracts

- **FastAPI**: define Pydantic `BaseModel` request/response; no untyped dicts.
- **Routes**: versioned under `/v1/…`.
- **Backward compatibility**: additive only. Breaking changes require `/v2/…`.
- **Event payloads** (watcher, jobs): define JSON schemas and validate at boundaries.
- **NWB**: emit mapping tables (ELN fields → NWB fields) as versioned JSON under `nwb/schemas/`.

---

## 5) Adapters (ELN & Storage)

**ELN Adapter Interface** (must implement):

```python
class ELNAdapter(Protocol):
    def get_project(self, project_id: str) -> Project: ...
    def list_entries(self, project_id: str) -> list[Entry]: ...
    def get_entry(self, entry_id: str) -> Entry: ...
    def append_note(self, entry_id: str, text: str) -> None: ...
    def download_attachment(self, entry_id: str, attachment_id: str, dest: Path) -> None: ...
```

- `adapters/eln/labarchives/…` uses the Lawrimore wrapper.
- `adapters/eln/elabftw/…` uses `elabapi-python`.

**Storage Adapter Interface**:

```python
class StorageAdapter(Protocol):
    def ensure_structure(self, manifest: Manifest) -> None: ...
    def put(self, src: Path, dst: Path) -> None: ...
    def exists(self, path: Path) -> bool: ...
    def list(self, path: Path) -> list[Path]: ...
```

- Provide **local** implementation first; `onedrive` and `box` stubs can raise `NotImplementedError` until configured.

---

## 6) NWB Packaging Rules

- Use `neuroconv` + `pynwb`.
- Include `ndx-fiber-photometry`; pin compatible versions in **pixi**.
- Packaging must be **idempotent**: re-running produces byte-stable files (allowing timestamp differences).
- Always run `pynwb validate` and persist a validation report artifact.
- Record provenance (Git SHA, conda/env hash equivalent via pixi lock hash, parameters) into:
  - the NWB file metadata (as available), and
  - the ELN via `append_note`.

---

## 7) DANDI Upload Rules

- Use DANDI CLI/SDK with resumable uploads.
- Precompute dandiset metadata YAML; validate with dandi’s validators before upload.
- On success, write DANDI ID/DOI back to ELN and to local manifest.

---

## 8) Watcher & Jobs

- Watcher detects readiness based on **explicit** manifest conditions (e.g., TDT, AnyMaze, video all present).
- Jobs must implement:
  - **retries with exponential backoff**,
  - **idempotency keys** (subject/session composite),
  - **dead-letter** queue/logging on terminal failure.

---

## 9) Observability

- **Structured logging** (JSON lines). Include `request_id`, `subject_id`, `entry_id`, `job_id`.
- Metrics:
  - ELN→Dir sync latency (target < 5 min)
  - Packaging duration
  - DANDI upload throughput & success %
- Traces: wrap packaging and upload steps; do not leak secrets into spans.

---

## 10) Security & Secrets

- Retrieve tokens via environment or secrets manager **only** (placeholder stubs acceptable).  
  Example:

```python
LABARCHIVES_TOKEN = os.environ["LABARCHIVES_TOKEN"]  # do not default
```

- Never log tokens, headers, or file contents.
- Keep research data in approved storage; no copying to temp cloud buckets unless configured adapter is approved.

---

## 11) Testing Policy

- **Unit**: fast, isolated; fakes/stubs allowed.
- **Integration**: real library calls against **sandbox/demo** services where possible.
- **E2E** (`@pytest.mark.e2e`): touch **real** ELN + **real** DANDI (or sanctioned sandbox).  
  - If unavailable, mark as **skipped: blocked by access** (do not mock).
- **Minimum coverage**: 85% unit; packaging and upload paths must be covered.
- Validation gate: NWB validation must pass in CI for golden test dataset.

**Never** commit test fixtures containing PII or real secrets.

---

## 12) CI/CD Gates (GitHub Actions)

1. Constitution checks (Python 3.13, no pip/conda, E2E policy text present).
2. Lint (`ruff check`) → fail on warnings.
3. Typecheck (`mypy`) → no errors.
4. Unit + integration tests.
5. NWB validation on golden dataset artifact.
6. (Optional) E2E job; allowed to **skip** with “blocked” message; never to mock.

Branch protection:
- Require PR review (≥1).
- Disallow force pushes to `main`.
- Require CI success.

---

## 13) Performance & Resource SLOs

- Sync poll interval default ≤ 60s; end-to-end ELN→Dir latency **P95 < 5 min**.
- Single packaging job **P95 < 10 min** for standard dataset (define in docs).
- DANDI upload uses chunking; **resume on failure**; no single chunk > 256 MiB unless required.

---

## 14) Error Handling & Resilience

- Wrap external calls with:
  - timeouts,
  - limited retries with jitter,
  - classification (4xx vs 5xx),
  - structured error objects (code, reason, context).
- Never swallow exceptions; surface actionable logs and user-facing status.

---

## 15) Prohibited Practices

- ❌ Emitting or suggesting `pip install`, `conda install`, `poetry add`.
- ❌ Global state in long-running services (use DI or explicit context).
- ❌ Writing plain files to arbitrary temp dirs without user-configurable base path.
- ❌ Silent fallback to mocks in E2E.
- ❌ Hard-coding paths, tokens, or institution-specific IDs.

---

## 16) Documentation Requirements

- Update **README** for any new pixi task or interface addition.
- Maintain field-mapping tables (ELN → NWB) in `nwb/schemas/*.json` and reference them in docs.
- Operator runbooks for:
  - onboarding a new lab,
  - adding a new storage backend,
  - rotating ELN/DANDI tokens.

---

## 17) “Ask-Before-Act” Triggers (for assistants)

When any of the following are true, **ask 3–5 crisp questions before generating code**:
- Introducing a new dependency.
- Proposing a new top-level folder.
- Altering NWB schemas or ELN field mappings.
- Changing task names in `pixi.toml`.
- Adjusting CI gates or bypass policies.

---

## 18) Commit & PR Hygiene

- Conventional commits: `feat:`, `fix:`, `refactor:`, `docs:`, `test:`, `chore:`.
- PR must include:
  - rationale,
  - test notes (unit/integration/E2E),
  - risks/rollbacks,
  - screenshots or logs for operator-facing changes.

---

## 19) Allowed Network Domains (default)

- ELN: `*.labarchives.com` (NIH instance), `*.elabftw.net` or configured demo host.
- DANDI: `*.dandiarchive.org`
- Storage APIs as configured (`*.microsoft.com` for OneDrive, `*.box.com`).
- GitHub: `api.github.com` for CI artifacts only.

Block any new domain until explicitly added.

---

## 20) Minimal Boilerplate Snippets (reference only)

**FastAPI route skeleton**
```python
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/v1/sync", tags=["sync"])

class SyncRequest(BaseModel):
    project_id: str

class SyncResponse(BaseModel):
    accepted: bool
    request_id: str

@router.post("/", response_model=SyncResponse)
def trigger_sync(req: SyncRequest) -> SyncResponse:
    # Call ELN adapter, schedule job, return request id
    ...
```

**Pytest markers**
```python
# tests/conftest.py
import pytest
def pytest_configure(config):
    config.addinivalue_line("markers", "e2e: marks end-to-end tests")

@pytest.fixture(scope="session")
def golden_dataset_path(tmp_path_factory):
    return tmp_path_factory.mktemp("golden")
```

---

## 21) Final Review Checklist (must pass before merge)

- [ ] Python 3.13 enforced; no non-pixi dependency commands.
- [ ] Public APIs fully typed; lint & typecheck clean.
- [ ] Contracts & schemas updated (and versioned) when applicable.
- [ ] Tests added/updated; coverage OK; NWB validation passes for golden dataset.
- [ ] No secrets; logs are structured; errors actionable.
- [ ] Docs & pixi tasks updated; operator impact considered.
