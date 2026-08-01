# FloatChat Remediation Plan

Synthesized from `docs/audit/BASELINE_AUDIT.md` after five independent audits and cross-review. This is a living plan — phases are gated on the previous phase's verification passing, per the project's test-gated commit protocol.

## Target architecture

One canonical product path, no duplicate RAG logic:

- **`web/`** — Next.js UI only. Talks to the Python API; never calls Ollama/Postgres/Chroma directly.
- **`backend/`** — installable Python package + FastAPI service. Owns query parsing, retrieval, SQL/data access, analytics, synthesis, plot specs, health checks, streaming. Built from the current `agentic_workflow/`, after H-1/H-2 (import structure) are fixed — that fix is a prerequisite, not parallel work.
- **`scripts/`** — explicit, safe administrative CLIs (ingestion, index building, migration, export, validation). The current `scripts/` tree is legacy/experimental (zero overlap with `agentic_workflow/`, undeclared deps) and will be archived under `scripts/legacy/` rather than deleted, pending owner sign-off on what's still needed.
- **`tests/`** — currently empty; net-new.
- **`docs/`** — architecture, ADRs, data dictionary, runbooks (this directory).
- **`data/`** (gitignored) — Chroma persistence, the raw dataset dump, generated plots, logs. Source control keeps manifests/checksums, not the mutable runtime files themselves (see C-2, H-13).

## Decisions that need the repo owner, not a guess

These are genuine blockers uncovered by the audit — proceeding past them requires either a credential only the owner has, or a judgment call the plan shouldn't make unilaterally:

