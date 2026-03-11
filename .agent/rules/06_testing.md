# Testing Rules

## Test Requirements
- Every new module MUST have corresponding test file in `tests/`
- Use `pytest` framework exclusively (not `unittest`)
- Test file naming: `test_<module_name>.py`
- Test class naming: `Test<ClassName>` or descriptive function `test_<behavior>`

## Coverage Targets
| Module | Minimum Coverage |
|--------|-----------------|
| `link_extractor.py` | 90% |
| `rule_engine.py` | 90% |
| `file_downloader.py` | 80% |
| `gmail_client.py` | 50% (external API) |
| `scheduler.py` | 60% |
| `app.py` (GUI) | Manual testing only |

## Test Structure
```python
class TestLinkExtractor:
    def setup_method(self):
        """Create fresh instance for each test."""
        self.extractor = LinkExtractor()
    
    def test_extract_found(self):       # happy path
    def test_extract_not_found(self):   # edge case
    def test_extract_malformed(self):   # error case
```

## What to Test
- ✅ Pure logic functions (extractors, validators, parsers)
- ✅ Config loading/saving (use `tmp_path` fixture)
- ✅ Error handling paths (exceptions raised correctly)
- ✅ Edge cases (empty input, None, unicode, long strings)
- ❌ GUI rendering (manual test only)
- ❌ External API calls in unit tests (use mocks)

## Running Tests
```bash
pytest tests/ -v                    # all tests
pytest tests/ --cov=src             # with coverage
pytest tests/test_link_extractor.py # single file
```
