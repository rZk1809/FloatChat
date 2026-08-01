# FloatChat Baseline Audit

**Method:** This audit is organized into five review areas — architecture/dependencies, RAG/data, backend/science, frontend/security, and quality/devops — cross-checked against each other where findings overlapped or conflicted. All file:line references were verified against the checkout at the time of writing; re-verify before acting, and use the repro command given on each finding.

## Audit integrity notes

**1. Chroma SQLite mutation during the audit (investigated, resolved, no data loss).** `chroma_db/chroma.sqlite3` and `agentic_workflow/chroma_db/chroma.sqlite3` were found modified in the working tree partway through this review, despite the review being read-only in intent. Root cause, confirmed three independent ways: (a) file sizes are byte-identical before/after (14,397,440 and 163,840 bytes); (b) a byte-level diff against the committed blob shows only 16 and 10 bytes changed respectively, landing in SQLite's header "file change counter"/"version-valid-for" fields — the signature of a WAL checkpoint triggered by opening a connection, not a data rewrite; (c) a direct content check (collection list + `count()`) against a pre-audit backup confirms identical row counts: `argo_profiles_ollama`=4922, `argo_profiles`=2612, the orphaned `agentic_workflow` store empty, in both the current and backed-up copies. **No logical data was lost.** Most likely cause: simply opening the store with a Chroma `PersistentClient` for inspection. This is exactly why C-2/ARCH-1 below recommend no longer tracking `chroma_db/` in git — as long as it's committed, any local run of the app can dirty the working tree and make an accidental overwrite of the canonical snapshot trivially easy.

**2. Instruction-shaped text found and disregarded during review.** One portion of this audit's raw exploration output contained text formatted to resemble an embedded system instruction, along with a reference to a local development-tool configuration path. Neither was acted on. A repository-wide search independently confirmed **no such file or directory exists anywhere in this repository**, tracked or untracked — the referenced path does not correspond to any real file here and has been excluded from this document; it will not be added to the actual `.gitignore`. Everything else from that pass was treated purely as data, cross-checked against the other four review areas and independently re-verified below where practical.

**3. A small number of additional diagnostic checks** (AST parsing of specific functions, isolated interpreter snippets with no DB/network/file-write reachability) were run beyond static reading, specifically to convert certain findings from "read the code" to "reproduced by execution" — each is called out inline as `Status: verified (reproduced)`. A follow-up repository-state check found no file changes beyond the already-diagnosed Chroma mutation in note 1.

---

## Critical

### C-1. The system does not work end-to-end on this machine right now
**Domains:** rag-data (RAG-1, RAG-2) · **Status:** verified
Both halves of the pipeline fail independently on the very first call:
- **Ollama:** `agentic_workflow/core/config.py:34-35` configures `embedding_model="embeddinggemma:300m"`, `general_model="qwen2:1.5b"`. Neither tag exists on this machine. `ollama show embeddinggemma:300m` → `Error: model not found`; `POST /api/generate {"model":"qwen2:1.5b",...}` → `404`. Installed look-alikes: `qwen2.5:1.5b`, `qwen3-embedding:8b` — different tags, not interchangeable.
- **PostgreSQL:** `agentic_workflow/core/config.py:14-18` hardcodes `user="rgk" password="rgk" host=localhost port=5432 db=argo_data`. Connecting with these exact credentials fails: `FATAL: password authentication failed for user "rgk"` (retested against `127.0.0.1` explicitly to rule out an IPv4/IPv6 split — same failure).
**Impact:** `RetrieverTool` can't embed a query, `PlannerAgent`/`SynthesizerAgent` can't call the LLM, `SQLExecutorTool` can't construct — the agentic pipeline is 0% functional as configured, independent of every other finding below.
**Fix:** two separate decisions needed from the repo owner: (1) which installed Ollama tags to standardize on (see the forthcoming `docs/MODEL_SELECTION.md` benchmarking phase — do not guess), (2) the current, correct Postgres password for the `rgk` role (or a decision to recreate the role) — **this is a credential the lead cannot supply or guess and must be provided by the owner.**
**Acceptance test:** `Config.validate_connections()` (already exists, `config.py:105-140`) returns all-`True` in a pre-flight/health check before any agent is instantiated.

