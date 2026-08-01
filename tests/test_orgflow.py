"""Smoke tests for the orgflow package scaffold."""

import pytest


@pytest.mark.unit
def test_orgflow_importable() -> None:
    """The package imports under the repo's ``pythonpath = ["src"]``."""
    import orgflow  # noqa: F401  (import-only smoke test)
