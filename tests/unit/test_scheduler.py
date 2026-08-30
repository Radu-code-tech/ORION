from datetime import datetime, timedelta, timezone

import pytest

from src.core.scheduler import Scheduler


class FakeClock:
    def __init__(self) -> None:
        self.current = datetime(2026, 1, 1, tzinfo=timezone.utc)

    def now(self):
        return self.current

    def advance(self, seconds: float):
        self.current += timedelta(seconds=seconds)


def test_scheduler_starts_and_runs_due_job_once():
    clock = FakeClock()
    calls = []
    scheduler = Scheduler(clock)
    scheduler.add_job("heartbeat", 10, lambda: calls.append("heartbeat"))

    assert scheduler.tick() == []

    scheduler.start()

    assert scheduler.tick() == ["heartbeat"]
    assert calls == ["heartbeat"]

    clock.advance(5)
    assert scheduler.tick() == []

    clock.advance(5)
    assert scheduler.tick() == ["heartbeat"]


def test_scheduler_rejects_invalid_jobs():
    scheduler = Scheduler(FakeClock())

    with pytest.raises(ValueError):
        scheduler.add_job("", 10, lambda: None)

    with pytest.raises(ValueError):
        scheduler.add_job("bad", 0, lambda: None)


def test_scheduler_rejects_duplicate_job():
    scheduler = Scheduler(FakeClock())

    scheduler.add_job("x", 1, lambda: None)

    with pytest.raises(ValueError):
        scheduler.add_job("x", 1, lambda: None)


def test_scheduler_can_remove_job():
    scheduler = Scheduler(FakeClock())

    scheduler.add_job("x", 1, lambda: None)
    scheduler.remove_job("x")

    scheduler.start()

    assert scheduler.tick() == []


def test_scheduler_rejects_non_callable_handler():
    scheduler = Scheduler(FakeClock())

    with pytest.raises(ValueError):
        scheduler.add_job("bad-handler", 1, None)


def test_scheduler_rejects_nan_interval():
    scheduler = Scheduler(FakeClock())

    with pytest.raises(ValueError):
        scheduler.add_job("nan-job", float("nan"), lambda: None)


def test_scheduler_rejects_infinite_interval():
    scheduler = Scheduler(FakeClock())

    with pytest.raises(ValueError):
        scheduler.add_job("inf-job", float("inf"), lambda: None)


def test_scheduler_preserves_job_execution_order():
    clock = FakeClock()
    calls = []

    scheduler = Scheduler(clock)

    scheduler.add_job("first", 10, lambda: calls.append("first"))
    scheduler.add_job("second", 10, lambda: calls.append("second"))
    scheduler.add_job("third", 10, lambda: calls.append("third"))

    scheduler.start()

    assert scheduler.tick() == ["first", "second", "third"]
    assert calls == ["first", "second", "third"]


def test_scheduler_does_not_reschedule_failed_job():
    clock = FakeClock()
    calls = []

    def failing_job():
        calls.append("failed")
        raise RuntimeError("job failure")

    scheduler = Scheduler(clock)
    scheduler.add_job("failure", 10, failing_job)
    scheduler.start()

    with pytest.raises(RuntimeError, match="job failure"):
        scheduler.tick()

    assert calls == ["failed"]

    clock.advance(10)

    with pytest.raises(RuntimeError, match="job failure"):
        scheduler.tick()

    assert calls == ["failed", "failed"]


def test_scheduler_stop_prevents_future_execution():
    clock = FakeClock()
    calls = []

    scheduler = Scheduler(clock)

    scheduler.add_job("job", 10, lambda: calls.append("job"))

    scheduler.start()
    assert scheduler.tick() == ["job"]

    scheduler.stop()

    clock.advance(10)

    assert scheduler.tick() == []
    assert calls == ["job"]