1. **Postgres password (C-1).** The hardcoded `rgk`/`rgk` credential fails authentication against the actual local instance right now. This needs either the real current password or a decision to drop/recreate the role — a credential change, which this plan will not perform without explicit direction.
2. **Ollama model selection.** Real installed inventory differs from what the original brief assumed (`qwen3-embedding:8b` and `qwen3.5:4b` exist and weren't anticipated; `qwen2:1.5b`/`embeddinggemma:300m` — what's currently configured — don't exist at all). Model choice is gated on the benchmarking phase below, not decided here.
3. **Git history.** C-2 quantifies ~97 MB of tracked cruft. Fixing `.gitignore` and `git rm --cached`-ing the newly-ignored paths going forward is in scope for this plan. Rewriting history to shrink the existing repo (`git filter-repo`/BFG) is **not** — it rewrites every commit hash and breaks the existing remote/any clones, and is explicitly out of scope for this run per the project's git-safety rules. Flagged as an option for the owner to decide on separately.
4. **`agentic_workflow/chroma_db/`, `scripts/` legacy tree, and the `plots/`/`web/public/plots/` duplication.** All confirmed either orphaned or duplicated (H-12, L-1, ARCH-8), but nothing gets deleted/untracked without the owner seeing the preservation ledger and approving the exact path list first, per the project's data-preservation rules.

## Phased sequence

Maps to the 8 tracked phases; each phase ends with a verification gate before the next begins.

**Phase 1 — Repo hygiene & secrets removal** (addresses C-2, C-5, H-7, M-1–M-10, L-1–L-8 groundwork)
- Replace root `.gitignore` with the corrected version (typos fixed, `chroma_db/`, `*.log`, `.DS_Store`, secrets patterns added).
- Extract every hardcoded credential/URL/model-tag/path (C-5, and the config-side of C-1) into a typed, env-var-backed settings module; add `.env.example` for the Python side.
- Fix the unparameterized SQL in `sql_executor_tool.py` (H-7) and remove/constrain the freeform LLM-SQL path in `xai.py` (C-3) — these are cheap, high-value, low-risk fixes independent of the bigger restructure and should land early.
- Add a confirmation flag to the destructive DB script and stop it from being the ambiguous "how do I set up the DB" default (C-4).
- **Not included in this phase:** actually removing tracked large files from git — that's a separate, explicitly-approved step once the owner has seen the preservation ledger.

**Phase 2 — Qwen/Ollama feasibility benchmarking**
- Benchmark the real installed candidates (`qwen2.5:1.5b`, `qwen2.5:3b`, `qwen2.5:7b`, `qwen3.5:4b` for chat; `qwen3-embedding:8b` for embedding) against the RTX 3060's actual, re-measured VRAM headroom (598 MiB–700 MiB free was observed during the audit, well short of what several of these need — must be re-checked at benchmark time, not assumed).
- Select one default + one fallback chat model and validate the embedding model's dimension/latency/stability, per the original brief's feasibility gate. Write `docs/MODEL_SELECTION.md`.

**Phase 3 — Chroma preservation & v2 index**
- External backup of both existing collections (already done for this audit — see the private session record — but re-verify immediately before this phase, since C-1/H-13's fixes change how the store is opened).
- Build `argo_profiles_v2` per rag-data's Task 5 schema (adds `profile_date`, `year`, `month`, `latitude`, `longitude`, `region_primary` + membership flags, `source_hash`, `schema_version`, `embedding_model` — directly fixing H-3's definitional half, H-8, and enabling real metadata filtering per the original brief).
- Cosine space, not `l2` (fixes L-7); stamped provenance metadata (fixes H-8); single authoritative ingestion path (fixes H-9).
- Retrieval evaluation (40+ questions, scaffolded in the audit's Task 6 output) comparing v1 vs. v2.

**Phase 4 — Backend API service**
- Prerequisite: fix H-1/H-2 (import structure) — cannot be skipped or done in parallel, since the API layer needs a cleanly importable package.
- FastAPI wrapper around a corrected `WorkflowEngine`: fix the unreachable-code bug (H-4), fix region comparison (H-3), reconcile the duplicate visualization pipelines (H-11), fix the CWD-dependent Chroma path (H-13).
- Health endpoints reporting API/Postgres/Chroma/Ollama/model state separately.

**Phase 5 — Frontend integration, tests, CI, docs**
- Replace the Anthropic-direct `/api/chat` with a validated call to the new backend; add rate limiting and request schema validation (H-5, M-12); remove `dangerouslySetInnerHTML` in favor of a safe markdown renderer (H-6); fix the accessibility gaps (M-13); replace hardcoded stats with live values from the backend (L-3).
- Add `tests/` (unit, integration with fixture Chroma/fake Ollama, one end-to-end path), CI workflow, coverage gate.
- Write the remaining docs deliverables (`ARCHITECTURE.md`, `DATA_AND_INDEX_MIGRATION.md`, `RAG_EVALUATION.md`, `DATA_DICTIONARY.md`, `SECURITY.md`, updated `README.md`/`CONTRIBUTING.md`/`docs/DEVELOPMENT.md`) and `docs/audit/VERIFICATION_REPORT.md`.

## Condensed move-map

The complete file-by-file mapping follows the same categorization as the audit above; the condensed shape:

| Current | Destination | Note |
|---|---|---|
| `agentic_workflow/{agents,core,tools,ui,utils,main.py}` | `backend/<package>/...` | not a pure move — import style changes first (H-1) |
| `agentic_workflow/requirements.txt` | `backend/requirements.txt` or `pyproject.toml` | no packaging metadata exists today |
| `agentic_workflow/streamlit_app.py` | owner decision: retire, or `backend/<pkg>/ui/streamlit_app.py` as an optional dev surface calling the same service layer | |
| `agentic_workflow/{agentic_workflow.log,xai_audit.log}` | untracked; runtime instance to gitignored `data/logs/` | fix ARCH-5's CWD-relative path first |
| `agentic_workflow/chroma_db/` | pending owner approval | confirmed orphaned (H-12) |
| `argo_data_dump.txt` | `data/raw/` (gitignored) | 62 MB; confirm regenerable-vs-irreplaceable with owner before any history action |
| `chroma_db/` (root) | `data/chroma/` at runtime | canonical live store; git tracking removed per C-2/ARCH-1 |
| `plots/` | `data/artifacts/plots/` (gitignored) or a small curated `docs/images/` subset | `web/public/plots/` stays (Next.js requires it) |
| `scripts/*` (24 files) | `scripts/legacy/` + its own `requirements.txt` | archived with a provenance note, not deleted |
| `web/**` | stays | integration point is `api/chat/route.ts` |

## Risk register (hardest to reverse, highest priority to get right)

1. Any future git-history rewrite to shrink the ~97 MB of tracked cruft — owner-only decision, not performed here.
2. Touching either `chroma_db/` copy (delete/move/regenerate) — confirmed to mutate on mere open (audit integrity note #1); external backup must stay current throughout.
3. The Phase 4 import restructure touches every file in `agents/`/`tools`/`core`/`ui` at once with zero pre-existing test coverage — Phase 5's tests should ideally land partially *before* this restructure where practical, to catch regressions.
4. `argo_data_dump.txt` — no single script in the repo obviously regenerates it end-to-end from raw sources (ingestion/scrapper/loading are disconnected); treat as possibly irreplaceable until confirmed otherwise.
