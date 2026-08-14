# Security Policy

## Supported versions

| Version | Supported |
|---------|-----------|
| 1.2.x   | ✅ Yes    |
| 1.1.x   | ⚠️ Critical fixes only |
| < 1.1   | ❌ No     |

## Reporting a vulnerability

**Do not open a public GitHub issue for security vulnerabilities.**

Please report security issues by emailing:

> **rohithgankan@gmail.com**

Include:

- A description of the vulnerability and its potential impact
- Steps to reproduce or a proof-of-concept (if available)
- The version(s) affected
- Any suggested mitigations

We aim to acknowledge reports within **48 hours** and provide a resolution timeline within **7 days** for critical issues.

## Security considerations for self-hosting

When deploying FloatChat locally:

- The `ANTHROPIC_API_KEY` must **never** be committed to version control. Use `.env.local` (already in `.gitignore`).
- The PostgreSQL backend runs with **read-only transactions** (`default_transaction_read_only=on`) — no write access is granted to the application user.
- All SQL queries use **parameterized statements** (no string interpolation / SQL injection risk).
- The `/api/chat` endpoint enforces per-IP rate limiting and Zod input validation to prevent abuse.
- `MessageContent.tsx` renders all LLM output through `react-markdown` without `dangerouslySetInnerHTML` or `rehype-raw`, preventing XSS from injected markup.
- The chat API strips `javascript:` URLs from links via `react-markdown`'s built-in `urlTransform`.

## Acknowledgments

Security improvements are tracked in [CHANGELOG.md](CHANGELOG.md).
