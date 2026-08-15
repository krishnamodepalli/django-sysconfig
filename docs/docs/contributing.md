# Contributing

Thanks for your interest in contributing to `django-sysconfig`! Whether you're fixing a bug, adding a feature, improving the docs, or just asking a question — all contributions are welcome.

---

## Ways to contribute

- **Bug reports** — open an issue with a clear description and a minimal reproduction
- **Feature requests** — open an issue explaining the use case and what you'd like to see
- **Bug fixes** — open a pull request linked to an issue
- **New validators or field types** — discuss in an issue first so we can agree on the API
- **Documentation improvements** — typos, unclear explanations, missing examples are all fair game
- **Tests** — improving coverage is always appreciated

---

## Setting up your local environment

### Prerequisites

- Python 3.11 or higher
- [Docker](https://www.docker.com/) and Docker Compose (for running the test database)
- Git

### Clone and install

```bash
git clone https://github.com/krishnamodepalli/django-sysconfig.git
cd django-sysconfig
```

Create a virtual environment and install the package with development dependencies:

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

### Set up the environment

Copy the example environment file and fill in any values if needed:

```bash
cp .env.example .env
```

### Start the development database

```bash
docker-compose up -d
```

This spins up a PostgreSQL instance used by the test suite and the demo app.

### Run migrations

```bash
python manage.py migrate --settings=settings_dev
```

### Start the demo app

```bash
python manage.py runserver --settings=settings_dev
```

Visit `http://127.0.0.1:8000/admin/config/` and log in with your superuser account to see the admin UI with the demo configuration.

---

## Running tests

```bash
pytest
```

To run with coverage:

```bash
pytest --cov=django_sysconfig --cov-report=term-missing
```

Tests live in the `tests/` directory. The project uses a `settings_dev.py` file at the root as the Django settings module for both the test suite and the dev server.

---

## Code style

This project uses:

- **[Ruff](https://docs.astral.sh/ruff/)** for linting and formatting
- **[pre-commit](https://pre-commit.com/)** to run checks before each commit

Install the pre-commit hooks once after cloning:

```bash
pre-commit install
```

After that, linting and formatting run automatically on `git commit`. To run them manually at any time:

```bash
pre-commit run --all-files
```

---

## Project structure

```
django-sysconfig/
├── django_sysconfig/       # The library itself
│   ├── accessor.py         # config object and ConfigAccessor
│   ├── apps.py             # AppConfig and autodiscovery
│   ├── exceptions.py       # Exception hierarchy
│   ├── frontend_models.py  # Built-in field types
│   ├── models.py           # ConfigValue database model
│   ├── registry.py         # ConfigRegistry, Section, Field
│   ├── urls.py             # Admin UI URL patterns
│   ├── validators.py       # Built-in validators
│   └── views.py            # ConfigAppListView, ConfigAppDetailView
├── demo/                   # Demo Django app for local development
├── tests/                  # Test suite
├── settings_dev.py         # Django settings for dev and tests
├── urls_dev.py             # URL config for the dev server
└── pyproject.toml          # Package metadata and dependencies
```

---

## Submitting a pull request

1. **Fork** the repository and create a branch from `master`:
   ```bash
   git checkout -b fix/your-bug-description
   ```

2. **Make your changes.** Write tests for any new behavior. Make sure existing tests still pass.

3. **Run the full test suite** and pre-commit hooks:
   ```bash
   pre-commit run --all-files
   pytest
   ```

4. **Open a pull request** against `master` with a clear description of what you changed and why. Link the relevant issue if one exists.

5. A maintainer will review your PR. Please be responsive to feedback — PRs that go quiet for more than 30 days may be closed.

---

## Commit message style

This project uses [Conventional Commits](https://www.conventionalcommits.org/):

```text
feat(validators): add JsonValidator
fix(accessor): correct cache invalidation on set_many
docs(readme): update installation steps
```

Format: `<type>(<scope>): <description>`. Common types: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`. Scope is optional but encouraged.

---

## Reporting a security vulnerability

Please **do not** open a public issue for security vulnerabilities. Instead, email the maintainer directly. You'll find contact details in the GitHub profile.

---

## Questions?

Open a [GitHub Discussion](https://github.com/krishnamodepalli/django-sysconfig/discussions) or file an issue — questions are welcome. There's no mailing list or Discord at the moment, but that may change as the project grows.
