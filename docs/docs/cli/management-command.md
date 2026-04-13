---
title: Management Command
description: CLI reference for django-sysconfig's config management command.
---

# Management Commands

`django-sysconfig` ships a `config` management command for interacting with configuration values directly from the terminal. It's useful for inspecting values, scripting changes, and importing or exporting configuration across environments.

```bash
python manage.py config <subcommand> [options]
```

---

## Get

Print the current value of a single config path.

```bash
python manage.py config get <path>
```

**Arguments**

| Argument | Description |
|---|---|
| `path` | Config path in `app.section.field` format |

**Examples**

```bash
python manage.py config get myapp.general.site_name
# My App

python manage.py config get billing.pricing.tax_rate
# 0.20
```

The value is printed as a string. The underlying Python type (int, bool, Decimal) is not preserved in the output — this command is for inspection, not for piping into other programs.

---

## Set

Set a single config value from the command line.

```bash
python manage.py config set <path> <value>
```

**Arguments**

| Argument | Description |
|---|---|
| `path` | Config path in `app.section.field` format |
| `value` | The value to set, as a string — parsed by the field's frontend model |

**Examples**

```bash
python manage.py config set myapp.general.site_name "Acme Corp"
python manage.py config set myapp.general.max_items 500
python manage.py config set myapp.general.maintenance_mode True
```

The value is parsed and validated through the field's frontend model and validators before being saved. If validation fails, nothing is written and the error is printed.

:::tip
The value is never echoed back in the success message — this is intentional so that secret fields are not exposed in terminal output or CI logs.
:::

<!-- REFERENCE: Link "frontend model" to reference/field-types -->
<!-- REFERENCE: Link "validators" to reference/validators -->

---

## Reset

Reset a config value back to its [field default](/guides/defining-config#always-set-a-default).

```bash
python manage.py config reset <path> [--force]
```

**Arguments**

| Argument | Description |
|---|---|
| `path` | Config path in `app.section.field` format |

**Flags**

| Flag | Description |
|---|---|
| `-f`, `--force` | Skip the confirmation prompt |

**Examples**

```bash
# With confirmation prompt
python manage.py config reset myapp.general.maintenance_mode

# Skip the prompt
python manage.py config reset myapp.general.maintenance_mode --force
```

Without `--force`, you will be asked to confirm before the reset takes effect. This cannot be undone.

---

## Export

Export all registered configuration values to a JSON file.

```bash
python manage.py config export [app] [--output <path>]
```

**Arguments**

| Argument | Description |
|---|---|
| `app` | *(Optional)* App label to export. Exports all registered apps if omitted. |

**Flags**

| Flag | Description |
|---|---|
| `-o`, `--output` | Output file path. Defaults to `config_export.json` in the current directory. |

**Examples**

```bash
# Export all apps
python manage.py config export

# Export a single app
python manage.py config export myapp

# Export to a specific path
python manage.py config export --output /tmp/backup.json
```

The output file is written with `0600` permissions (owner read/write only) because it contains plaintext secrets.

:::warning
The export file contains **plaintext secrets**. Treat it like a credentials file — restrict access, do not commit it to version control, and delete it once it is no longer needed.
:::

**Output format**

```json
{
  "version": 1,
  "exported_at": "2026-01-15T10:30:00+00:00",
  "config": {
    "myapp": {
      "general": {
        "site_name": "Acme Corp",
        "maintenance_mode": false
      }
    }
  }
}
```

---

## Import

Import configuration values from a JSON file or stdin.

```bash
python manage.py config import [--file <path>] [--stdin] [--dry-run] [--force] [-S]
```

**Flags**

| Flag | Description |
|---|---|
| `-i`, `--file` | Path to the input `.json` file |
| `--stdin` | Read JSON from stdin instead of a file |
| `--dry-run` | Validate all values without writing anything to the database |
| `-f`, `--force` | Skip the confirmation prompt |
| `-S`, `--skip-on-save-callbacks` | Suppress `on_save` callbacks for all fields in this batch |

`--file` and `--stdin` are mutually exclusive. One of them must be provided.

**Examples**

```bash
# Import from a file
python manage.py config import --file config_export.json

# Import from stdin
cat config_export.json | python manage.py config import --stdin

# Validate without writing
python manage.py config import --file config_export.json --dry-run

# Skip confirmation and callbacks (useful in CI/CD pipelines)
python manage.py config import --file config_export.json --force --skip-on-save-callbacks
```

**Dry run**

`--dry-run` runs the full import pipeline — path resolution, type coercion, serialization, and validators — inside a database transaction that is always rolled back. This means a passing dry run is a genuine guarantee that the real import will succeed.

```bash
python manage.py config import --file config_export.json --dry-run
# ✔ Dry run passed — 12 value(s) look valid
```

**Atomicity**

The import runs inside a single database transaction. If any value fails validation, the entire import is rolled back and nothing is written.

**Skipping callbacks**

`--skip-on-save-callbacks` suppresses all [`on_save` callbacks](/guides/on-save-callbacks) for the duration of the import. This is useful when:

- Restoring a snapshot — you don't want 50 Slack notifications firing at once
- Cloning an environment — callbacks may be environment-specific
- Running in CI/CD — side effects are noise in automated pipelines

[Cache refresh](/guides/caching) always runs regardless of this flag — the cache is always kept consistent after import.

---

## Common workflows

### Inspect a value in production

```bash
python manage.py config get billing.general.live_mode
```

### Enable maintenance mode without logging in as staff

```bash
python manage.py config set myapp.general.maintenance_mode True
```

### Back up all config before a risky deployment

```bash
python manage.py config export --output pre_deploy_backup.json
```

### Restore config after a failed deployment

```bash
python manage.py config import --file pre_deploy_backup.json --force
```

### Rotate `SECRET_KEY` without losing encrypted values

See the full procedure in the [Encryption guide](/guides/encryption#key-rotation).

### Seed a fresh environment from an existing one

```bash
# On the source environment
python manage.py config export --output seed.json

# On the target environment
python manage.py config import --file seed.json --force --skip-on-save-callbacks
```

<!-- REFERENCE: Link "Encryption guide" to guides/encryption -->
