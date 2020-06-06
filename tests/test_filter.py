"""Tests for filter module."""
import pytest

from retrocookie.filter import escape_jinja


@pytest.mark.parametrize(
    "text, expected",
    [
        ("", ""),
        ("{{}}", '{{ "{{" }}{{ "}}" }}'),
        ("${{ matrix.os }}", '${{ "{{" }} matrix.os {{ "}}" }}'),
        ("lorem {# ipsum #} dolor", 'lorem {{ "{#" }} ipsum {{ "#}" }} dolor'),
        ("{{ a }} {{ b }}", '{{ "{{" }} a {{ "}}" }} {{ "{{" }} b {{ "}}" }}'),
    ],
)
def test_escape_jinja(text: str, expected: str) -> None:
    """It returns the expected result."""
    assert expected == escape_jinja(text.encode()).decode()
