from __future__ import annotations

from pathlib import Path

from silly.app import NoteWidgetApp


def main() -> None:
    db_path = Path("silly.sqlite3")
    app = NoteWidgetApp(db_path)
    app.run()


if __name__ == "__main__":
    main()
