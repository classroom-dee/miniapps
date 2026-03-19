# Silly Notes

A tiny Python desktop widget that displays a rotating user-defined messages from an SQLite database.

## Planned features
- Small always-on desktop widget window
- SQLite-backed message storage
- Add/delete messages
- Configurable rotation interval
- Blacklist messages without deleting them
- Low resource usage
- Pytest test suite

## Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
pytest
python -m motto_widget.app
```