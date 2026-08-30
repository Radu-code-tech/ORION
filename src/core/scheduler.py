"""OR-CORE-001: deterministic application scheduler.

The scheduler coordinates registered ORION jobs. It contains no market,
trading, risk, execution, or decision logic.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Callable, Protocol


class Clock(Protocol):
    def now(self) -> datetime: ...


class SystemClock:
    def now(self) -> datetime:
        return datetime.now(timezone.utc)


@dataclass(frozen=True)
class ScheduledJob:
    name: str
    interval_seconds: float
    handler: Callable[[], None]
    next_run: datetime


class Scheduler:
    """Minimal deterministic scheduler for ORION internal jobs."""

    def __init__(self, clock: Clock | None = None) -> None:
        self._clock = clock or SystemClock()
        self._jobs: dict[str, ScheduledJob] = {}
        self._running = False

    @property
    def running(self) -> bool:
        return self._running

    def add_job(
        self,
        name: str,
        interval_seconds: float,
        handler: Callable[[], None],
    ) -> None:
        if not isinstance(name, str) or not name.strip():
            raise ValueError("job name must not be empty")

        if not isinstance(interval_seconds, (int, float)):
            raise ValueError("interval_seconds must be numeric")

        if not math.isfinite(float(interval_seconds)):
            raise ValueError("interval_seconds must be finite")

        if interval_seconds <= 0:
            raise ValueError("interval_seconds must be greater than zero")

        if not callable(handler):
            raise ValueError("handler must be callable")

        if name in self._jobs:
            raise ValueError(f"job already exists: {name}")

        self._jobs[name] = ScheduledJob(
            name=name,
            interval_seconds=float(interval_seconds),
            handler=handler,
            next_run=self._clock.now(),
        )

    def remove_job(self, name: str) -> None:
        self._jobs.pop(name, None)

    def start(self) -> None:
        self._running = True

    def stop(self) -> None:
        self._running = False

    def tick(self) -> list[str]:
        """Run due jobs once and return their names.

        The scheduler deliberately does not sleep. A higher-level runtime can
        call tick() at its chosen cadence, making this component deterministic
        and easy to test.

        If a handler raises an exception, the exception is propagated and the
        job is not rescheduled as a successful execution.
        """
        if not self._running:
            return []

        now = self._clock.now()
        executed: list[str] = []

        for job in list(self._jobs.values()):
            if now < job.next_run:
                continue

            job.handler()

            executed.append(job.name)

            self._jobs[job.name] = ScheduledJob(
                name=job.name,
                interval_seconds=job.interval_seconds,
                handler=job.handler,
                next_run=now + timedelta(seconds=job.interval_seconds),
            )

        return executed