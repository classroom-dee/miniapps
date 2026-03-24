from __future__ import annotations

from silly.db import Database


def test_rotation_sequence_skips_blacklisted(tmp_path) -> None:
    db = Database(tmp_path / "app.sqlite3")
    try:
        first = db.add_message("One")
        second = db.add_message("Two")
        third = db.add_message("Three")

        db.set_blacklist(second, True)

        m1 = db.get_next_message(None)
        m2 = db.get_next_message(m1.id if m1 else None)
        m3 = db.get_next_message(m2.id if m2 else None)

        assert m1 is not None and m1.text == "One"
        assert m2 is not None and m2.text == "Three"
        assert m3 is not None and m3.text == "One"
        assert third > first
    finally:
        db.close()


def test_rotation_none_when_all_blacklisted(tmp_path) -> None:
    db = Database(tmp_path / "app.sqlite3")
    try:
        a = db.add_message("A")
        b = db.add_message("B")
        db.set_blacklist(a, True)
        db.set_blacklist(b, True)

        assert db.get_next_message() is None
    finally:
        db.close()