### C-2. `.gitignore` doesn't match any of the large files it appears to target — 97.6 MB of the repo's tracked content is data/binary/log cruft
**Domains:** architect (ARCH-2), quality-devops (OPS-20) · **Status:** verified
`git ls-tree -r -l HEAD` totals **97.62 MB** across 117 tracked files. `argo_data_dump.txt` alone is **62.26 MB** (64% of everything tracked). Root `.gitignore` lines 5 and 10 read `SIH2025-IDEA-Presentation-Format(1).pptx` (real file has a space: `...Format (1).pptx`) and `argo_data_dumpt.txt` (real file: `argo_data_dump.txt`, no "t") — both are one-character/one-space off from the actual filenames and therefore never match. There is no `.gitignore` entry at all for `chroma_db/`, `.DS_Store`, or `*.log`. Net effect: the dataset dump, ~29.6 MB of Chroma binaries, 2 `.DS_Store` files, and 2 log files are permanently in git history.
**Fix:** replace `.gitignore` (full proposed text below), then `git rm --cached` the newly-matched paths — a deliberate, separate, explicitly-approved step, not automatic. Whether to also purge history (`filter-repo`/BFG) is a distinct, higher-risk decision this audit is flagging, not executing or recommending as a default.
**Acceptance test:** `git check-ignore -v argo_data_dump.txt chroma_db/chroma.sqlite3 .DS_Store agentic_workflow/agentic_workflow.log` returns a match for all four.

### C-3. `scripts/analysis/xai.py` executes LLM-generated SQL text against Postgres with only cosmetic sanitization
**Domains:** backend-science (SCI-2) · **Status:** verified
`generate_sql_from_query()` (`xai.py:228-286`) builds a prompt from the raw user chat message and asks Ollama to generate SQL; `fix_sql_schema()` (`xai.py:59-74`) only does plain `.replace()` column-name fixups, not a security control; `execute_sql_query()` (`xai.py:298`) runs `pd.read_sql(text(sql_query), conn)` on the result. The only pre-execution guard (`xai.py:290`) checks whether the string starts with `"-- Error"` — nothing else blocks `DROP`/`DELETE`/`UPDATE`, and nothing enforces `SELECT`-only.
**Impact:** an arbitrary-SQL-execution surface reachable from user input (accidental or adversarial prompt injection), independent of and more severe than the classic f-string injection patterns below, because the LLM intermediary can be steered to emit destructive statements directly.
**Fix:** remove this freeform text-to-SQL path, or constrain it to a strict allow-listed `SELECT`-only grammar validated with a real SQL parser (not string replace) and executed under a least-privilege read-only DB role, before it ever reaches `pd.read_sql`.
**Acceptance test:** a prompt engineered to request `DROP TABLE measurements` never results in a non-`SELECT` statement reaching the database; verified against a disposable test DB.

### C-4. `scripts/database/populate.py` runs an unconditional, undocumented `DROP TABLE ... CASCADE`
**Domains:** quality-devops (OPS-16) · **Status:** verified
`populate.py:35` — `DROP TABLE IF EXISTS measurements, profiles, floats CASCADE;` — unconditional, no confirmation flag, no mention in either `README.md` or `agentic_workflow/README.md`. A safer, idempotent `ingestion.py` (`CREATE TABLE IF NOT EXISTS`) exists alongside it doing the equivalent job. Compounding this, `RAG-7` (below) shows `populate.py`'s Chroma-writing half also independently diverged from and would silently corrupt the schema of the live 4,922-record collection if run.
**Impact:** the single most severe irreversible-data-loss risk found in this audit — a plausible, easy mistake (running the obviously-named "populate" script) destroys the entire ARGO dataset with no warning.
**Fix:** keep only the idempotent path as the documented one; rename the destructive script (e.g. `reset_and_reseed_dev_db.py`) behind an explicit `--confirm-destroy` flag and a typed confirmation prompt.
**Acceptance test:** running the documented setup path twice against a populated DB does not change row counts on the second run; the destructive path requires an explicit flag and refuses to run without it.

