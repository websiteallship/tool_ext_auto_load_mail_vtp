# Git & Workflow Rules

## Commit Message Format
```
<type>: <description>

Types:
  feat:     New feature
  fix:      Bug fix
  refactor: Code change (no new feature/fix)
  docs:     Documentation only
  test:     Adding/updating tests
  chore:    Build, deps, configs
  style:    Formatting (no logic change)
```

Examples:
```
feat: add Gmail OAuth2 authentication flow
fix: handle timeout when downloading bang ke PDF
refactor: extract URL validation to utility function
docs: add CORE_gmail_client API documentation
test: add unit tests for link extractor edge cases
chore: update requirements.txt with keyring 25.0
```

## Branch Naming
```
feature/<short-description>    # New features
fix/<short-description>        # Bug fixes
refactor/<short-description>   # Code improvements
docs/<short-description>       # Documentation
```

## Files to NEVER Commit
```
.env                    # Client credentials
credentials.json        # Google Cloud credentials
token.json             # OAuth tokens
downloads/             # Downloaded invoice files
logs/                  # Application log files
__pycache__/           # Python bytecode
*.pyc                  # Compiled Python
dist/                  # PyInstaller output
build/                 # PyInstaller temp
*.spec                 # PyInstaller spec (auto-generated)
venv/                  # Virtual environment
```

## PR Checklist (before merging)
- [ ] Code follows `02_coding_standards.md`
- [ ] No credentials in code (`03_security.md`)
- [ ] Architecture layers respected (`04_architecture.md`)
- [ ] Error handling is specific (`05_error_handling.md`)
- [ ] Tests pass: `pytest tests/ -v`
- [ ] Type checking passes: `mypy src/`
- [ ] Linting passes: `ruff check src/ app.py`
