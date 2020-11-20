"""Tests for filter module."""
from typing import Any
from typing import Dict
from typing import List
from typing import Tuple

import pytest

from retrocookie.filter import escape_jinja
from retrocookie.filter import get_replacements


@pytest.mark.parametrize(
    "text, expected",
    [
        ("", ""),
        ("{{}}", '{{"{{"}}{{"}}"}}'),
        ("${{ matrix.os }}", '${{"{{"}} matrix.os {{"}}"}}'),
        ("lorem {# ipsum #} dolor", 'lorem {{"{#"}} ipsum {{"#}"}} dolor'),
        ("{{ a }} {{ b }}", '{{"{{"}} a {{"}}"}} {{"{{"}} b {{"}}"}}'),
    ],
)
def test_escape_jinja(text: str, expected: str) -> None:
    """It returns the expected result."""
    assert expected == escape_jinja(text.encode()).decode()


@pytest.mark.parametrize(
    "context, expected",
    [
        (
            {"test_key": "a test string", "other_key": ["this", "is", "a list"]},
            [(b"a test string", b"{{cookiecutter.test_key}}")],
        ),
        (
            {"test_key": "a test string", "other_key": None},
            [(b"a test string", b"{{cookiecutter.test_key}}")],
        ),
    ],
)
def test_get_replacements(
    context: Dict[str, Any], expected: List[Tuple[bytes, bytes]]
) -> None:
    """It ignore non string values."""
    assert expected == get_replacements(context, "", "")
