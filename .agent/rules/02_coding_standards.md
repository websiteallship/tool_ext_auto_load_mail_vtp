# Coding Standards

## Python Style
- Follow PEP 8 and modern Python 3.11+ idioms
- Use `ruff` for linting (replaces black + isort + flake8)
- Use `mypy` for static type checking (strict mode)
- Line length: 100 characters maximum

## Naming Conventions
- Classes: `PascalCase` (e.g. `GmailClient`, `EmailRule`)
- Functions/methods: `snake_case` (e.g. `search_emails`, `extract_bang_ke_link`)
- Variables: `snake_case` (e.g. `max_results`, `output_dir`)
- Constants: `UPPER_SNAKE_CASE` (e.g. `GMAIL_SCOPES`, `SERVICE_NAME`)
- Private: prefix with `_` (e.g. `_api_call`, `_parse_html`)

## Type Hints — MANDATORY
Always use type hints for function signatures:
```python
# ✅ Correct
def search_emails(self, query: str, max_results: int = 50) -> list[EmailMessage]:

# ❌ Wrong — missing type hints
def search_emails(self, query, max_results=50):
```

## Functions
- Each function does ONE thing (Single Responsibility)
- Maximum 20 lines per function — split if longer
- Maximum 3 arguments — use dataclass for more
- Descriptive verb names: `download_attachment`, `extract_link`, `validate_rule`
- No side effects in functions named `get_*`, `is_*`, `extract_*`

## Docstrings — REQUIRED for public methods
Use Google-style docstrings:
```python
def search_emails(self, query: str) -> list[EmailMessage]:
    """
    Search Gmail for emails matching query.
    
    Args:
        query: Gmail search query syntax string
    
    Returns:
        List of matching EmailMessage objects
    
    Raises:
        AuthError: If not authenticated
    """
```

## Imports Order
1. Standard library (`import json`, `from pathlib import Path`)
2. Third-party (`import requests`, `from bs4 import BeautifulSoup`)
3. Local (`from src.models import EmailMessage`)

Separated by blank lines. Use `ruff` to auto-sort.

## Error Handling
- Use specific exceptions, never bare `except:`
- Never swallow errors silently (`except: pass`)
- Custom exceptions inherit from `AppError` base class
- Log errors before re-raising
- Use `tenacity` for retry logic, not manual loops

## No Magic Numbers
```python
# ✅ 
MAX_RETRY_ATTEMPTS = 3
RETRY_BACKOFF_SECONDS = 2

# ❌
for i in range(3):
    time.sleep(2)
```
