import importlib.metadata


def test_version_present():
    assert importlib.metadata.version("silly-notes") == "0.1.0"
