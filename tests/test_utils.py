"""Tests for retrocookie.utils."""
import pytest

from retrocookie.utils import removeprefix
from retrocookie.utils import removesuffix


@pytest.mark.parametrize(
    "string, prefix, expected",
    [
        ("Lorem ipsum", "Lorem", " ipsum"),
        ("Lorem ipsum", "", "Lorem ipsum"),
        ("Lorem ipsum", "Lorem ipsum", ""),
        ("Lorem ipsum", "x", "Lorem ipsum"),
        ("", "Lorem ipsum", ""),
        ("", "", ""),
    ],
)
def test_removeprefix(string: str, prefix: str, expected: str) -> None:
    """It removes the prefix."""
    assert expected == removeprefix(string, prefix)


@pytest.mark.parametrize(
    "string, suffix, expected",
    [
        ("Lorem ipsum", "ipsum", "Lorem "),
        ("Lorem ipsum", "", "Lorem ipsum"),
        ("Lorem ipsum", "Lorem ipsum", ""),
        ("Lorem ipsum", "x", "Lorem ipsum"),
        ("", "Lorem ipsum", ""),
        ("", "", ""),
    ],
)
def test_removesuffix(string: str, suffix: str, expected: str) -> None:
    """It removes the suffix."""
    assert expected == removesuffix(string, suffix)
