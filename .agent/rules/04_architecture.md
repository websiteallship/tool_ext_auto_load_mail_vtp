# Architecture Rules

## Layer Boundaries — STRICT

```
GUI Layer (app.py)           → calls ONLY Core Layer
Core Layer (src/*.py)        → NEVER imports from GUI
Infrastructure (keyring, fs) → injected into Core via parameters
```

### GUI Layer Rules
- All GUI code lives in `app.py` only
- GUI NEVER contains business logic (searching, parsing, downloading)
- GUI communicates with Core via `Queue` (thread-safe)
- Long operations run on background `threading.Thread(daemon=True)`
- Use `root.after(100, poll_queue)` to update UI from queue

### Core Layer Rules
- Each module has a SINGLE responsibility:
  - `gmail_client.py` — Gmail connection only
  - `link_extractor.py` — HTML parsing only
  - `file_downloader.py` — file I/O only
  - `rule_engine.py` — rule CRUD only
  - `scheduler.py` — orchestration only
  - `models.py` — dataclasses only (NO logic)
- Core modules are testable WITHOUT GUI
- Core modules communicate via function calls and return values, NOT global state

### Infrastructure Rules
- External I/O (Gmail API, HTTP, file system) is wrapped in Core functions
- Retry logic is applied at the infrastructure boundary
- All I/O has explicit timeouts

## Data Flow — Unidirectional
```
User Action → GUI → Scheduler → Core Modules → Infrastructure → Results → GUI
```
Never: Infrastructure → Core (callbacks are OK via injected callables)

## Configuration
- All user configuration is JSON-based (`config/*.json`)
- Default values are defined in code, loaded from JSON if exists
- Config changes require NO code changes (data-driven)

## Threading Model
- Main thread: GUI event loop (CustomTkinter)
- Background thread: email processing (daemon=True)
- Queue: thread-safe communication between them
- NEVER call GUI methods from background thread

## Module Dependencies (Direction Allowed)
```
app.py → scheduler.py → gmail_client.py
                       → rule_engine.py
                       → link_extractor.py
                       → file_downloader.py
                       → models.py

All modules → models.py (shared types)
No circular dependencies allowed
```
