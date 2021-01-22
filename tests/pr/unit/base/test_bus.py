"""Tests for retrocookie.pr.bus."""
import contextlib
from typing import ContextManager

import pytest

from retrocookie.pr.base.bus import Bus
from retrocookie.pr.base.bus import Context
from retrocookie.pr.base.bus import Error
from retrocookie.pr.base.bus import Event


def test_events_publish() -> None:
    """It invokes the handler."""
    events = []
    bus = Bus()

    @bus.events.subscribe
    def handler(event: Event) -> None:
        events.append(event)

    event = Event()
    bus.events.publish(event)
    [seen] = events
    assert event is seen


def test_contexts_publish() -> None:
    """It invokes the handler."""
    contexts = []
    bus = Bus()

    @bus.contexts.subscribe
    def handler(context: Context) -> ContextManager[None]:
        contexts.append(context)
        return contextlib.nullcontext()

    context = Context()
    with bus.contexts.publish(context):
        pass
    [seen] = contexts
    assert context is seen


def test_events_subscribe_without_annotations() -> None:
    """It fails when the handler has no type annotations."""
    bus = Bus()
    with pytest.raises(Exception):

        @bus.events.subscribe
        def handler(event):  # type: ignore[no-untyped-def]
            pass


def test_contexts_subscribe_without_annotations() -> None:
    """It fails when the handler has no type annotations."""
    bus = Bus()
    with pytest.raises(Exception):

        @bus.contexts.subscribe
        def handler(event):  # type: ignore[no-untyped-def]
            pass


def test_events_errorhandler_raise() -> None:
    """It raises an Error when an event is "raised"."""
    bus = Bus()
    with pytest.raises(Error):
        with bus.events.errorhandler():
            bus.events.raise_(Event())


def test_events_errorhandler_reraise() -> None:
    """It raises an Error when an event is "reraised"."""
    bus = Bus()
    with pytest.raises(Error):
        with bus.events.errorhandler():
            with bus.events.reraise(Event(), when=Exception):
                raise Exception("Boom")
