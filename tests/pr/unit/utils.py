"""Utilities for testing."""
from typing import Iterator
from typing import Type

import pytest

from retrocookie.pr.base import bus
from retrocookie.pr.compat import contextlib


@contextlib.contextmanager
def raises(event_type: Type[bus.Event]) -> Iterator[None]:
    """It raises the event on the bus."""
    with pytest.raises(bus.Error) as exception_info:
        yield
    event = exception_info.value.event
    del exception_info
    assert isinstance(event, event_type)
