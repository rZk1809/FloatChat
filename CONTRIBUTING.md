# Contributing to FloatChat

Thank you for your interest in contributing to FloatChat!

## Development setup

### Web frontend (Next.js)

```bash
cd web
npm install
npm run dev          # http://localhost:3000
npm run lint         # ESLint
npm run typecheck    # TypeScript
npm test             # Vitest unit tests
npm run build        # Production build
```

Copy `.env.example` to `web/.env.local` and add your `ANTHROPIC_API_KEY`.

### Python backend

Requirements: Python 3.11+, PostgreSQL 14+, Ollama running locally.

```bash
pip install -e ".[dev]"
# Configure .env or export variables from .env.example

# Run the CLI
python -m agentic_workflow.main

# Run the Streamlit UI
streamlit run agentic_workflow/streamlit_app.py

# Run the FastAPI server
uvicorn agentic_workflow.api:app --reload --port 8000

# Tests
pytest tests/ -v

# Lint
ruff check agentic_workflow/ tests/
mypy agentic_workflow/ --ignore-missing-imports
```

## Branch naming

| Type | Pattern |
|------|---------|
| Feature | `feat/<short-description>` |
| Bug fix | `fix/<short-description>` |
| Refactor | `refactor/<short-description>` |
| Tests | `test/<short-description>` |
| Docs | `docs/<short-description>` |

## Commit conventions

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(chat): add message timestamps to ChatDemo
fix(api): handle rate-limit header when Retry-After is missing
test(planner): add unit test for region extraction
docs: update README with Docker setup instructions
```

## Pull Request process

1. Open an issue first for non-trivial changes.
2. Fork the repo and create a branch from `main`.
3. Ensure all checks pass: lint, typecheck, tests, build.
4. Fill in the PR template.
5. Request a review from `@rZk1809`.

## Code style

- **TypeScript/React**: ESLint + Prettier (via `next lint`). No `any` unless unavoidable.
- **Python**: Ruff for linting and formatting. Type annotations required for all public functions.
- **No unnecessary comments**: Code should speak for itself. Add a comment only when the *why* is non-obvious.
- **No half-finished features**: Every PR should be a complete, working unit of change.

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).
