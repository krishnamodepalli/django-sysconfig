# Encryption

`django-sysconfig` can store sensitive values — API keys, passwords, tokens — encrypted at rest using the `SecretFrontendModel`. This page explains how the encryption works, what it protects against, and what to do when you rotate your `SECRET_KEY`.

## How it works

Secret fields are encrypted using [Fernet](https://cryptography.io/en/latest/fernet/) symmetric encryption, which is AES-128-CBC with a SHA-256 HMAC for integrity verification.

The encryption key is derived from Django's `SECRET_KEY` using SHA-256. This means:

- You don't need to configure a separate encryption key.
- Changing `SECRET_KEY` will make existing encrypted values unreadable (see [Key rotation](#key-rotation) below).
- The encrypted value is stored as a Fernet token (a base64-encoded string) in the `raw_value` column of the `ConfigValue` table.

## Defining a secret field

```python
from django_sysconfig.frontend_models import SecretFrontendModel
from django_sysconfig.registry import register_config, Section, Field

@register_config("integrations")
class IntegrationsConfig:
    class Stripe(Section):
        label = "Stripe"

        secret_key = Field(
            SecretFrontendModel,
            label="Stripe Secret Key",
            comment="Starts with <code>sk_live_</code> or <code>sk_test_</code>.",
        )

        webhook_secret = Field(
            SecretFrontendModel,
            label="Webhook Signing Secret",
            comment="Starts with <code>whsec_</code>.",
        )
```

## Reading secret values

Reading a secret field is identical to reading any other field. Decryption is transparent:

```python
from django_sysconfig.accessor import config

stripe_key = config.get("integrations.stripe.secret_key")
# Returns the plaintext string, decrypted automatically
```

## What the admin UI shows

The admin UI **never exposes** the stored value of a secret field. Secret fields always render as `<input type="password" />`:

- **A value is already stored** — the field shows a dummy placeholder, not the real value.
- **No value has been stored** — the field renders empty.

### Editing secrets

| Intent | Action |
|---|---|
| Set or update a secret | Type the new value and save |
| Keep the existing value | Leave the field as-is and save — the encrypted value is preserved |

:::warning
Once a secret is saved, it cannot be retrieved through the admin UI. To verify or audit a stored secret, query the database directly (values are stored encrypted) or refer to your original source.
:::

:::tip
Any modified field on the config page is marked with a dot indicator, so you can always tell what has changed before saving.
:::

## What it protects against

Encryption at rest protects secret values if your database is compromised. An attacker who gains read access to the `ConfigValue` table will see Fernet tokens, not plaintext secrets.

**It does not protect against:**

- An attacker with access to both the database and `SECRET_KEY` (they can derive the encryption key)
- Application-level vulnerabilities — once decrypted by `config.get(...)`, the value is a plaintext Python string in memory
- Django's `SECRET_KEY` itself being exposed

For most threat models, this is the right level of protection for operational secrets like third-party API keys.

## Key Rotation

:::warning
Rotating Django's `SECRET_KEY` **will make all encrypted `ConfigValue` rows permanently unreadable.** There is no automatic migration in the current version.
:::

By default, secret fields are encrypted using a key derived from Django's `SECRET_KEY`. This means rotating `SECRET_KEY` — which you should do if it's ever been exposed — also invalidates all stored secrets.

### Before rotating `SECRET_KEY`

You must export all config values before the rotation, then re-import them after.

**Step 1 — Export all config while the old key is still active:**

```bash
python manage.py config export --output config_backup.json
```

:::warning
The export file contains **plaintext secrets**. Treat it like a credentials file — restrict its permissions and delete it once the rotation is complete.
:::

**Step 2 — Rotate `SECRET_KEY`** in your settings or environment.

**Step 3 — Re-import to re-encrypt everything under the new key:**

```bash
python manage.py config import --file config_backup.json
```

You can validate the file first without writing anything using `--dry-run`:

```bash
python manage.py config import --file config_backup.json --dry-run
```

The import runs inside a single transaction — it either fully succeeds or rolls back entirely, leaving your config unchanged.

:::tip
Once the import completes successfully, delete `config_backup.json`. It contains your secrets in plaintext.
:::

See the [Management Command](/cli/management-command) reference for all available flags.

### Coming in Phase 2: `SYSCONFIG_ENCRYPTION_KEY`

This coupling between `SECRET_KEY` and config encryption is a known limitation being addressed in the next major release ([#32](https://github.com/krishnamodepalli/django-sysconfig/issues/32)).

Phase 2 will introduce:

- **`SYSCONFIG_ENCRYPTION_KEY`** — a dedicated setting to decouple config encryption from `SECRET_KEY`. Once set, rotating `SECRET_KEY` will no longer affect your stored secrets.
- **`rotate_encryption_key` management command** — a safe, atomic key rotation:

  ```bash
  python manage.py rotate_encryption_key --old-key=<old> --new-key=<new>
  ```

Until then, the export/import procedure above is required whenever `SECRET_KEY` is rotated.

## Security considerations

- Keep `SECRET_KEY` in an environment variable or secrets manager — never commit it to version control.
- Use a long, random `SECRET_KEY` (Django generates a 50-character random string by default). Avoid reusing keys across environments.
- If you use a dedicated secrets manager (AWS Secrets Manager, Vault, etc.) for production secrets, consider whether encrypting those same secrets in the database provides sufficient additional value for your threat model. Using `django-sysconfig` for non-sensitive configuration and your secrets manager for credentials is also a perfectly valid architecture.
