# Security Rules

## 🔴 NEVER — Hard Rules (Violation = Immediate Fix)

1. **NEVER hardcode credentials** in source code (passwords, tokens, API keys, client secrets)
2. **NEVER commit `.env` files** or credential JSON files to git
3. **NEVER log sensitive data** (OAuth tokens, passwords, email content body)
4. **NEVER use `gmail.full_access` scope** — use minimal scopes only
5. **NEVER store tokens as plain text** on disk
6. **NEVER pass credentials** via command line arguments

## ✅ ALWAYS — Required Practices

1. **Store OAuth tokens** using `keyring` (Windows Credential Locker)
2. **Store client credentials** in `.env` file (which is gitignored)
3. **Use minimal Gmail API scopes:**
   - `gmail.readonly` — read emails and attachments
   - `gmail.modify` — add/remove labels
4. **Mask sensitive data** in log output using `mask_sensitive()` utility
5. **Use HTTPS** for all external connections
6. **Validate URLs** before making HTTP requests
7. **Set timeouts** on all HTTP requests (default: 30 seconds)

## Credential Storage Map

| Credential | Storage Method | Access |
|------------|---------------|--------|
| OAuth2 tokens | `keyring` (Windows Credential Locker) | `keyring.get_password()` |
| Client ID/Secret | `.env` file | `os.getenv()` via `python-dotenv` |
| App settings | `config/settings.json` | `json.load()` |
| Email rules | `config/rules.json` | `json.load()` |

## .gitignore Must Include
```
.env
credentials.json
token.json
*.pem
*.key
downloads/
logs/
__pycache__/
```

## URL Validation
Before downloading from any URL extracted from email:
- Must be HTTPS
- Must match expected domain patterns (e.g. `vinvoice.viettel.vn`)
- Log a warning for unexpected domains
