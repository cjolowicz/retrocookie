"""Tests for retrocookie.pr.exceptionhandlers."""
from functools import reduce
from typing import Tuple
from typing import Union

import pytest

from retrocookie.pr.base.exceptionhandlers import ExceptionHandler
from retrocookie.pr.base.exceptionhandlers import exceptionhandler
from retrocookie.pr.base.exceptionhandlers import nullhandler


class RedError(Exception):
    """Exception for testing."""


class GreenError(Exception):
    """Exception for testing."""


class BlueError(Exception):
    """Exception for testing."""


class IndigoError(BlueError):
    """Exception for testing."""


@exceptionhandler
def suppress_red(error: RedError) -> bool:
    """Suppress RedError exceptions."""
    return True


@exceptionhandler()  # empty parentheses are equivalent to none
def suppress_green(error: GreenError) -> bool:
    """Suppress GreenError exceptions."""
    return True


@exceptionhandler
def suppress_blue(error: BlueError) -> bool:
    """Suppress BlueError exceptions."""
    return True


@exceptionhandler
def suppress_indigo(error: IndigoError) -> bool:
    """Suppress IndigoError exceptions."""
    return True


@exceptionhandler(RedError, BlueError)
def suppress_red_and_blue(error: Union[RedError, BlueError]) -> bool:
    """Suppress RedError and BlueError exceptions."""
    return True


@exceptionhandler(RedError, GreenError)
def suppress_red_and_green(error: Union[RedError, GreenError]) -> bool:
    """Suppress RedError and GreenError exceptions."""
    return True


@exceptionhandler(RedError, GreenError, BlueError)
def suppress_red_green_blue(error: Union[RedError, GreenError, BlueError]) -> bool:
    """Suppress RedError, GreenError, and BlueError exceptions."""
    return True


def test_nullhandler() -> None:
    """It does not swallow the error."""
    with pytest.raises(BlueError):
        with nullhandler:
            raise BlueError()


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
        raise BlueError()

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
        raise IndigoError()


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
    with pytest.raises(BlueError):
        with handler:
            raise BlueError()


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
        raise IndigoError()


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
        raise IndigoError()
