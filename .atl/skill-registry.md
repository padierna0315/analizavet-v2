# Skill Registry: analizavet-v2-26deabril

**Generated**: 2026-04-26  
**Project**: analizavet-v2-26deabril  
**Mode**: engram persistence

---

## Auto-Resolved Skills

These skills are automatically loaded based on code context and task type.

### Code Context Triggers

| Extension/Path | Skill | Description |
|---------------|-------|-------------|
| `*.py` | pytest | Python testing patterns |
| `app/core/` | skill-santiago | Santiago's immutable stack rules |
| `app/satellites/web/` | skill-santiago | HTMX + FastAPI rules |

### Task Context Triggers

| Task Type | Skill | Description |
|-----------|-------|-------------|
| `sdd-init` | sdd-init | Initialize SDD context |
| `sdd-explore` | sdd-explore | Explore ideas before changes |
| `sdd-propose` | sdd-propose | Create change proposals |
| `sdd-spec` | sdd-spec | Write specifications |
| `sdd-design` | sdd-design | Technical design |
| `sdd-tasks` | sdd-tasks | Task breakdown |
| `sdd-apply` | sdd-apply | Implement changes |
| `sdd-verify` | sdd-verify | Validate implementation |
| `sdd-archive` | sdd-archive | Archive completed changes |

---

## User Skills Available

| Skill | Location | Description |
|-------|----------|-------------|
| skill-santiago | `~/.config/opencode/skills/skill-santiago/SKILL.md` | Santiago's immutable stack and rules |
| pytest | `~/.config/opencode/skills/pytest/SKILL.md` | Python testing patterns |

---

## Compact Rules

### From skill-santiago (CRITICAL)

**La Bandera - Stack Inmutable:**
- Python 3.11 LTS ONLY (NO 3.13+)
- uv replaces pip+venv completely
- FastAPI (async-first)
- SQLModel (Pydantic + SQLAlchemy 2.0)
- Dynaconf (configuration)
- Dramatiq + Redis (background tasks)
- HTMX + Jinja2 (server-side frontend)
- SSE for real-time (NO WebSockets)
- WeasyPrint for PDFs
- PostgreSQL (production), SQLite (dev)

**Critical Rules:**
1. ALWAYS use `uv run` (never python directly)
2. HTMX buttons MUST have `hx-indicator` + `hx-disabled-elt`
3. FastAPI returns HTML templates (NOT JSON) for HTMX endpoints
4. `static/` folder MUST exist from minute 1
5. BackgroundTasks for <2s tasks, Dramatiq for critical/long tasks
6. Never block terminal (use `> /dev/null 2>&1 &`)
7. Fase 1 = uv, Fase 2 = Docker (only when declared "versión final")

**Architecture Pattern:**
- `app/core/` - Business logic (models, services, validators)
- `app/satellites/` - Adapters (api, hardware, web, persistence)
- `app/satellites/web/static/` - CSS, JS, images (MUST exist)
- `app/satellites/web/templates/` - Jinja2 templates
- `uploads/` - Binary files (NO BLOBs in DB)

### From pytest

**Test Patterns:**
- Use `pytest-asyncio` for async tests
- Use `httpx.AsyncClient` for integration tests
- Fixtures in `conftest.py` at test root
- Use `monkeypatch` for mocking
- Test files: `test_*.py` or `*_test.py`

---

## Project Conventions

### File Extensions
- `.py` - Python source
- `.html` - Jinja2 templates
- `.css` - Stylesheets (in static/)
- `.toml` - Configuration (pyproject.toml, dynaconf)

### Test Commands
```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=app --cov-report=term-missing

# Run specific test
uv run pytest tests/test_models.py::test_patient -v
```

### Quality Commands
```bash
# Lint
uv run ruff check .

# Format
uv run ruff format .

# Type check
uv run mypy app/
```

---

## Dependency on Skills

This registry references skills from:
- `~/.config/opencode/skills/` (user skills)

All SDD phases available and configured for engram persistence.
