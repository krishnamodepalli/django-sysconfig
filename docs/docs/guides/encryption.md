# Encryption

`django-sysconfig` can store sensitive values — API keys, passwords, tokens — encrypted at rest using the `SecretFrontendModel`. This page explains how the encryption works, what it protects against, and what to do when you rotate your `SECRET_KEY`.

---

## How it works

Secret fields are encrypted using [Fernet](https://cryptography.io/en/latest/fernet/) symmetric encryption, which is AES-128-CBC with a SHA-256 HMAC for integrity verification.

The encryption key is derived from Django's `SECRET_KEY` using SHA-256. This means:

- You don't need to configure a separate encryption key.
- Changing `SECRET_KEY` will make existing encrypted values unreadable (see [Key rotation](#key-rotation) below).
- The encrypted value is stored as a Fernet token (a base64-encoded string) in the `raw_value` column of the `ConfigValue` table.

---

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

---

## Reading secret values

Reading a secret field is identical to reading any other field. Decryption is transparent:

```python
from django_sysconfig.accessor import config

stripe_key = config.get("integrations.stripe.secret_key")
# Returns the plaintext string, decrypted automatically
```

---

## What the admin UI shows

The admin UI **never displays** the stored value of a secret field. The input is always rendered as an empty password field, regardless of whether a value exists.

- To **set or update** a secret: type the new value and save.
- To **leave it unchanged**: leave the input empty and save. The existing encrypted value is preserved.

This means there's no way to retrieve a secret value through the admin UI once it's been saved. If you need to verify or audit a stored secret, query the database directly (the value will be encrypted) or check your original source.

---

## What it protects against

Encryption at rest protects secret values if your database is compromised. An attacker who gains read access to the `ConfigValue` table will see Fernet tokens, not plaintext secrets.

**It does not protect against:**

- An attacker with access to both the database and `SECRET_KEY` (they can derive the encryption key)
- Application-level vulnerabilities — once decrypted by `config.get(...)`, the value is a plaintext Python string in memory
- Django's `SECRET_KEY` itself being exposed

For most threat models, this is the right level of protection for operational secrets like third-party API keys.

---

## Key rotation

If you rotate Django's `SECRET_KEY` — which you should do if it's ever been exposed — all encrypted `ConfigValue` rows become unreadable. There is no automatic migration.

**The procedure for rotating `SECRET_KEY` with encrypted config values:**

1. **Before rotating**, read all secret field values while the old key is still active:

    ```python
    from django_sysconfig.accessor import config

    secrets = {
        "integrations.stripe.secret_key": config.get("integrations.stripe.secret_key"),
        "integrations.stripe.webhook_secret": config.get("integrations.stripe.webhook_secret"),
        # ... all other SecretFrontendModel fields
    }
    ```

2. **Rotate `SECRET_KEY`** in your settings / environment.

3. **Re-save all secret values** using the new key:

    ```python
    config.set_many(secrets)
    ```

    This re-encrypts each value with the new key derived from the new `SECRET_KEY`.

> **Tip:** Write this as a management command and test it in a staging environment before running in production.

---

## Security considerations

- Keep `SECRET_KEY` in an environment variable or secrets manager — never commit it to version control.
- Use a long, random `SECRET_KEY` (Django generates a 50-character random string by default). Avoid reusing keys across environments.
- If you use a dedicated secrets manager (AWS Secrets Manager, Vault, etc.) for production secrets, consider whether encrypting those same secrets in the database provides sufficient additional value for your threat model. Using `django-sysconfig` for non-sensitive configuration and your secrets manager for credentials is also a perfectly valid architecture.
