# CHANGELOG


## v0.0.2 (2026-03-14)

### Bug Fixes

- **registry**: Added Transaction and creates Configvalue records
  ([`4569e97`](https://github.com/krishnamodepalli/django-sysconfig/commit/4569e97f1f5e04a763cfd07804e447d8f64975c9))

### Chores

- Remove unwanted docker-compose file
  ([`8aa3098`](https://github.com/krishnamodepalli/django-sysconfig/commit/8aa309870514a648b3e171ac3477b84bea90c291))

- **demo**: Setup the settings module for the demo app
  ([`94c5482`](https://github.com/krishnamodepalli/django-sysconfig/commit/94c5482ced6f9d4fe91277e8e53e8fa652cd1ffa))

### Continuous Integration

- Setup Python Anywhere App reload with cron schedule on 1, 15 of each month
  ([`5bf3a31`](https://github.com/krishnamodepalli/django-sysconfig/commit/5bf3a31be43362f014bc3ae9293f47dab448d824))

- **demo**: Harden PA reload curl call with timeouts and error logging
  ([`02b0311`](https://github.com/krishnamodepalli/django-sysconfig/commit/02b03112159aee184f693222f68c2565a9dfbf61))

- Add --connect-timeout 10 and --max-time 30 to prevent hanging - Capture response body to a temp
  file instead of discarding with -o /dev/null - Append || true so a curl failure does not leave
  $http_status empty, avoiding 'integer expression expected' in the numeric comparison - Switch
  comparison to string equality (!=) so an empty status is handled - Print both HTTP status and
  response body on failure for easier debugging

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>

### Documentation

- **readme**: Add badges for PyPI, CI, release, license and demo
  ([`25eeb6c`](https://github.com/krishnamodepalli/django-sysconfig/commit/25eeb6ca7e1ab29387559742401ec77da8632e83))

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>

- **README**: Use absolute links in the README
  ([`9278487`](https://github.com/krishnamodepalli/django-sysconfig/commit/9278487d26e2e788ea3c7d591bdf58331ecac7cc))


## v0.0.1 (2026-03-10)

### Bug Fixes

- **accessor**: Always raise for invalid paths; keep default only for missing DB values
  ([`bc78232`](https://github.com/krishnamodepalli/django-sysconfig/commit/bc7823206d6e9ce48319611efeb6922703e633e3))

Previously config.get() suppressed AppNotFoundError/FieldNotFoundError when a default was provided.
  This masked typos and misconfiguration silently.

New behaviour: - Invalid path format, unknown app, or unknown field always raises — no exceptions -
  The 'default' param is only used when the field IS registered but has no value in the database and
  no field-level default is defined (non-required fields) - Removes the _MISSING sentinel — no
  longer needed

Closes #2

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>

- **accessor**: Always run validators when declared, regardless of value
  ([`2b1568f`](https://github.com/krishnamodepalli/django-sysconfig/commit/2b1568fe48ffa66546dd52871a8450598a49d385))

The previous guard skipped validators for optional fields when value was None or empty,
  reintroducing the programmatic-bypass. Each validator is now responsible for handling None/empty
  on its own (NotEmptyValidator raises; length and regex validators skip silently).

- **accessor**: Use sentinel to correctly handle default=None in get()
  ([`aecfe92`](https://github.com/krishnamodepalli/django-sysconfig/commit/aecfe92af1f0a0f06b9adc307b3e6c2666ed9b6b))

Previously, config.get(path, default=None) would re-raise exceptions because the guard checked 'if
  default is not None'. Passing None explicitly is a valid and common pattern, but it was
  indistinguishable from 'no default provided'.

Introduced a module-level _MISSING sentinel so any explicit default value — including None —
  correctly suppresses AppNotFoundError, FieldNotFoundError, and InvalidPathError.

Closes #2

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>

- **accessor**: Validate the value before setting a config value
  ([`98a7c39`](https://github.com/krishnamodepalli/django-sysconfig/commit/98a7c39847f70ac7d8101995df0a06aea4b216b2))

- **frontend-models**: Correct all template paths
  ([`afda1b6`](https://github.com/krishnamodepalli/django-sysconfig/commit/afda1b618d7199c21605df19b2afeb6ca09a6148))

All 7 frontend model classes had template_name pointing to 'config/frontend_models/*' which doesn't
  exist. With APP_DIRS=True, Django resolves paths relative to each app's templates/ directory, so
  the correct prefix is 'django_sysconfig/frontend_models/'.

This was causing TemplateDoesNotExist on every field render, making the entire config admin UI
  broken.

Closes #1

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>

- **templates**: Update config: namespace refs to django_sysconfig:
  ([`a10180c`](https://github.com/krishnamodepalli/django-sysconfig/commit/a10180c9750b36619bda9a8291037541f31fb3a3))

app_config.html and app_list.html still used the old 'config:' URL namespace prefix for template {%
  url %} tags. Updated to match the correct app_name declared in django_sysconfig/urls.py.

- **urls**: Correct namespace mismatch and URL ordering
  ([`3276299`](https://github.com/krishnamodepalli/django-sysconfig/commit/3276299ad484b0c8b7c33b38b6f38e6175542983))

Two related bugs that caused /admin/config/ to 404:

1. URL ordering: path("admin/", admin.site.urls) was listed first, so Django handed admin/config/ to
  the Django admin URL resolver, which has no config/ route -> 404. Fixed by placing the config URL
  pattern before the admin pattern.

2. Namespace mismatch: views.py used redirect("config:...") but django_sysconfig/urls.py declares
  app_name="django_sysconfig". Updated all redirects in views.py to use the correct namespace.

Also updated README.md to document the required URL ordering with an explanatory comment so
  consumers don't hit the same issue.

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>

- **validators**: Skip None in MinLength, MaxLength, RegexValidator
  ([`578eb36`](https://github.com/krishnamodepalli/django-sysconfig/commit/578eb36d90729ea05623f24dfb92cddb4e85d34a))

Presence enforcement is NotEmptyValidator's sole responsibility. When value is None, length and
  regex validators should skip silently rather than raising 'This field is required.' — that caused
  duplicate error messages when a required field had additional validators.

Closes #12

### Chores

- Add pull request template
  ([`5125468`](https://github.com/krishnamodepalli/django-sysconfig/commit/512546879f56a9fcb363b0f2ab468c59d69587f5))

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>

- Apply suggestion from @Copilot
  ([`b1a07e9`](https://github.com/krishnamodepalli/django-sysconfig/commit/b1a07e9a231ece792df0a8f307a144a61e4f94e5))

Co-authored-by: Copilot <175728472+Copilot@users.noreply.github.com>

- Untrack AGENTS.md and add to .gitignore
  ([`b55f3ab`](https://github.com/krishnamodepalli/django-sysconfig/commit/b55f3abe9484a5173e09ce1b8e90058579a93ae1))

AGENTS.md contains local AI agent instructions and should not be version-controlled. Removed from
  tracking with git rm --cached; file is preserved locally.

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>

- Update pyproject.toml
  ([`02e2d73`](https://github.com/krishnamodepalli/django-sysconfig/commit/02e2d73fd602f30eb16b1f166706529b60729609))

- Use plain django-admin instead of .venv/bin/django-admin in settings_dev.py
  ([`7a66557`](https://github.com/krishnamodepalli/django-sysconfig/commit/7a6655700e0e856feb3eb9cba6b0de5e3e5b9e73))

- **demo**: Remove unused MinLengthValidator import
  ([`f348547`](https://github.com/krishnamodepalli/django-sysconfig/commit/f34854738ad3e82365ee66d0743a75f08a47ef2c))

- **dev**: Add demo app for manual UI testing
  ([`5d2a376`](https://github.com/krishnamodepalli/django-sysconfig/commit/5d2a3762b79f732ec081b32148828e786c3e7ce0))

Adds a demo/ Django app to the repository (not packaged — only django_sysconfig/ is included in the
  wheel/sdist).

The demo app registers a realistic config with 4 sections and 15 fields covering every available
  field type: - StringFrontendModel, TextareaFrontendModel - IntegerFrontendModel,
  DecimalFrontendModel - BooleanFrontendModel - SelectFrontendModel (with choices) -
  SecretFrontendModel (encrypted at rest)

Also exercises a range of validators: NotEmptyValidator, EmailValidator, UrlValidator,
  RangeValidator, PortValidator, PositiveValidator, MaxLengthValidator.

To use: start the dev server (see settings_dev.py) and visit http://127.0.0.1:8000/admin/config/

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>

- **dev**: Add venv, Postgres via Docker, and dev settings
  ([`bd69fdb`](https://github.com/krishnamodepalli/django-sysconfig/commit/bd69fdbc71fc3418c2219facb59fbfe9d4027503))

- Add docker-compose.yml with postgres:17-alpine service - Add .env.example documenting required env
  vars - Add settings_dev.py (reads from .env, uses Postgres) - Add urls_dev.py wiring admin +
  django_sysconfig config UI - Add psycopg2-binary and python-dotenv to dev dependencies - Gitignore
  .venv/, .env, and local settings files

To start developing: cp .env.example .env docker compose up -d DJANGO_SETTINGS_MODULE=settings_dev
  .venv/bin/django-admin migrate DJANGO_SETTINGS_MODULE=settings_dev .venv/bin/django-admin
  runserver

Tests still use tests/settings.py with in-memory SQLite (no Docker needed): .venv/bin/pytest

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>

- **dev**: Switch dev server to SQLite, add CONTRIBUTING.md
  ([`bcefd2a`](https://github.com/krishnamodepalli/django-sysconfig/commit/bcefd2a0088b81c3f74ab5806c703b9bc7efaaad))

Removes the Postgres/Docker requirement for local development. SQLite is sufficient for manually
  testing the admin UI and requires zero external setup.

Changes: - settings_dev.py: replaced Postgres DB config with SQLite (db.sqlite3) removed
  python-dotenv loading and os.environ calls added demo app to INSTALLED_APPS (was missing from this
  branch) - pyproject.toml: removed psycopg2-binary and python-dotenv from dev deps; added
  pre-commit>=3.7 - CONTRIBUTING.md: new file documenting local setup, dev server, test suite, code
  style, and PR workflow - README.md: added Contributing section linking to CONTRIBUTING.md

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>

- **release**: Expose __version__ and refine PSR config
  ([`d390f75`](https://github.com/krishnamodepalli/django-sysconfig/commit/d390f7569fe112dd8ded2c851f6273c295166b24))

- Add __version__ = '0.1.0' to django_sysconfig/__init__.py so the version is accessible at import
  time and PSR keeps it in sync - Register version_variables so PSR updates both pyproject.toml and
  __init__.py on each release - Move changelog config to [tool.semantic_release.changelog] (v9
  schema) - Add allowed_tags and default_bump_level = 0 so non-triggering commit types (chore, docs,
  ci, test) do not cut a release - Enable upload_to_vcs_release so built dists are attached to the
  GitHub Release created by PSR

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>

### Continuous Integration

- Add GitHub Actions CI workflow
  ([`c1be761`](https://github.com/krishnamodepalli/django-sysconfig/commit/c1be7610e54a7564fe2cf549079a36d008d4b209))

Runs on every push and on PRs targeting master.

Jobs: - lint: ruff + black --check (Python 3.13) - test: pytest matrix across Python 3.11/3.12/3.13
  and Django 4.2 (LTS) / 5.1 / 5.2 (LTS)

fail-fast is disabled so all matrix combinations run even when one fails.

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>

- Add pre-commit hooks for lint enforcement
  ([`d713d00`](https://github.com/krishnamodepalli/django-sysconfig/commit/d713d007ae4ba90af7a994a84ab39e6bd9e56a36))

Adds .pre-commit-config.yaml with: - pre-commit-hooks: trailing whitespace, EOF fixer,
  yaml/toml/json/merge checks - black: auto-format on commit - ruff: lint + auto-fix on commit
  (exits non-zero if fixes were applied)

Also adds pre-commit>=3.7 to dev dependencies.

Install hooks locally after cloning: pip install -e '.[dev]' pre-commit install

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>

- Setup release ci for automatic versioning & publish to pypi
  ([`89007a3`](https://github.com/krishnamodepalli/django-sysconfig/commit/89007a362ca9afd6b81b56bccc13694ba5321441))

- **release**: Use python-semantic-release for versioning and changelog
  ([`f24cb17`](https://github.com/krishnamodepalli/django-sysconfig/commit/f24cb17c0b244f0890f6a049eeb5d768481e9cf0))

- Replace hand-rolled bump script with python-semantic-release v9 - PSR reads conventional commits
  to determine version bump, updates pyproject.toml, generates CHANGELOG.md, creates a commit + tag,
  and opens a GitHub Release automatically on every push to master - A separate 'publish' job runs
  only when PSR cut a new release and uses pypa/gh-action-pypi-publish with the protected 'pypi'
  environment (Trusted Publisher / OIDC — no API token needed) - Added [tool.semantic_release]
  config to pyproject.toml

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>

- **release**: Use RELEASE_TOKEN instead of GITHUB_TOKEN
  ([`c907f45`](https://github.com/krishnamodepalli/django-sysconfig/commit/c907f45848ea5800ff3145da7279ea53d78e6433))

GITHUB_TOKEN is rejected when pushing to branches with protection rules. RELEASE_TOKEN is a PAT with
  the necessary permissions to push the version bump commit and tag created by
  python-semantic-release.

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>

### Documentation

- Rewrite README with complete validator and field type reference
  ([`f4834ff`](https://github.com/krishnamodepalli/django-sysconfig/commit/f4834ff097f39c699f57b4da2516c6e81e14720e))

- Add table of contents and requirements section - Document all 20 validators across 5 categories
  (presence, string length, pattern, numeric, network/format) - Fix TextAreaFrontendModel typo →
  TextareaFrontendModel - Document all accessor methods including exists() and is_set() - Add
  exceptions reference table - Expand on_save, encryption, and admin UI sections - Add 'How It
  Works' section explaining the full config flow - Add field options and section options reference
  tables - Add examples for SelectFrontendModel choices and DecimalFrontendModel step

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>

### Refactoring

- Validators are refactored to only do one task and not repeat the non-empty check
  ([`ea06d09`](https://github.com/krishnamodepalli/django-sysconfig/commit/ea06d091ab8f3e72dfe00cc7e4cde87dda5ef4e7))

### Testing

- Add new test case for choice validator for None Case
  ([`a2bad42`](https://github.com/krishnamodepalli/django-sysconfig/commit/a2bad420e73bc752130d1b50c5094697b76c8e90))
