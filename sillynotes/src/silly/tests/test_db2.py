from __future__ import annotations

from silly.db import Database


def test_unblacklisting_restores_message_to_rotation(tmp_path) -> None:
    db = Database(tmp_path / "test.sqlite3")
    try:
        first = db.add_message("First")
        second = db.add_message("Second")

        db.set_blacklist(second, True)
        assert db.get_next_message(first).text == "First"

        db.set_blacklist(second, False)
        assert db.get_next_message(first).text == "Second"
    finally:
        db.close()


def test_delete_current_message_rotation_can_continue(tmp_path) -> None:
    db = Database(tmp_path / "test.sqlite3")
    try:
        first = db.add_message("First")
        second = db.add_message("Second")

        db.delete_message(first)
        next_message = db.get_next_message(first)

        assert next_message is not None
        assert next_message.id == second
    finally:
        db.close()


def test_list_messages_excludes_blacklisted_when_requested(tmp_path) -> None:
    db = Database(tmp_path / "test.sqlite3")
    try:
        visible = db.add_message("Visible")
        hidden = db.add_message("Hidden")
        db.set_blacklist(hidden, True)

        messages = db.list_messages(include_blacklisted=False)
        assert len(messages) == 1
        assert messages[0].id == visible
    finally:
        db.close()
