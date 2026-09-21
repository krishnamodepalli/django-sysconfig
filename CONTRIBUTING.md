# Contributing to django-sysconfig

## Before you start

**Check the issue tracker first.** Someone else may already be working on the same thing — duplicate PRs create unnecessary review overhead for maintainers.

1. Browse [open issues](https://github.com/krishnamodepalli/django-sysconfig/issues). Look for ones labelled `good first issue` if you're new.
2. If an issue exists for what you want to work on, comment on it and ask to be assigned. Wait for a maintainer to assign it to you before starting.
3. If no issue exists, open one first — describe the bug or feature and mention that you'd like to work on it. A maintainer will assign it if it's a good fit.

This ensures no two contributors spend time on the same problem.

---

## Setup

Fork the repo, then:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pre-commit install
```

No database server or Docker required.

**Run the tests:**

```bash
pytest
```

Tests use an in-memory SQLite database. All tests should pass before opening a PR.

**Start the dev server:**

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

## Submitting a PR

1. Cut a branch off `master` — use the convention `feat/typed-accessor` or `fix/accessor-get-fail`
2. Make your changes, ensure `pytest` passes and `pre-commit run --all-files` is clean
3. Commit messages must follow [Conventional Commits](https://www.conventionalcommits.org/):
   ```text
   <type>(<scope>): <short description>
   ```
   Types: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`, `ci`, `perf`, `style`
   — e.g. `fix(accessor): always raise for invalid paths`, `docs: update quickstart`
4. Open a PR against `master` using the PR template — fill in as much as you can:
   - **Required:** Description, `closes #N`, Type of Change, Changes Made, Checklist
   - **Optional:** Django/Python Compatibility (skip if not applicable), Breaking Changes, Additional Notes
5. Assign yourself as the **Assignee** and a maintainer as **Reviewer**
6. Add appropriate labels — e.g. `bug`, `enhancement`, `code-quality`
7. Keep PRs focused — one issue per PR. If you find a related bug while working, open a separate issue for it.

**PR titles must follow the same Conventional Commits format.**

---

## Release process (maintainers)

Releases are fully manual — merging to `master` never triggers a release.

1. Bump the version in `pyproject.toml` (`project.version`) and `django_sysconfig/__init__.py` (`__version__`)
2. Move the `## [Unreleased]` entries in `CHANGELOG.md` under a new `## [X.Y.Z] - YYYY-MM-DD` heading, grouped into `Added`/`Changed`/`Deprecated`/`Removed`/`Fixed`/`Security` per [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
3. Commit: `chore(release): X.Y.Z`
4. Tag: `git tag vX.Y.Z` and `git push origin vX.Y.Z`
5. The tag push triggers the `Release` workflow, which builds and publishes to PyPI

---

## Reporting bugs

Open an issue on [GitHub Issues](https://github.com/krishnamodepalli/django-sysconfig/issues) with:
- Django and Python versions
- A minimal reproduction
- Expected vs actual behaviour

Apply the most relevant label (`bug`, `enhancement`, `good first issue`, etc.) if you have triage access. If not, a maintainer will label it.

---

## Security

Please do **not** open a public issue for security vulnerabilities. Report them privately via [GitHub Security Advisories](https://github.com/krishnamodepalli/django-sysconfig/security/advisories/new).
