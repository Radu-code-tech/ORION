"""OR-EVENT-001: deterministic in-process publish/subscribe event bus."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class Event:
    """Immutable ORION event."""

    topic: str
    payload: Any = None
    event_id: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.topic, str) or not self.topic.strip():
            raise ValueError("event topic must be a non-empty string")


class EventBus:
    """Deterministic synchronous event bus for ORION components."""

    def __init__(self) -> None:
        self._subscribers: dict[str, list[Callable[[Event], Any]]] = {}

    def subscribe(
        self,
        topic: str,
        handler: Callable[[Event], Any],
    ) -> None:
        """Register a handler for a topic.

        Handlers are called synchronously in registration order.
        Duplicate registrations are rejected.
        """
        self._validate_topic(topic)

        if not callable(handler):
            raise TypeError("handler must be callable")

        handlers = self._subscribers.setdefault(topic, [])

        if handler in handlers:
            raise ValueError("handler already subscribed to topic")

        handlers.append(handler)

    def unsubscribe(
        self,
        topic: str,
        handler: Callable[[Event], Any],
    ) -> None:
        """Remove a previously registered handler."""
        self._validate_topic(topic)

        handlers = self._subscribers.get(topic)

        if handlers is None or handler not in handlers:
            raise ValueError("handler is not subscribed to topic")

        handlers.remove(handler)

        if not handlers:
            del self._subscribers[topic]

    def publish(self, event: Event) -> list[Exception]:
        """Publish an event to all registered subscribers.

        Subscribers are invoked in registration order.

        A subscriber exception is isolated and collected in the returned
        failure list. Other subscribers continue to receive the event.

        A snapshot of the subscriber list is used so subscription changes
        performed during dispatch do not alter the current dispatch cycle.
        """
        if not isinstance(event, Event):
            raise TypeError("event must be an Event instance")

        failures: list[Exception] = []

        subscribers = list(self._subscribers.get(event.topic, []))

        for handler in subscribers:
            try:
                handler(event)
            except Exception as exc:
                failures.append(exc)

        return failures

    def subscriber_count(self, topic: str) -> int:
        """Return the number of subscribers registered for a topic."""
        self._validate_topic(topic)
        return len(self._subscribers.get(topic, []))

    @staticmethod
    def _validate_topic(topic: str) -> None:
        if not isinstance(topic, str) or not topic.strip():
            raise ValueError("topic must be a non-empty string")