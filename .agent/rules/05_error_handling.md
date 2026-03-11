# Error Handling Rules

## Exception Hierarchy — USE THIS
```python
AppError (base)
├── AuthError
│   ├── TokenExpiredError     # auto-refresh possible
│   └── AuthRevokedError      # needs re-auth
├── NetworkError
│   └── ApiQuotaError         # Gmail quota exceeded
├── FileError
│   └── DiskSpaceError        # cannot write
└── ConfigError
    └── InvalidRuleError      # bad rule config
```

## Rules

1. **Custom exceptions ONLY** — never raise generic `Exception` or `ValueError`
2. **All exceptions inherit from `AppError`** with `recoverable: bool` flag
3. **Catch specific, raise specific** — no `except Exception` without re-raise
4. **Log before raising** — always `logger.error()` or `logger.warning()` before `raise`
5. **Never swallow errors** — `except: pass` is FORBIDDEN

## Retry Policy
- Gmail API calls: 3 retries, exponential backoff (2s, 4s, 8s)
- File downloads: 3 retries, exponential backoff (3s, 6s, 12s)
- Token refresh: 2 retries, backoff (1s, 3s)
- Use `tenacity` library, not manual `for` loops

## Graceful Degradation Priority
```
Priority 1: Download Gmail attachments     ← MUST succeed
Priority 2: Download bảng kê from URL      ← CAN fail without blocking
Priority 3: Label emails in Gmail          ← Nice-to-have
```

If bảng kê download fails → log warning, continue to next email
If Gmail auth fails → stop batch, notify user
If disk full → stop immediately, alert user

## Error Messages for User
- User-facing: clear Vietnamese, no technical jargon
- Log file: full English technical detail with traceback
- Example user: "Không thể tải bảng kê. Vui lòng kiểm tra kết nối mạng."
- Example log: `ERROR file_downloader: ConnectionError downloading https://... timeout=30s`
