# CHANGELOG


## v1.1.0 (2026-05-14)

### Documentation

- Update docs for feat/fields-shorthand branch
  ([#99](https://github.com/krishnamodepalli/django-sysconfig/pull/99),
  [`7e75e6e`](https://github.com/krishnamodepalli/django-sysconfig/commit/7e75e6ecfdcf1542a27ba464a125ef52b4170007))

### Features

- Add `--dry-run` flag for `config set` sub-command
  ([#98](https://github.com/krishnamodepalli/django-sysconfig/pull/98),
  [`3f2fb0a`](https://github.com/krishnamodepalli/django-sysconfig/commit/3f2fb0a8309737b4d871ea6fe526dc4bacef666e))

* feat: Add --dry-run flag for `config set` sub-command

* docs: Update docs for `config set` command with `--dry-run` flag

* tests: Update tests for `config set` subcommand `--dry-run` flag

* tests: Fix tests to correctly set dry_run for config_set dry-run tests

* refactor: Use `set_rollback` instead of throwing TransactionManagementError

changes: - The commands `config set` and `config import` both have a `--dry-run` flag. To catch this
  flag, the TransactionManagementError is previously used. From Django 4.2
  `transaction.set_rollback()` is preferred for the same behavior, we shifted to that in this commit

* tests: refactor test_case `test_dry_run_doesnt_save` in test_cmd_set.py

- **fields**: Add typed field shorthands
  ([#86](https://github.com/krishnamodepalli/django-sysconfig/pull/86),
  [`6b2403f`](https://github.com/krishnamodepalli/django-sysconfig/commit/6b2403f32ebb6ea50ba3b0bcd7a40c357cb04647))

* feat(fields): add typed field shorthands using functools.partial

* feat(init): re-export Section and register_config from package root

* style(fields): add __all__ to define public API surface

* refactor: add __all__ to public API modules

* refactor: Add `config` and all exceptions in the __init__.py

* chore: Add fields and validators in __init__.py:__all__

* docs: Update docs for shorthand fields

* docs: fix typos in docs

* docs: Update docs according to the fields shorthand


## v1.0.2 (2026-05-07)

### Bug Fixes

- **accessor**: Let exists() propagate InvalidPathError
  ([#89](https://github.com/krishnamodepalli/django-sysconfig/pull/89),
  [`aef108d`](https://github.com/krishnamodepalli/django-sysconfig/commit/aef108db9dfc93a328330411239189051c05c81d))

* fix(accessor): let exists() propagate InvalidPathError

Closes #71.

ConfigAccessor.exists() previously caught InvalidPathError alongside AppNotFoundError and
  FieldNotFoundError, returning False for all three. That hid programmer errors: a malformed path
  (wrong number of segments) was indistinguishable from a well-formed path whose app/section/field
  simply was not registered.

- `config.exists("myapp.general")` two segments, programmer error -
  `config.exists("myapp.general.missing")` three segments, just not registered

Both returned False with no way for the caller to tell which.

InvalidPathError is now allowed to propagate, matching the behaviour of get() and set() on malformed
  paths. AppNotFoundError and FieldNotFoundError continue to produce False, so existing lookup-style
  callers keep working.

Tests: the TestExists suite in tests/accessor/test_rest.py previously asserted that exists() never
  raises and returned False for every bad path. Those three cases are now asserted to raise
  InvalidPathError, and a new test_well_formed_unknown_path_still_returns_false pins the
  false-not-raise contract for three-segment-but-unregistered paths.

* fix(accessor): tighten _parse_path empty-segment validation

_parse_path and _parse_app_section now reject paths with any empty segment (e.g. "testapp..field",
  ".section.field"), matching the contract that a malformed path is a programmer error. Updates the
  is_set test to expect InvalidPathError instead of False, matching exists()'s propagate-not-swallow
  contract.

---------

Co-authored-by: Matt Van Horn <455140+mvanhorn@users.noreply.github.com>

### Chores

- Add python 3.10 & 3.14 support
  ([#91](https://github.com/krishnamodepalli/django-sysconfig/pull/91),
  [`1bb445e`](https://github.com/krishnamodepalli/django-sysconfig/commit/1bb445e20116229f8c5438d902dd837592672c1f))

- chore: Add support for python 3.10 & 3.14 in pyproject.toml - test: Update test matrix in github
  ci to support py 3.10 & 3.14 - fix: add Python 3.10 compatibility for typing & datetime - chore:
  Update black & ruff base python version to 3.10 - fix: Use 3.10 compatible UTC from datetime -
  docs: Update min python version required from 3.11 to 3.10

- Remove `docs/upgrade` from documentation workflow
  ([`ac5210a`](https://github.com/krishnamodepalli/django-sysconfig/commit/ac5210a1405a0f71460e037c7d7bdd4d7e769acf))

- **CHANGELOG**: Update CHANGELOG for V1.0.1
  ([`005c142`](https://github.com/krishnamodepalli/django-sysconfig/commit/005c1427a6683f2b3933c2b97ef58d9bf5dd279f))

### Continuous Integration

- Allow tests CI actions to run for PRs on master, develop
  ([`188e207`](https://github.com/krishnamodepalli/django-sysconfig/commit/188e20756ec2c6bb30861d109d8ec72774b48c3d))

### Documentation

- Move from custom docs builder to VitePress
  ([#93](https://github.com/krishnamodepalli/django-sysconfig/pull/93),
  [`22d1f6b`](https://github.com/krishnamodepalli/django-sysconfig/commit/22d1f6b5c575098b3d29fea845da2a4286300374))

* docs: migrate to VitePress with full SEO and pnpm

Replaces the custom TypeScript builder with VitePress. Sets up config with cleanUrls, sitemap,
  per-page og/twitter/JSON-LD head injection, local search, PyPI social link, and GitHub edit links.
  Converts blockquote tips/warnings to VitePress containers, moves public assets inside srcDir,
  fixes dead anchor links, and switches the package manager to pnpm.

* chore(docs): remove legacy custom builder artifacts

Deletes the old TypeScript doc engine (src/, assets/, docs.config.js, tsconfig.json, README.md).
  Fixes edit link branch to develop, corrects PyPI icon title, and disables line numbers.

* docs: add missing inline links and uncomment field-types/validators references

* docs: fix broken links, wrong singleton name, cache description, and contributing guide

* docs: fix factual errors found by cross-checking source code

- BooleanFrontendModel serializes to 'true'/'false', not '1'/'0' - config.get(default=...) does not
  suppress unknown-path errors - ConfigValidationError (not ConfigValueError) raised on validation
  failure - registry-api methods corrected to match actual ConfigRegistry API - config.set() updates
  cache, does not invalidate it

* docs: Update docs introduction & defining-config page

* docs: Update docs, fix incorrect documentations, etc

* fix: remove changelog from docs navbar

* ci: setup docs github workflow for vitepress deployment

* fix: Use pnpm instead of npm in docs workflow

* ci: correctly setup pnpm in docs workflow

* chore: update .gitignore and index.md docs page

* refactor(docs): Update footer copyright year in docs

* docs: Fix PR comments on #93

* docs: Fix PR comments 2 on #93

### Refactoring

- **admin**: Replace short_description with @admin.display decorator
  ([#79](https://github.com/krishnamodepalli/django-sysconfig/pull/79),
  [`66e2a76`](https://github.com/krishnamodepalli/django-sysconfig/commit/66e2a76d0ebff6d2c266e7eae41faecbda1c928d))


## v1.0.1 (2026-04-14)

### Bug Fixes

- **registry**: Log warning instead of silently passing DB errors in _ensure_db_records
  ([#77](https://github.com/krishnamodepalli/django-sysconfig/pull/77),
  [`23ca282`](https://github.com/krishnamodepalli/django-sysconfig/commit/23ca2820cf5d4ccc453707d717c8b2e04ed86e69))

* refactor(admin): replace short_description with @admin.display decorator

* fix(registry): log warning instead of silently passing DB errors in _ensure_db_records

* Revert "refactor(admin): replace short_description with @admin.display decorator"

This reverts commit c18daafe438ba7f25850386b9e962c97073d13f2.

### Chores

- Ignore CLAUDE.md
  ([`117be43`](https://github.com/krishnamodepalli/django-sysconfig/commit/117be43d6fa5a70fe84d8897cb48224bc06e81f2))

- Update pyproject to mark the project as Production/Stable
  ([#67](https://github.com/krishnamodepalli/django-sysconfig/pull/67),
  [`7329723`](https://github.com/krishnamodepalli/django-sysconfig/commit/73297237844501b75ab509fde2894024d0f856cd))

### Continuous Integration

- Add explicit permissions blocks to workflows
  ([#81](https://github.com/krishnamodepalli/django-sysconfig/pull/81),
  [`23baba1`](https://github.com/krishnamodepalli/django-sysconfig/commit/23baba1d0393b0397220bf2ed02e770abab0f8f9))

### Documentation

- Improve and fix docs, README, and community files
  ([#66](https://github.com/krishnamodepalli/django-sysconfig/pull/66),
  [`7d55197`](https://github.com/krishnamodepalli/django-sysconfig/commit/7d55197e5fb9d5032407efda54f6e596f42b8f60))

* docs: remove Magento references, fix broken links, slim README

- Replace 'Magento-style' with 'schema-driven, database-backed runtime configuration' across
  pyproject.toml, docs.config.js, index.md, introduction.md - Slim README down to badge + GIF +
  minimal install + link to docs - Fix broken /cli/management-commands slug (plural) →
  management-command in encryption.md and on-save-callbacks.md - Replace dead reference/ links in
  getting-started.md with live guide links

* docs: fix the navigation issues with sidebar and links

* docs: Improve docs, update README

* docs: Update CONTRIBUTING.md file

* chore: Add issue templates for github issues

* docs: Update pyproject.toml with Documentation & Changelog URLs

* docs: Remove non-existing pages in documentation

* docs: Improve docs generation code

- Restructure CONTRIBUTING.md and add Security section to README
  ([#84](https://github.com/krishnamodepalli/django-sysconfig/pull/84),
  [`7c00a10`](https://github.com/krishnamodepalli/django-sysconfig/commit/7c00a102118c5a3849809de907c237c8d76c5c21))

* docs(contribution): Improve `CONTRIBUTING.md`

* docs(contributing): Specify to assign a maintainer as reviewer in PRs

* docs(contributing): clarify PR template usage and reviewer assignment

* docs(contributing): use GitHub Security Advisories for vulnerability reporting

* docs(contributing): Update CONTRIBUTING.md

* docs: Improve README & CONTRIBUTING files

- **contributing**: Clarify issue assignment workflow and PR guidelines
  ([#80](https://github.com/krishnamodepalli/django-sysconfig/pull/80),
  [`3d52570`](https://github.com/krishnamodepalli/django-sysconfig/commit/3d525701168fb9b7cdbc671da19c2a071abbeaab))

- Specify to assign a maintainer as reviewer in PRs - Clarify PR template usage and reviewer
  assignment - Add GitHub Security Advisories for vulnerability reporting

### Refactoring

- **registry**: Remove redundant __init_subclass__ from Section
  ([#78](https://github.com/krishnamodepalli/django-sysconfig/pull/78),
  [`4dfacd8`](https://github.com/krishnamodepalli/django-sysconfig/commit/4dfacd81d9e22b0045fa61acb73f8f36ef213530))

* refactor(admin): replace short_description with @admin.display decorator

* refactor(registry): remove redundant __init_subclass__ from Section, rely solely on SectionMeta

* Revert "refactor(admin): replace short_description with @admin.display decorator"

This reverts commit c18daafe438ba7f25850386b9e962c97073d13f2.


## v1.0.0 (2026-03-25)

### Bug Fixes

- **registry**: Enforce snake_case naming and consolidate to dot notation paths
  ([#65](https://github.com/krishnamodepalli/django-sysconfig/pull/65),
  [`3dd2c4a`](https://github.com/krishnamodepalli/django-sysconfig/commit/3dd2c4afce1289475083cabfd122379ce7bfc6f3))

- fix: use snake_case consistency for app, sections, fields in registry - fix: move slash notation
  for path to completely dot notation - test: Update accessor tests for snake_case sections in
  registry - fix(tests): remove redundant _ensure_db_records call in isolate_registry fixture

register() already calls _ensure_db_records internally. The manual second call was a no-op
  (get_or_create is idempotent) but wasted 8 DB queries per test. Also removed the now-unused
  AppConfigDefinition import.

- test(registry): Add tests for registry

### Documentation

- First draft of the documentation site
  ([#57](https://github.com/krishnamodepalli/django-sysconfig/pull/57),
  [`ffb50b3`](https://github.com/krishnamodepalli/django-sysconfig/commit/ffb50b36ec7951ab8014cec0120162251dfb4ae5))

* docs: Claude version docs for `django-sysconfi` app

* style: Set serif font for `<em>` and italics in docs

* docs: Improve & add accurate docs in home, intro, quickstart pages

* docs(engine): Support `<code>` in headings and add title for TOC

* docs: Update docs for getting-started, admin-ui, quickstart

* docs: Update how-it-works page

* docs: Update defining-config and reading-writing pages

* docs: Update reading-writing page

* docs: Update admin-ui page

* docs: Update encryption page

* docs: Update caching page

* docs: Update on-save-callbacks page

* docs: Show only required pages in the documentation for now

* docs: Improve UI, UX for sidebar, search bar, etc

* docs: refactor md files and remove un-wanted horizontal lines

* docs: Set default collapsible state as closed and open collapsible on page change

* docs: Add images and fix typos and minor miskates in docs

* docs: Update README

* docs: Add docs page for management command

* docs: Fix minor mistakes and references

* docs: Ref docs page in README, and correct references

* docs(registry): Update docs for the registry in defining-config page

* docs: Add gif for the index page in docs


## v0.3.0 (2026-03-24)

### Bug Fixes

- Set_many() is not atomic — partial writes on failure
  ([#58](https://github.com/krishnamodepalli/django-sysconfig/pull/58),
  [`db7f6a9`](https://github.com/krishnamodepalli/django-sysconfig/commit/db7f6a955e0bc2cbac8f19cef052d70d1f4dc409))

* fix(accessor):importing the callable module from collections * tests: Add tests for accessor
  config

- **accessor**: Check for non-empty values in `accessor.is_set` method
  ([#53](https://github.com/krishnamodepalli/django-sysconfig/pull/53),
  [`ec70975`](https://github.com/krishnamodepalli/django-sysconfig/commit/ec70975509302c63277f4fb1429c5b5e3b676372))

* fix(accessor): check for non-empty values in `accessor.is_set` method

The is_set() method now verifies that ConfigValue.value is not None and not an empty string, not
  just that the database row exists.

This ensures is_set() correctly distinguishes between "explicitly set to a value" vs "using default
  or empty".

* refactor: Add todo comments for accessor.py to mark some methods as private

* chore: Remove unwanted todos in the accessor

- **encryption**: Is_encrypted() uses an unreliable length heuristic
  ([`88efb54`](https://github.com/krishnamodepalli/django-sysconfig/commit/88efb54ca14a45d859d93e6693693d2fd68df528))

changes: - Now `is_encrypted()` method uses two heuristic, instead of only depending one lenght. -
  Both length and the decoded format starting with `0x80`.

- **validators**: Fix the URLValidator not respecting the schemes provided
  ([#64](https://github.com/krishnamodepalli/django-sysconfig/pull/64),
  [`33239d9`](https://github.com/krishnamodepalli/django-sysconfig/commit/33239d9fc069c52bee942868f907a35dc1561ed9))

* fix(validators): Fix the URLValidator not respecting the schemes provided

* refactor: Restrict what schemes are allowed in Url Validator

* tests: Update tests for URL validator

* docs: Improve annotation for URL validator

### Chores

- Remove extra migration and modify the initial
  ([`9b7e6af`](https://github.com/krishnamodepalli/django-sysconfig/commit/9b7e6af1962ddda2f03de2c78236d63cfe2ee838))

### Documentation

- **typo**: Correct the models value col help text
  ([`ac63a8c`](https://github.com/krishnamodepalli/django-sysconfig/commit/ac63a8cc77f897fcf2cba59fa8c29ab593950861))

### Features

- Add `skip_on_save_callbacks` flag for `set_many` in accessor.
  ([#59](https://github.com/krishnamodepalli/django-sysconfig/pull/59),
  [`a6b102d`](https://github.com/krishnamodepalli/django-sysconfig/commit/a6b102d20106f4adc098608d5c5d43b0a2880812))

* fix(accessor):importing the callable module from collections

* tests: Add tests for accessor config

* feat: Add `skip_on_save_callbacks` flag for `set_many` in accessor.

changes: - This is very helpful for bulk imports and CI environments where we do not want any
  undesired side-effects

* fix(accessor): `set_many` should handle cache_refresh via `on_commit`

changes: Previously, cache invalidation and repopulation were grouped with the on_save callback
  inside a single on_commit handler. This made it unclear that cache refresh and on_save dispatch
  are independent concerns — one is always required, the other is optional.

_set_value_internal now returns two separate callables instead of one: on_commit_cache_refresh and
  on_commit_callback. Both are still registered with transaction.on_commit to ensure cache only
  reflects durable DB state — setting cache before commit would risk serving values from a
  rolled-back transaction.

set_many now conditionally registers on_commit_callback based on skip_on_save_callbacks, so the
  callback is never queued at all when suppressed rather than being queued and silently skipped
  inside the handler.

* test: Add tests for new feature `skip_on_save_callbacks` in `set_many`

* docs(accessor): Improve docstring annotation for `_set_value_internal`

* fix: ensure full cache refresh before on_save callbacks in set_many

changes: Previously, on_commit callbacks were registered per-item in interleaved order: refresh(A) →
  on_save(A) → refresh(B) → on_save(B). Since transaction.on_commit fires in FIFO order, on_save(A)
  could read a stale cached value for B if B was part of the same batch and already cached.

Collect all cache_refresh callbacks first, then register all on_save callbacks, so the entire batch
  cache is guaranteed to be consistent before any on_save hook runs.

---------

Co-authored-by: Shivaram4011 <maddipati.ram2003@gmail.com>

- Make the config views extendable with extra permissions
  ([#55](https://github.com/krishnamodepalli/django-sysconfig/pull/55),
  [`e8a04e8`](https://github.com/krishnamodepalli/django-sysconfig/commit/e8a04e855df6d09a00feb595edd9268843b4920a))

* feat: Make the config views extendable with extra permissions

* fix(views): Redirect to login page if not logged in for config views

changes: - Redirect to login page if an anonymous user tries to access config pages. - Throw errors
  if the user is not a staff or doesn't have specified extra permissions.

- **management**: Config management command (get, set, reset, export, import)
  ([#42](https://github.com/krishnamodepalli/django-sysconfig/pull/42),
  [`c966515`](https://github.com/krishnamodepalli/django-sysconfig/commit/c9665152644986d9d01cb204d297173355e19294))

* feat(management): scaffold config command with subparsers

Adds the management command skeleton for: - get: read a config value by path - set: write a config
  value by path - reset: restore a field to its default (with -f/--force flag to skip confirmation)
  - export: dump config to JSON/YAML (with --output and --batch-size flags) - import: load config
  from JSON/YAML (with --dry-run flag)

No subcommand logic yet — all handlers raise NotImplementedError.

* feat(management): implement get and set subcommands

* feat(accessor,management): add reset() to ConfigAccessor and implement reset subcommand

- ConfigAccessor.reset() removes the DB override and re-primes the cache with the serialized field
  default - Management command reset subcommand prompts for confirmation unless -f/--force is passed

* feat(management): implement export and import subcommands

- Export enumerates registry metadata, batches 100 fields at a time across app boundaries, one
  targeted DB query per a per batch - Secrets are decrypted to plaintext in the export file (warning
  printed) - Decimal values serialised via custom _JSONEncoder - Import accepts --dry-run flag
  (validates paths without writing) - Import is wrapped in transaction.atomic() for all-or-nothing
  behaviour - --output defaults to config_export.json in current working directory

Closes #36

* fix(apps): defer _ensure_db_records to post_migrate signal

Calling _ensure_db_records() from register() triggered DB queries during AppConfig.ready() when
  sysconfig.py files were autodiscovered, producing a RuntimeWarning on every management command
  invocation.

Move DB default-seeding to a post_migrate signal handler so it runs after migrations complete. The
  accessor already falls back to field defaults when no DB row exists, so runtime behaviour is
  unchanged.

* fix(apps,management): fix import name and two handle_set/import bugs

- apps.py: _sync_defaults imported 'registry' which doesn't exist; correct name is 'config_registry'
  - handle_set: used raw path.split('.') which raised ValueError for malformed paths; replaced with
  config._parse_path() so InvalidPathError is raised and caught as ConfigError -> CommandError -
  handle_import: cache was not invalidated when the DB transaction rolled back on validation error;
  now invalidates all cache keys that were written before the rollback so the cache stays consistent

* test(management): add tests for config management command

37 tests covering all five subcommands:

- get: field default, DB value, integer, unknown app/field, invalid path - set:
  string/integer/boolean coercion, validation failure, bad path - reset: --force flag, confirmation
  yes/no, bad path - export: JSON structure, DB values, None for unset fields, secret decryption,
  stderr warning, non-.json extension, bad batch size, specific app, unknown app, no apps registered
  - import: basic import, --dry-run (no save), --dry-run unknown path, non-.json extension, file not
  found, invalid JSON, empty config, atomic rollback on validation error, secret encryption at rest

Also adds tests/conftest.py with: - clean_state (autouse): isolates registry singleton and cache per
  test - registered_config: testapp with General + Secrets sections

* fix(accessor):importing the callable module from collections

* refactor: Refactor config command

* tests: Add tests for accessor config

* feat: Add `skip_on_save_callbacks` flag for `set_many` in accessor.

changes: - This is very helpful for bulk imports and CI environments where we do not want any
  undesired side-effects

* fix(accessor): `set_many` should handle cache_refresh via `on_commit`

changes: Previously, cache invalidation and repopulation were grouped with the on_save callback
  inside a single on_commit handler. This made it unclear that cache refresh and on_save dispatch
  are independent concerns — one is always required, the other is optional.

_set_value_internal now returns two separate callables instead of one: on_commit_cache_refresh and
  on_commit_callback. Both are still registered with transaction.on_commit to ensure cache only
  reflects durable DB state — setting cache before commit would risk serving values from a
  rolled-back transaction.

set_many now conditionally registers on_commit_callback based on skip_on_save_callbacks, so the
  callback is never queued at all when suppressed rather than being queued and silently skipped
  inside the handler.

* test: Add tests for new feature `skip_on_save_callbacks` in `set_many`

* docs(accessor): Improve docstring annotation for `_set_value_internal`

* Revert "test(management): add tests for config management command"

This reverts commit 85db9f3aa237adaa0c9de8ac4bfdcb266fd6a9c9.

* refactor: Use the in-built `set_many` method form accessor in command

changes: Previously, the import command is depending on manual transactions and rollbacks. This was
  already implemented in accessor. So directly using it instead of large chunks of duplicated and
  bad code

* fix: Fix the reset method in accessor

changes: - `reset()` method is deleting the existing row, and invalidating the cache previously.
  Modified it to just set the value for that field to the default value.

* fix(command): Hide the changed values with `config set` command

changes: - Could expose secrets if we log or print the values after setting a config from command.
  Removed the value from the log statement.

* tests: Add tests for the management command

* test: Modify validator tests from unittests to pytest

* chore: Add pyproject configuraiton for pytest

* refactor: Use config.all() instead of DB queries in the export command

* test(command): Adjust (and remove unwanted) tests for export command

* Revert "fix(apps): defer _ensure_db_records to post_migrate signal"

This reverts commit 108acabc45aaba784b71ce682fc5f52ccbb235f7.

* tests: Remove unnescessary print statements

* feat(management): harden import command with structure validation, real dry-run, and secure export
  permissions

changes: - Validate the nested JSON structure before iterating, with clear error messages pointing
  to the exact malformed app, section, or field key. - Replace the shallow dry-run exists() check
  with a full set_many() call inside a transaction that is always rolled back. Validators, coercion,
  and serialization now run on dry-run, so failures are caught before any real write. - Tighten
  export file permissions to 0600 so plaintext secrets are not readable by other users on shared
  systems.

* test: Update tests for modified management command

---------

Co-authored-by: Shivaram4011 <maddipati.ram2003@gmail.com>

Co-authored-by: Miles Mace <169963839+milesmace@users.noreply.github.com>


## v0.2.0 (2026-03-15)

### Bug Fixes

- **docs**: Support deployment path prefixes
  ([`9928ca2`](https://github.com/krishnamodepalli/django-sysconfig/commit/9928ca2f668ddc3974ac5c325417883109c21eb5))

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>

### Continuous Integration

- **docs**: Remove fix/docs-pages-path-prefix branch to trigger docs generation
  ([`b72c8b8`](https://github.com/krishnamodepalli/django-sysconfig/commit/b72c8b8ce01f16f7a3ab6609e7d4ce0c5c13a0f0))

- **docs**: Run workflow on fix branch
  ([`2c90fc6`](https://github.com/krishnamodepalli/django-sysconfig/commit/2c90fc652ab99338ba5e05a7dae64988ca6717a0))

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>

### Features

- **docs**: Generate SEO metadata artifacts
  ([`219e29f`](https://github.com/krishnamodepalli/django-sysconfig/commit/219e29f6582e65e10692cd289f0cb06f1c970c20))

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>

### Refactoring

- **frontend_models**: Close all input tags used in `frontend_models`
  ([`43f8727`](https://github.com/krishnamodepalli/django-sysconfig/commit/43f87272adac5390b74c9b0fddb7d17b51c9c82f))


## v0.1.0 (2026-03-15)

### Bug Fixes

- **docs**: Add missing highlight.js theme CSS
  ([`e8c4e36`](https://github.com/krishnamodepalli/django-sysconfig/commit/e8c4e3629b10c63199d68183dde4a3df67cd2fac))

### Chores

- Remove accidental config_export.json
  ([`50f4229`](https://github.com/krishnamodepalli/django-sysconfig/commit/50f4229f98e2809280624fc69208b5f81f964dbc))

- **docs**: Automate version extraction from pyproject.toml
  ([`767485b`](https://github.com/krishnamodepalli/django-sysconfig/commit/767485b3d1f654c9df4387bdaaad34f0f49ea3a8))

### Continuous Integration

- **docs**: Remove the test branch from docs workflow
  ([`c36e9bb`](https://github.com/krishnamodepalli/django-sysconfig/commit/c36e9bbeb9b27dd6830a380e5f528302d544d096))

### Features

- **docs**: Add PATH_PREFIX for GitHub Pages and setup deployment workflow
  ([`88b0422`](https://github.com/krishnamodepalli/django-sysconfig/commit/88b0422c31f870f2517666e3a26bd9ed84479ecd))

- **docs**: Implement production minification for HTML, CSS, and JS
  ([`d9cb3a2`](https://github.com/krishnamodepalli/django-sysconfig/commit/d9cb3a22cd77814bb24de8be3671c1352ed88684))

- **docs**: Implement robust scroll-based TOC highlighting
  ([`fe53673`](https://github.com/krishnamodepalli/django-sysconfig/commit/fe53673fe179686c4946b82c93e338b6cc659d58))

- **docs**: Implement static docs generator and initial content for django-sysconfig
  ([`8079623`](https://github.com/krishnamodepalli/django-sysconfig/commit/807962311370c9be07bd12c9ce9837c178b24576))

- **docs**: Overhaul fuzzy search with tokenization, acronyms, and typo tolerance
  ([`1979f43`](https://github.com/krishnamodepalli/django-sysconfig/commit/1979f4353a8151e3de530bccea4f92552697c3a4))

- **docs**: Serve highlight.js theme locally
  ([`890d5d9`](https://github.com/krishnamodepalli/django-sysconfig/commit/890d5d9348cfa241d8a416ae97d230531ea0825b))

### Refactoring

- **docs**: Extract fuzzy search algorithm and improve TOC visibility
  ([`939e525`](https://github.com/krishnamodepalli/django-sysconfig/commit/939e525244b17e7b2168f0d392894e2d933ea56e))

- **docs**: Modularize assets and cleanup legacy build files
  ([`d2ea134`](https://github.com/krishnamodepalli/django-sysconfig/commit/d2ea13421da55f581735afc5adb6a2e7530011b3))

- **docs**: Transform generator into modular TypeScript build engine with SPA navigation
  ([`4f0f764`](https://github.com/krishnamodepalli/django-sysconfig/commit/4f0f764ed782d80ed2b24060cb3bedb6a0bb9576))


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