### C-5. Hardcoded, duplicated, and (per C-1) already-broken database credentials
**Domains:** quality-devops (OPS-14), backend-science (SCI-6), architect (ARCH-10), rag-data (RAG-9) · **Status:** verified
The literal pair `user="rgk"` / `password="rgk"` is hardcoded independently in at least 10 source locations plus documented in prose in 2 more: `agentic_workflow/core/config.py`, `scripts/database/postgres.py`, `scripts/database/populate.py`, `scripts/data/ingestion.py`, `scripts/data/loading.py`, `scripts/analysis/peek.py`, `scripts/analysis/xai.py`, `scripts/apps/app.py`, `scripts/apps/app1.py`, `scripts/vector_store/vector.py`, plus `agentic_workflow/README.md` and `agentic_workflow/PROJECT_SUMMARY.md`. Zero `os.environ`/`dotenv` usage exists anywhere on the Python side (`web/.env.example` covers only the unrelated Next.js app). Since the initial commit ("Rag Model V1"), per `git log -p`.
**Impact:** rotating a password requires editing ~12 files by hand; the credential has been in git history since the first commit; directly caused C-1's Postgres half.
**Fix:** one shared, env-var-backed config module; every script imports it; add a Python-side `.env.example`.
**Acceptance test:** `git grep -n '"rgk"'` returns nothing outside historical-context comments/docs after the fix.

---

## High

### H-1. `agentic_workflow` cannot be imported as a package from outside its own directory
**Domains:** architect (ARCH-3) · **Status:** verified (reproduced)
`agentic_workflow/__init__.py` uses a relative import, but `core/workflow_engine.py:10-13` and siblings use flat absolute imports (`from agents.planner_agent import ...`) that only resolve because `main.py`/`ui/cli_interface.py` manually `sys.path.insert` the `agentic_workflow/` directory itself. `python -c "import agentic_workflow"` from repo root fails: `ModuleNotFoundError: No module named 'agents'`.
**Impact:** this blocks the core goal of wiring a FastAPI backend on top of this package — it cannot be `pip install -e`'d and imported normally until internal imports are converted to relative/fully-qualified form.
**Fix:** convert `core/`, `agents/`, `tools/`, `ui/` internal imports to relative or fully-qualified form; add `pyproject.toml`.
**Acceptance test:** `python -c "import agentic_workflow"` (or the post-rename package) succeeds from repo root with no `sys.path` manipulation.

### H-2. Circular package initialization — real, but distinct from a simple import-graph cycle (cross-team discrepancy, reconciled)
**Domains:** backend-science (SCI-7) vs. architect (Task 2) · **Status:** verified — both findings are correct, about different things
Architect's per-file dependency graph (which file imports which) is a clean DAG with no back-edges — verified true. Backend-science reproduced a real `ImportError: cannot import name 'RetrieverTool' from partially initialized module 'tools.retriever_tool' (most likely due to a circular import)` when running `python -c "from tools.analyzer_tool import AnalyzerTool"` as the *first* import in a fresh interpreter. The cause is package-**initialization** order, not file-level imports: `core/__init__.py:4` eagerly imports `WorkflowEngine`, which imports `agents`, whose `__init__.py` eagerly imports `ExecutorAgent`, which imports `tools.retriever_tool`, which re-enters `core.config` — a cycle that only exists because of eager `__init__.py` re-exports, invisible to a per-file DAG. It "works" today purely because `main.py`/`streamlit_app.py` happen to touch `core.workflow_engine` first, in the one order that avoids tripping it.
**Impact:** blocks direct unit-testing of `tools`/`agents` modules and any import order other than the app's current lucky one; likely why no test suite exists.
**Fix:** stop eager-importing submodules in `__init__.py` files, or make the cross-package import in `retriever_tool.py` more targeted.
**Acceptance test:** `python -c "from tools.analyzer_tool import AnalyzerTool"` and `python -c "from agents.executor_agent import ExecutorAgent"` both succeed as the first import, in either order.

