"""Tests for retrocookie.pr.exceptionhandlers."""
from functools import reduce
from typing import Tuple
from typing import Union

import pytest

from retrocookie.pr.base.exceptionhandlers import ExceptionHandler
from retrocookie.pr.base.exceptionhandlers import exceptionhandler
from retrocookie.pr.base.exceptionhandlers import nullhandler


class Red(Exception):
    """Exception for testing."""


class Green(Exception):
    """Exception for testing."""


class Blue(Exception):
    """Exception for testing."""


class Indigo(Blue):
    """Exception for testing."""


@exceptionhandler
def suppress_red(error: Red) -> bool:
    """Suppress Red exceptions."""
    return True


@exceptionhandler()  # empty parentheses are equivalent to none
def suppress_green(error: Green) -> bool:
    """Suppress Green exceptions."""
    return True


@exceptionhandler
def suppress_blue(error: Blue) -> bool:
    """Suppress Blue exceptions."""
    return True


@exceptionhandler
def suppress_indigo(error: Indigo) -> bool:
    """Suppress Indigo exceptions."""
    return True


@exceptionhandler(Red, Blue)
def suppress_red_and_blue(error: Union[Red, Blue]) -> bool:
    """Suppress Red and Blue exceptions."""
    return True


@exceptionhandler(Red, Green)
def suppress_red_and_green(error: Union[Red, Green]) -> bool:
    """Suppress Red and Green exceptions."""
    return True


@exceptionhandler(Red, Green, Blue)
def suppress_red_green_blue(error: Union[Red, Green, Blue]) -> bool:
    """Suppress Red, Green, and Blue exceptions."""
    return True


def test_nullhandler() -> None:
    """It does not swallow the error."""
    with pytest.raises(Blue):
        with nullhandler:
            raise Blue()


def test_decorator_missing_annotation() -> None:
    """It raises TypeError."""
    with pytest.raises(TypeError):

        @exceptionhandler
        def _(exception):  # type: ignore[no-untyped-def]
            pass


def test_decorator_decorator() -> None:
    """It can be used as a decorator."""

    @suppress_blue
    def raise_blue() -> None:
        raise Blue()

    raise_blue()  # does not throw


@pytest.mark.parametrize(
    "handler",
    [
        suppress_indigo,
        suppress_blue,
        suppress_red_and_blue,
        suppress_red_green_blue,
    ],
)
def test_decorator_positive(handler: ExceptionHandler) -> None:
    """The exception is handled."""
    with handler:
        raise Indigo()


@pytest.mark.parametrize(
    "handler",
    [
        nullhandler,
        suppress_red,
        suppress_green,
        suppress_indigo,
        suppress_red_and_green,
    ],
)
def test_decorator_negative(handler: ExceptionHandler) -> None:
    """The exception is not handled."""
    with pytest.raises(Blue):
        with handler:
            raise Blue()


@pytest.mark.parametrize(
    "handlers",
    [
        (nullhandler, suppress_indigo),
        (suppress_indigo, nullhandler),
        (suppress_red, suppress_green, suppress_blue),
        (suppress_blue, suppress_green, suppress_red),
    ],
)
def test_compose_lshift(handlers: Tuple[ExceptionHandler]) -> None:
    """The exception is handled."""
    handler = reduce(lambda a, b: a << b, handlers)
    with handler:
        raise Indigo()


@pytest.mark.parametrize(
    "handlers",
    [
        (nullhandler, suppress_indigo),
        (suppress_indigo, nullhandler),
        (suppress_blue, suppress_red),
        (suppress_red, suppress_blue),
        (suppress_red, suppress_green, suppress_blue),
        (suppress_blue, suppress_green, suppress_red),
    ],
)
def test_compose_rshift(handlers: Tuple[ExceptionHandler]) -> None:
    """The exception is handled."""
    handler = reduce(lambda a, b: a >> b, handlers)
    with handler:
        raise Indigo()
