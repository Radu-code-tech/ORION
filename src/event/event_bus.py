"""Deterministic in-process publish/subscribe event bus for ORION."""
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

@dataclass(frozen=True)
class Event:
    topic: str
    payload: Any = None
    event_id: Optional[str] = None

class EventBus:
    def __init__(self) -> None:
        self._subscribers: Dict[str, List[Callable[[Event], Any]]] = {}

    def subscribe(self, topic: str, handler: Callable[[Event], Any]) -> None:
        if not isinstance(topic, str) or not topic.strip():
            raise ValueError("topic must be a non-empty string")
        if not callable(handler):
            raise TypeError("handler must be callable")
        handlers = self._subscribers.setdefault(topic, [])
        if handler in handlers:
            raise ValueError("handler already subscribed to topic")
        handlers.append(handler)

    def unsubscribe(self, topic: str, handler: Callable[[Event], Any]) -> None:
        if topic not in self._subscribers or handler not in self._subscribers[topic]:
            raise ValueError("handler is not subscribed to topic")
        self._subscribers[topic].remove(handler)
        if not self._subscribers[topic]:
            del self._subscribers[topic]

    def publish(self, event: Event) -> List[Exception]:
        if not isinstance(event, Event):
            raise TypeError("event must be an Event instance")
        failures: List[Exception] = []
        for handler in list(self._subscribers.get(event.topic, [])):
            try:
                handler(event)
            except Exception as exc:
                failures.append(exc)
        return failures

    def subscriber_count(self, topic: str) -> int:
        return len(self._subscribers.get(topic, []))
