# Contributing to django-sysconfig

## Setup

Fork the repo, then:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pre-commit install
```

No database server or Docker required.

---

## Run tests

```bash
pytest
```

Tests use an in-memory SQLite database. All tests should pass before opening a PR.

---

## Dev server

```bash
DJANGO_SETTINGS_MODULE=settings_dev django-admin migrate
DJANGO_SETTINGS_MODULE=settings_dev django-admin createsuperuser
DJANGO_SETTINGS_MODULE=settings_dev django-admin runserver
```

| URL | What you see |
|---|---|
| http://127.0.0.1:8000/ | Demo showcase |
| http://127.0.0.1:8000/admin/config/ | Config app list |
| http://127.0.0.1:8000/admin/config/demo/ | Demo config (all field types) |

---

## Commit messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <short description>
```

Types: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`, `ci`, `perf`, `style`

Examples:
- `feat(registry): add support for nested sections`
- `fix(accessor): always raise for invalid paths`
- `docs: update quickstart`

**PR titles must follow the same format.**

---

## Submitting a PR

1. Branch off `master`: `fix/my-fix` or `feat/my-feature`
2. Make changes, ensure `pytest` passes
3. Open a PR against `master`

---

## Reporting issues

Open an issue on [GitHub Issues](https://github.com/krishnamodepalli/django-sysconfig/issues) with Django/Python versions, a minimal reproduction, and expected vs actual behaviour.
