from src.event.event_bus import Event, EventBus

def test_publish_calls_subscribers_in_registration_order():
    bus = EventBus(); calls = []
    bus.subscribe("market.tick", lambda e: calls.append(("a", e.payload)))
    bus.subscribe("market.tick", lambda e: calls.append(("b", e.payload)))
    assert bus.publish(Event("market.tick", {"price": 100})) == []
    assert calls == [("a", {"price": 100}), ("b", {"price": 100})]

def test_duplicate_subscription_is_rejected():
    bus = EventBus(); handler = lambda e: None
    bus.subscribe("risk.alert", handler)
    try:
        bus.subscribe("risk.alert", handler)
        assert False
    except ValueError:
        pass

def test_unsubscribe_removes_handler():
    bus = EventBus(); calls = []
    handler = lambda e: calls.append(e.payload)
    bus.subscribe("risk.alert", handler)
    bus.unsubscribe("risk.alert", handler)
    bus.publish(Event("risk.alert", 1))
    assert calls == []
    assert bus.subscriber_count("risk.alert") == 0

def test_invalid_topic_and_handler_are_rejected():
    bus = EventBus()
    try:
        bus.subscribe("", lambda e: None); assert False
    except ValueError:
        pass
    try:
        bus.subscribe("x", "not-callable"); assert False
    except TypeError:
        pass

def test_subscriber_failure_is_isolated():
    bus = EventBus(); calls = []
    def failing(event): raise RuntimeError("boom")
    def healthy(event): calls.append(event.payload)
    bus.subscribe("system.event", failing)
    bus.subscribe("system.event", healthy)
    failures = bus.publish(Event("system.event", 7))
    assert len(failures) == 1
    assert isinstance(failures[0], RuntimeError)
    assert calls == [7]