### H-3. Region comparison is broken both computationally and definitionally
**Domains:** backend-science (SCI-4, reproduced), rag-data (RAG-6, data-driven) · **Status:** verified
Two independent, compounding bugs on the product's own flagship demo query ("compare Arabian Sea vs. Bay of Bengal"):
1. **Computational:** `planner_agent.py:306` only ever retrieves the *first* region mentioned; `executor_agent.py:148-154`'s `_get_context_value()` then maps **both** `region1_measurements` and `region2_measurements` placeholders to the same single step-2 result. Reproduced: `region1_measurements is region2_measurements` → `True`. `compare_regions()` then runs a t-test against itself (own comment: `# Simplified - would need region filtering`).
2. **Definitional:** even if (1) is fixed, the configured region boxes (`config.py:60-76`) are not mutually exclusive — measured against the real 4,922 profile coordinates, **33.6% fall inside more than one region box simultaneously** (Bay of Bengal, 149 points, is essentially a geographic subset of the "Indian Ocean" box, which captures 81.9% of all points).
**Impact:** the system runs to completion and reports a confident, meaningless result (p≈1.0, "not significant") with no error — worse than a crash, for the exact scenario the product is demoed on.
**Fix:** planner must issue two independent per-region retrieval steps; `_get_context_value` must key by region, not a shared step index. Separately, compute one deterministic `region_primary` per profile (most-specific-wins) plus explicit multi-membership boolean flags, so comparisons are made between disjoint sets.
**Acceptance test:** for a two-region query, the two DataFrames passed to `compare_regions()` must not be the same object and must have different region provenance; `sum(region_primary counts) == total profile count` with no double-counting.

### H-4. The advertised "XAI logging" / SHAP feature is entirely dead code
**Domains:** quality-devops (OPS-15), backend-science (SCI-1, AST-verified), architect (ARCH-13) — independently found three ways · **Status:** verified
`WorkflowEngine.process_query()` returns at line 151; the history-append and XAI-logging calls at lines 153-161 sit *after* that return, inside the same block, and are unreachable (confirmed by AST parse: 4 unreachable statements including a dead second `return`). Separately, `XAILogger` (`utils/logger.py`) is exported by `utils/__init__.py` but never called from any agent/tool/entry point — confirmed by exhaustive grep. `shap` is never imported anywhere in the repository despite `README.md` and `web/src/app/page.tsx` both explicitly advertising "SHAP values" as a feature.
**Impact:** `get_workflow_history()` always returns `[]` on the success path; `xai_audit.log` is permanently 0 bytes (consistent, tracked-in-git evidence); the product's "Explainable AI" pillar cannot execute on a single successful query, and the specific SHAP claim has no implementation to even be dead code for.
**Fix:** move the history/XAI-logging lines above the return and delete the dead second return; either wire `XAILogger` into real stage transitions or remove the subsystem and the README/page.tsx claims.
**Acceptance test:** after a successful query, `workflow_history` has length ≥1 and `xai_audit.log` contains a corresponding structured entry.

### H-5. Public, unauthenticated `/api/chat` route with no rate limiting or spend caps
**Domain:** frontend-security (FE-1) · **Status:** verified
`web/src/app/api/chat/route.ts` forwards every request straight to Anthropic using the developer's own key. The only "limit" (`ChatDemo.tsx:50`, `.slice(-10)`) is client-side and trivially bypassed by calling the endpoint directly. No rate-limit package, `middleware.ts`, or `vercel.json` exists anywhere in the repo.
**Impact:** anyone who finds the public URL can script unlimited billed completions against the owner's Anthropic account.
**Fix:** server-side rate limiting (IP-keyed) plus a hard request/spend ceiling; consider a lightweight challenge for the public demo.
**Acceptance test:** the (N+1)th request within a window returns 429 with zero additional upstream API calls.

### H-6. DOM XSS via a 4-line regex "renderer" feeding `dangerouslySetInnerHTML`
**Domain:** frontend-security (FE-2) · **Status:** verified
`ChatDemo.tsx:91-97`'s `renderMessage()` does 4 regex substitutions (bold/italic/code/newline) with **no HTML-escaping** before or after, rendered via `dangerouslySetInnerHTML` for both user and assistant messages. No sanitizer (`dompurify`) or safe renderer (`react-markdown`) is a dependency.
**Impact:** a user typing `<img src=x onerror=alert(1)>` executes it in their own tab immediately (self-XSS today); once any auth/session state is added, an attacker who gets the assistant to echo a crafted string (a classic prompt-injection pattern) executes in the victim's browser.
**Fix:** replace with `react-markdown` (renders to React elements, no raw HTML) or sanitize with `DOMPurify` before setting `__html`; add a CSP as defense-in-depth.
**Acceptance test:** rendering `<img src=x onerror="window.__xss=true">` never sets `window.__xss` and no live `onerror` attribute reaches the DOM.

