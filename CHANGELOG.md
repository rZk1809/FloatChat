# Changelog

All notable changes to FloatChat are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/) and this project uses [Semantic Versioning](https://semver.org/).

---

## [1.2.0] — 2025-08-14

### Added

**Web frontend**
- `GallerySection` client component with interactive category filtering and click-to-expand plot modal (`PlotModal`)
- `CopyButton` component for one-click clipboard copy of assistant messages
- `Toast` notification system with `useToast` hook (success / error / info variants, 3s auto-dismiss)
- `ErrorBoundary` React class component with reset button
- `LoadingSkeleton` components (chat message, plot card, stat card)
- `useLocalStorage` hook with SSR-safe hydration and functional updates
- `useQueryHistory` hook — persists up to 20 past queries with response snippets in localStorage
- `lib/cn.ts` — `clsx` + `tailwind-merge` utility
- `lib/constants.ts` — shared constants (regions, stats, ML metrics, example queries)
- Query history panel in ChatDemo (badge count, remove individual, clear all)
- Suggested follow-up questions appear after each AI response
- Message timestamps on all chat messages
- Conversation export (Markdown / JSON) via download button in ChatDemo
- Character counter in chat input (visible above 70% of limit)
- Chat clear action with toast confirmation

**New API routes**
- `GET /api/health` — service status, version, API key presence
- `GET /api/regions` — ocean region data from constants
- `POST /api/suggestions` — context-aware query suggestions
- `POST /api/feedback` — thumbs-up / thumbs-down rating collection
- `POST /api/export` — chat export in markdown / json / txt

**New pages**
- `/about` — mission, author, dataset stats, technology stack, data sources
- `/docs` — interactive REST API documentation with request/response examples
- `/not-found` — custom 404 page

**Navigation**
- Added "About" and "API Docs" links to main nav and footer
- Footer expanded with About and API Docs buttons

**FAQ section** added to main landing page (6 Q&A about ARGO floats, the system, data coverage)

**Python backend**
- `agentic_workflow/api.py` — FastAPI REST server (`/health`, `/stats`, `/regions`, `/query`)
- `agentic_workflow/utils/cache.py` — TTL in-memory cache for tool results

**CI/CD**
- `.github/workflows/ci.yml` — GitHub Actions CI (web lint + typecheck + test + build; Python ruff + mypy + pytest; matrix: Node 20, Python 3.11/3.12)
- `.github/workflows/deploy.yml` — Vercel production deploy on push to `main`
- `.github/ISSUE_TEMPLATE/bug_report.md`
- `.github/ISSUE_TEMPLATE/feature_request.md`
- `.github/PULL_REQUEST_TEMPLATE.md`

**Documentation**
- `CONTRIBUTING.md` — dev setup, branch naming, commit conventions, PR process
- `SECURITY.md` — vulnerability disclosure policy

**Tests**
- `web/src/hooks/useLocalStorage.test.ts` — 5 unit tests
- `web/src/components/ChatDemo.test.tsx` — 7 integration tests (send, response, error, disabled state)
- `web/src/app/api/health/route.test.ts` — 5 unit tests

### Changed

- `ChatDemo.tsx` — major upgrade: history panel, copy buttons, timestamps, follow-ups, export, character counter
- `page.tsx` — uses `GallerySection` for interactive filtering; FAQ section; updated nav/footer links
- `web/src/app/layout.tsx` — no changes (already has OpenGraph and SEO metadata)

---

## [1.1.0] — 2025-07-20

### Added

- `MessageContent.tsx` — safe markdown renderer (no `dangerouslySetInnerHTML`, no `rehype-raw`)
- `MessageContent.test.tsx` — XSS regression tests for `img onerror` and `javascript:` URLs
- `web/vitest.config.ts` — Vitest + jsdom test configuration
- `web/.eslintrc.json` — ESLint config extending `next/core-web-vitals`
- Rate limiting (20 req/min/IP sliding window) on `/api/chat`
- Zod request validation on `/api/chat`
- `web/package-lock.json` committed for reproducible installs

---

## [1.0.0] — 2025-06-15

### Added

- Initial release for **Smart India Hackathon 2025**
- Multi-agent pipeline: Planner → Executor → Synthesizer → Plotting Agent
- PostgreSQL + ChromaDB hybrid RAG retrieval
- 4,922 ARGO profile embeddings (Bay of Bengal, Arabian Sea, Indian Ocean, Southern Ocean)
- XGBoost temperature prediction, K-Means clustering, Isolation Forest anomaly detection
- 17 generated visualizations (T-S diagrams, depth profiles, geographic maps, PDP plots)
- Streamlit web UI and CLI interface
- Next.js landing page deployed on Vercel
- Claude AI chat demo (`/api/chat`)
