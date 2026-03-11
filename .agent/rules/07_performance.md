# Performance & Async Rules

## Threading Model — MANDATORY
- GUI runs on main thread (CustomTkinter event loop)
- Email processing runs on daemon background thread
- Communication between threads via `queue.Queue` only
- NEVER call GUI methods (`widget.configure()`, `widget.insert()`) from background thread
- Use `root.after(100, poll_queue)` pattern for GUI updates

## Async Downloads
When downloading multiple files:
```python
# Use asyncio.gather() with semaphore for concurrent downloads
semaphore = asyncio.Semaphore(5)  # max 5 concurrent
```
- Maximum 5 concurrent downloads
- Each download has 30-second timeout
- Rate limit: 1 request per 2 seconds for sequential operations

## Memory Rules
- Stream large file downloads (don't load entire file into memory)
- Use generators for processing large email lists
- Close HTTP sessions after use (`with requests.Session() as session:`)
- Log file uses RotatingFileHandler (max 5MB × 3 files = 15MB total)

## Gmail API Optimization
- Batch API calls when possible
- Request only needed fields (`fields` parameter)
- Cache processed email IDs to avoid re-processing
- Respect Gmail API rate limits (250 quota units/user/second)
- Use `pageToken` for pagination, don't fetch all at once

## Startup Performance
- Load config files lazily (only when needed)
- Don't authenticate Gmail until user triggers action
- GUI should be responsive within 1 second of launch
