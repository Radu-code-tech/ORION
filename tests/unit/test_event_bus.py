from src.event.event_bus import Event, EventBus


def test_publish_calls_subscribers_in_registration_order():
    bus = EventBus()
    calls = []

    bus.subscribe("market.tick", lambda e: calls.append(("a", e.payload)))
    bus.subscribe("market.tick", lambda e: calls.append(("b", e.payload)))

    assert bus.publish(Event("market.tick", {"price": 100})) == []
    assert calls == [
        ("a", {"price": 100}),
        ("b", {"price": 100}),
    ]


def test_duplicate_subscription_is_rejected():
    bus = EventBus()
    handler = lambda e: None

    bus.subscribe("risk.alert", handler)

    try:
        bus.subscribe("risk.alert", handler)
        assert False
    except ValueError:
        pass


def test_unsubscribe_removes_handler():
    bus = EventBus()
    calls = []

    handler = lambda e: calls.append(e.payload)

    bus.subscribe("risk.alert", handler)
    bus.unsubscribe("risk.alert", handler)

    bus.publish(Event("risk.alert", 1))

    assert calls == []
    assert bus.subscriber_count("risk.alert") == 0


def test_invalid_topic_and_handler_are_rejected():
    bus = EventBus()

    try:
        bus.subscribe("", lambda e: None)
        assert False
    except ValueError:
        pass

    try:
        bus.subscribe("x", "not-callable")
        assert False
    except TypeError:
        pass


def test_subscriber_failure_is_isolated():
    bus = EventBus()
    calls = []

    def failing(event):
        raise RuntimeError("boom")

    def healthy(event):
        calls.append(event.payload)

    bus.subscribe("system.event", failing)
    bus.subscribe("system.event", healthy)

    failures = bus.publish(Event("system.event", 7))

    assert len(failures) == 1
    assert isinstance(failures[0], RuntimeError)
    assert calls == [7]


def test_event_rejects_empty_topic():
    try:
        Event("")
        assert False
    except ValueError:
        pass


def test_event_rejects_non_string_topic():
    try:
        Event(None)
        assert False
    except ValueError:
        pass


def test_publish_rejects_non_event():
    bus = EventBus()

    try:
        bus.publish("not-an-event")
        assert False
    except TypeError:
        pass


def test_unsubscribe_rejects_unknown_handler():
    bus = EventBus()

    handler = lambda e: None

    try:
        bus.unsubscribe("risk.alert", handler)
        assert False
    except ValueError:
        pass


def test_subscriber_count_rejects_invalid_topic():
    bus = EventBus()

    try:
        bus.subscriber_count("")
        assert False
    except ValueError:
        pass


def test_publish_uses_subscriber_snapshot():
    bus = EventBus()
    calls = []

    def first(event):
        calls.append("first")
        bus.subscribe("snapshot.test", third)

    def second(event):
        calls.append("second")

    def third(event):
        calls.append("third")

    bus.subscribe("snapshot.test", first)
    bus.subscribe("snapshot.test", second)

    bus.publish(Event("snapshot.test"))

    assert calls == ["first", "second"]
    assert bus.subscriber_count("snapshot.test") == 3


def test_failed_subscriber_does_not_stop_later_subscribers():
    bus = EventBus()
    calls = []

    def failing(event):
        calls.append("failed")
        raise RuntimeError("failure")

    def healthy_one(event):
        calls.append("healthy_one")

    def healthy_two(event):
        calls.append("healthy_two")

    bus.subscribe("failure.test", failing)
    bus.subscribe("failure.test", healthy_one)
    bus.subscribe("failure.test", healthy_two)

    failures = bus.publish(Event("failure.test"))

    assert calls == [
        "failed",
        "healthy_one",
        "healthy_two",
    ]

    assert len(failures) == 1
    assert isinstance(failures[0], RuntimeError)


def test_unsubscribe_deletes_empty_topic():
    bus = EventBus()

    handler = lambda e: None

    bus.subscribe("temporary.topic", handler)

    assert bus.subscriber_count("temporary.topic") == 1

    bus.unsubscribe("temporary.topic", handler)

    assert bus.subscriber_count("temporary.topic") == 0