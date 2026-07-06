"""Pytest configuration for the PawPal+ test suite.

Replaces each test's reported node id with its docstring, so `pytest -v`
reads as a plain-English checklist of what the suite verifies:

    <docstring> PASSED
"""

from __future__ import annotations


def pytest_itemcollected(item) -> None:
    """Show only the test's one-line docstring as its reported node id."""
    doc = item.obj.__doc__
    if doc:
        summary = " ".join(line.strip() for line in doc.strip().splitlines())
        item._nodeid = summary
