from __future__ import annotations

import pytest
from silly.db import Database
from silly.settings import DEFAULT_ROTATION_INTERVAL_SECONDS


@pytest.fixture()
def db(tmp_path):
    database = Database(tmp_path / "test.sqlite3")
    try:
        yield database
    finally:
        database.close()


def test_initializes_default_interval(db: Database) -> None:
    assert (
        db.get_settings().rotation_interval_seconds == DEFAULT_ROTATION_INTERVAL_SECONDS
    )


def test_add_and_list_messages(db: Database) -> None:
    first_id = db.add_message("Stay curious")
    second_id = db.add_message("Ship small, improve fast")

    messages = db.list_messages()

    assert [m.id for m in messages] == [first_id, second_id]
    assert [m.text for m in messages] == ["Stay curious", "Ship small, improve fast"]
    assert all(not m.is_blacklisted for m in messages)


def test_rejects_empty_messages(db: Database) -> None:
    with pytest.raises(ValueError):
        db.add_message("   \n   ")


def test_delete_message(db: Database) -> None:
    message_id = db.add_message("Delete me")

    assert db.delete_message(message_id) is True
    assert db.get_message(message_id) is None
    assert db.delete_message(message_id) is False


def test_blacklist_filters_rotation_pool(db: Database) -> None:
    first_id = db.add_message("Visible")
    second_id = db.add_message("Hidden")
    db.set_blacklist(second_id, True)

    visible_messages = db.list_messages(include_blacklisted=False)

    assert [m.id for m in visible_messages] == [first_id]
    assert visible_messages[0].text == "Visible"


def test_rotation_wraps_and_skips_blacklisted(db: Database) -> None:
    first_id = db.add_message("One")
    second_id = db.add_message("Two")
    third_id = db.add_message("Three")
    db.set_blacklist(second_id, True)

    assert db.get_next_message().id == first_id
    assert db.get_next_message(first_id).id == third_id
    assert db.get_next_message(third_id).id == first_id


def test_rotation_returns_none_when_no_eligible_messages(db: Database) -> None:
    only_id = db.add_message("Blocked")
    db.set_blacklist(only_id, True)

    assert db.get_next_message() is None
    assert db.get_next_message(only_id) is None


def test_set_rotation_interval(db: Database) -> None:
    assert db.set_rotation_interval(120) == 120
    assert db.get_settings().rotation_interval_seconds == 120


def test_rejects_invalid_interval(db: Database) -> None:
    with pytest.raises(ValueError):
        db.set_rotation_interval(0)

    with pytest.raises(TypeError):
        db.set_rotation_interval("30")  # type: ignore[arg-type]


def test_duplicate_message_raises_integrity_error(db: Database) -> None:
    db.add_message("Same text")

    with pytest.raises(Exception) as exc:
        db.add_message("Same text")

    assert "UNIQUE" in str(exc.value).upper() or "unique" in str(exc.value)
