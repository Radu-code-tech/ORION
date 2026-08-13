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
