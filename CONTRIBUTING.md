# Contributing to django-sysconfig

Thank you for your interest in contributing! This guide covers everything you need to get a working development environment and submit changes.

---

## Prerequisites

- Python 3.11+
- Git

No database server, Docker, or external services required.

---

## Local setup

```bash
# 1. Clone the repository
git clone git@github.com:krishnamodepalli/django-sysconfig.git
cd django-sysconfig

# 2. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3. Install the package in editable mode with dev dependencies
pip install -e ".[dev]"

# 4. Install pre-commit hooks (runs black + ruff automatically on every commit)
pre-commit install
```

---

## Running the test suite

```bash
pytest
```

Tests use an in-memory SQLite database — no setup required. All 115+ tests should pass.

---

## Running the dev server

You can run a local Django dev server using the provided `settings_dev.py` to manually test the admin UI and any configured apps.

```bash
# Apply migrations (creates db.sqlite3 in the repo root)
DJANGO_SETTINGS_MODULE=settings_dev django-admin migrate

# Create a superuser
DJANGO_SETTINGS_MODULE=settings_dev django-admin createsuperuser

# Start the dev server
DJANGO_SETTINGS_MODULE=settings_dev django-admin runserver
```

Then visit:

| URL | What you see |
|---|---|
| http://127.0.0.1:8000/admin/ | Django admin |
| http://127.0.0.1:8000/admin/config/ | Config app list |
| http://127.0.0.1:8000/admin/config/demo/ | Demo config with all field types |

The dev server uses SQLite (`db.sqlite3` in the repo root, gitignored) — no Docker or Postgres needed.

> **Tip:** The dev server watches for file changes automatically. Edits to `django_sysconfig/` are reflected immediately without a restart.

---

## Project structure

```
django_sysconfig/   # The installable package (what gets published to PyPI)
demo/               # Local demo app for manual dev testing (not packaged)
tests/              # Automated test suite (pytest)
settings_dev.py     # Django settings for the dev server
urls_dev.py         # URL config for the dev server
```

---

## Code style

This project uses **black** for formatting and **ruff** for linting. Both run automatically via pre-commit on every commit. To run them manually:

```bash
black .
ruff check .
```

---

## Commit messages

This project follows [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <short description>
```

Common types: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`, `ci`, `perf`, `style`

Examples:
- `feat(registry): add support for nested sections`
- `fix(accessor): always raise for invalid paths`
- `docs: update README validator reference`

---

## Submitting a pull request

1. Create a branch: `git checkout -b fix/my-fix` or `feat/my-feature`
2. Make your changes and ensure all tests pass: `pytest`
3. Push and open a PR against `master`
4. Fill in the PR template — it will be pre-populated when you open the PR on GitHub

---

## Reporting issues

Open an issue on [GitHub Issues](https://github.com/krishnamodepalli/django-sysconfig/issues). Please include:
- Django and Python versions
- A minimal reproduction case
- Expected vs actual behaviour