### H-7. Unparameterized SQL construction in the reachable retrieval tool, plus a latent injection-shaped pattern in dead code
**Domains:** backend-science (SCI-2 detail), rag-data (RAG-8) · **Status:** verified
`agentic_workflow/tools/sql_executor_tool.py` builds WHERE clauses via f-string interpolation in multiple methods — most clearly `:150,152`, `f"p.profile_date >= '{start_date}'"` with no escaping, where `start_date`/`end_date` are the exact parameters `planner_agent.py`'s `_parse_time_period()` stub is designed to eventually populate from free text. Contrast with `scripts/data/ingestion.py`/`scripts/apps/app1.py`, which already use real `:name` bind parameters elsewhere in the repo — proof the safe pattern is known, just not applied consistently. `get_profiles_by_region_and_time` (the worst offender) is currently unreachable dead code (referenced only in an unused capabilities dict), so today's exploitability is low — but it sits directly next to the stub that's designed to feed it.
**Fix:** convert every dynamic query in this file to SQLAlchemy bound parameters, uniformly, not only where currently reachable.
**Acceptance test:** a bandit/static SQL-injection scan (e.g. rule B608) over this file reports zero raw string-built SQL.

### H-8. Chroma collections carry no real embedding-function/schema provenance
**Domain:** rag-data (RAG-4), corroborated by lead's independent check · **Status:** verified
`collection.metadata` is `None` for both collections; `configuration_json.embedding_function` reports `{"name":"default",...}` for both — provably synthetic, since Chroma's real default embedder is fixed at 384 dimensions and cannot have produced the 768-dim collection. Real embeddings are injected externally via `embeddings=` (correctly bypassing Chroma's embedder abstraction on both ingest and query paths today), but nothing stops a future `.query(query_texts=...)` call from silently invoking the wrong embedder.
**Fix:** stamp real `embedding_model`/`schema_version`/`hnsw:space` at both collection- and record-level for any new collection; add an application-level guard that refuses to query/insert on a tag mismatch.
**Acceptance test:** a deliberately mismatched embedding-model tag raises before reaching Chroma.

### H-9. Two diverged Chroma ingestion scripts target the same collection; one has the wrong schema
**Domain:** rag-data (RAG-7) · **Status:** verified
`scripts/database/populate.py` builds 2-key metadata (no `cycle_number`) that does **not** match the live collection; `scripts/vector_store/chrom.py` builds the 3-key metadata that matches every sampled live record. Both unconditionally `delete_collection()` + `create_collection()` against the same name.
**Impact:** running the "wrong" script silently destroys the current schema and replaces it with an incompatible one — a Chroma-side sibling to C-4.
**Fix:** retire `populate.py`'s Chroma-writing half (keep only its Postgres role, pending C-4's fix); add a schema-version guard so a mismatched re-run fails loudly.
**Acceptance test:** only one code path can call `delete_collection`/`create_collection` for a given name; enforced by a static check.

### H-10. Full raw user queries logged verbatim to a git-tracked log file
**Domain:** quality-devops (OPS-13) · **Status:** verified — already realized, not just theoretical
`retriever_tool.py:73` and `workflow_engine.py:308-324` log complete, untruncated query text and a raw XAI dict (contrast with `workflow_engine.py:72`, which *does* truncate — proving the safe pattern was known but applied inconsistently). The committed `agentic_workflow/agentic_workflow.log` (381 lines) already contains real query text today.
**Fix:** redact/truncate free-text logging consistently; stop tracking `*.log` in git (see C-2).
**Acceptance test:** a canary string run through the pipeline never appears untruncated in a fresh log file.

### H-11. Two parallel visualization pipelines; one is fully computed and then discarded
**Domain:** backend-science (SCI-5) · **Status:** verified
`VisualizerTool` (Matplotlib, base64 PNG) and `PlottingAgent` (Plotly) both run in the live pipeline and overlap heavily in what they render (including a **third**, independently-drifted density formula used only for `VisualizerTool`'s T-S contour lines). `WorkflowEngine.process_query()`'s returned dict never includes the `"visualizations"` key the Matplotlib path populates — confirmed dead on all three shipped UIs (CLI, `main.py`, Streamlit all read `.get("visualizations", [])` → always `[]`).
**Fix:** standardize on the Plotly path (already reaches the UI end-to-end); delete or explicitly bridge the Matplotlib path.
**Acceptance test:** for a query whose plan includes a visualizer step, the final response's visualization field is non-empty when that step succeeded — false today.

### H-12. `agentic_workflow/chroma_db/` is orphaned and its own README contradicts the real code path
**Domains:** rag-data (RAG-11), architect (ARCH-4) · **Status:** verified
Confirmed via direct sqlite read: all tables (`collections`/`segments`/`embeddings`) have 0 rows, but all 16/16 schema migrations are applied — a correctly-initialized, never-populated store, not a version-compat artifact. `agentic_workflow/README.md:57` documents `./chroma_db` (i.e. inside `agentic_workflow/`); the actual code (`config.py:27`) and every other reference in the repo resolve to the **root** `chroma_db/` instead.
**Fix:** correct the README; remove this path from git once explicitly approved (do not delete during this audit).
**Acceptance test:** only one `chroma_db/` exists in the repo, and every doc/code reference agrees.

### H-13. Chroma path resolution is CWD-dependent, not anchored to the file/config location
**Domain:** quality-devops (OPS-19) · **Status:** verified
`ChromaDBConfig.db_path = "../chroma_db"` resolves against the process's working directory, not the file's location. It happens to resolve correctly only when launched exactly as documented (`cd agentic_workflow && python main.py`); a different CWD (an IDE run config, `streamlit run` from repo root, a future container `WORKDIR`) silently connects to the near-empty orphaned store (H-12) instead — with no error, just confusingly few/no results.
**Fix:** anchor the path via `Path(__file__).resolve()` or an absolute env-var.
**Acceptance test:** `main.py` invoked from two different working directories reports the same `collection.count()`.

### H-14. Disabled TLS certificate verification when downloading ARGO data
**Domain:** backend-science (SCI-6 sub-finding) · **Status:** verified
`scripts/data/scrapper.py:13-14,35,48` and `scripts/analysis/s1.py:19-20,41,55` call `requests.get(..., verify=False)` (after suppressing the resulting warning) over HTTPS.
**Fix:** remove `verify=False`; if a specific endpoint's certificate is genuinely problematic, pin its CA explicitly instead of disabling verification globally.
**Acceptance test:** `grep -rn "verify=False" scripts/` returns nothing.

---

## Medium

| ID | Finding | Domain(s) | Evidence |
|---|---|---|---|
| M-1 | No CI pipeline at all — no `.github/workflows` anywhere | quality-devops (OPS-1) | confirmed absent |
| M-2 | No dependency manifest for `scripts/` (24 files import `cartopy`/`xgboost`/`sklearn`/`xarray`/`tqdm`/`sentence_transformers`, none declared anywhere) | quality-devops (OPS-3), architect (ARCH-8) | `scripts/` has zero requirements file |
| M-3 | No JS lockfile in `web/`; deps mostly unpinned (`^` ranges) | quality-devops (OPS-4), architect (ARCH-6), frontend-security (FE-7) | confirmed absent |
| M-4 | Zero automated tests anywhere; `scripts/test.py`/`test1.py` are not tests (no assert/pytest, hardcoded macOS paths `/Users/admin/...`, blocking `plt.show()`) | quality-devops (OPS-5), architect (ARCH-8), backend-science (SCI-7 notes the circular import would block naive test-adding anyway) | verified by full read |
| M-5 | Every Python dependency is floor-only (`>=`), zero pins/lock; flagged (not yet proven) compatibility risk for `chromadb`, `psycopg2-binary`, `kaleido` against the installed Python 3.13.6 | quality-devops (OPS-6) | needs an empirical install check, not assumed |
| M-6 | Duplicated/dead Python deps: `pytest`+`pytest-cov` with no tests to run; `sphinx`+`sphinx-rtd-theme` with no docs anywhere | quality-devops (OPS-7) | confirmed absent consumers |
| M-7 | Import-time filesystem side effects: `config.py`'s module-level `Config()` and `logger.py`'s module-level `XAILogger()` open log file handlers on *any* import, at a bare relative path | architect (ARCH-5) | reproduced — a stray log file appears wherever CWD happens to be |
| M-8 | Missing `typecheck`/`test` npm scripts despite `strict: true` TypeScript and a real API route | quality-devops (OPS-9) | `web/package.json` confirmed |
| M-9 | No committed ESLint config despite `"lint": "next lint"` being wired up (interactive-prompt risk in CI) | quality-devops (OPS-10) | confirmed absent |
| M-10 | `PlottingAgent` silently missing from `agents/__init__.py`'s exports despite being a real, actively-used 4th agent | architect (ARCH-12) | reproduced import difference |
| M-11 | Legacy `/api/embeddings` used instead of current `/api/embed`; ingestion makes ~4,900 sequential HTTP calls instead of batching | rag-data (RAG-10) | still functional on Ollama 0.17.7 today, but a real cost at v2 scale |
| M-12 | No request schema validation on `/api/chat` (TS cast is compile-time only; no zod/manual guard, no message-count/size caps) | frontend-security (FE-3) | confirmed |
| M-13 | Chat widget accessibility gaps: no `aria-label` on input/send button, no `aria-live` region for new replies, weak focus indicator, icon-only nav link with `hidden sm:inline` removing its only text at small widths, caption text below 4.5:1 contrast in two spots | frontend-security (FE-5) | verified structurally; some `.glass`-background contrast estimates flagged as assumption pending a rendered check |
| M-14 | Region config duplicated in two places that can drift (`config.py: SYSTEM_CONFIG.regions` vs. `planner_agent.py: known_regions`) | backend-science (SCI-4 note) | confirmed |
| M-15 | Undocumented PostGIS dependency — both DB setup scripts require it, no README mentions it | quality-devops (OPS-17) | confirmed |
| M-16 | `argo_data_dump.txt` (62 MB, tracked) is never referenced by any setup instruction — unclear how to use it | quality-devops (OPS-18) | confirmed |

## Low / Informational

| ID | Finding | Domain(s) |
|---|---|---|
| L-1 | `plots/` and `web/public/plots/` are 100% byte-identical (verified 3 ways: git blob hash, SHA256, filesize) — 2.2 MB paid twice; README already references the two paths inconsistently | architect (ARCH-7) |
| L-2 | `.DS_Store` tracked at repo root and in `agentic_workflow/`, not gitignored | architect (ARCH-9), quality-devops | 
| L-3 | Hardcoded/fabricated "live" statistics in `page.tsx`/`route.ts` (4,922 profiles, R²=0.97, etc.) not fetched from any backend | frontend-security (FE-4) |
| L-4 | README's Vercel section doesn't state the deployed demo has no connection to Postgres/Chroma/Ollama (the correct disclaimer exists only inside the running page itself, `page.tsx:298`) | frontend-security (FE-6), rag-data (RAG-13) |
| L-5 | Presentation filename (`... (1).pptx`, with space) doesn't match its near-miss `.gitignore` entry | architect (ARCH-11) |
| L-6 | Binary Chroma vector-store files committed directly to git; will worsen at v2 scale/dimensionality | rag-data (RAG-12) |
| L-7 | `l2` distance metric confirmed (not cosine) on both existing collections; `similarity = 1 - distance` is invalid but currently dead code (zero consumers found) | rag-data (RAG-3) |
| L-8 | Potential-density calculation is a simplified linear approximation with a **dead `reference_pressure` parameter** (verified identical output regardless of the argument), and a third, independently-drifted density formula exists in `visualizer_tool.py` for T-S contour lines | backend-science (SCI-3) |

## Confirmed good / no defect found

- All source under `agentic_workflow/` and `scripts/` compiles cleanly under Python 3.13.6 (`py_compile`/`compileall`, zero errors) — OPS-8.
- No secrets have ever been committed in `web/`'s history; `ANTHROPIC_API_KEY` is correctly server-side only — RAG-13.
- `agentic_workflow/requirements.txt` is internally consistent with its own imports (no undeclared-but-used packages) — architect Task 2.
- `web/package.json` dependencies are all actually used; nothing declared-but-unused — architect Task 2.

## Assumptions flagged for empirical follow-up (not yet proven either way)

- Whether `chromadb`, `psycopg2-binary`, and `kaleido`'s currently-floor-pinned versions actually install/import cleanly under Python 3.13.6 (OPS-6) — requires a real `pip install` attempt.
- Exact rendered-page color-contrast ratios on the semi-transparent `.glass` UI backgrounds (FE-5) — the two flat-background failures are measured exactly; the blended ones are estimated.
- Whether any Next.js 14.2.5 security advisory applies to this app's specific usage (FE-7) — no `middleware.ts`/Server Actions narrows exposure but wasn't fully ruled out without running `npm audit`.
