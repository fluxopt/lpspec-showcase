"""The queue: one solve at a time, in a thread, writing where the readers read.

Serial on purpose. A solve is CPU-bound and the whole point of the archive is
that it lands whole, so two of them racing on one scenario's directory is a
failure mode with nothing to gain. What is *not* held here is history: a
finished run leaves no entry, because the archive it wrote is the entry.
"""

from __future__ import annotations

import queue
import threading
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from showcase.solve import solve


@dataclass(frozen=True)
class Pending:
    """A scenario the queue has accepted and the archive does not yet describe.

    Attributes:
        scenario: Which scenario was asked for.
        state: ``queued``, ``running`` or ``failed`` — never ``archived``, which
            is a fact about the directory rather than about this object.
        submitted: When the request arrived, UTC.
        error: What went wrong, for ``failed`` only.
    """

    scenario: str
    state: str
    submitted: datetime
    error: str | None = None


class Queue:
    """Accepts scenarios and solves them one at a time, into *runs*.

    The worker starts with the first submission and runs as a daemon, so a
    server that is never asked for a solve never starts one.
    """

    def __init__(self, runs: Path) -> None:
        self.runs = runs
        self._work: queue.Queue[str] = queue.Queue()
        self._pending: dict[str, Pending] = {}
        self._lock = threading.Lock()
        self._worker: threading.Thread | None = None

    def submit(self, scenario: str) -> Pending:
        """Accept *scenario*, or raise ``KeyError`` if one is already in flight for it."""
        with self._lock:
            if scenario in self._pending and self._pending[scenario].state in ('queued', 'running'):
                raise KeyError(scenario)
            entry = Pending(scenario, 'queued', datetime.now(UTC))
            self._pending[scenario] = entry
            if self._worker is None:
                self._worker = threading.Thread(target=self._drain, name='showcase-solve', daemon=True)
                self._worker.start()
        self._work.put(scenario)
        return entry

    def in_flight(self) -> dict[str, Pending]:
        """Every scenario this process has been asked for and not yet archived."""
        with self._lock:
            return dict(self._pending)

    def _drain(self) -> None:
        while True:
            scenario = self._work.get()
            self._mark(scenario, 'running')
            try:
                solve(scenario, self.runs, replace=True)
            except Exception as error:  # the request is answered by GET, so the thread must survive it
                self._mark(scenario, 'failed', f'{type(error).__name__}: {error}')
            else:
                with self._lock:
                    self._pending.pop(scenario, None)
            finally:
                self._work.task_done()

    def _mark(self, scenario: str, state: str, error: str | None = None) -> None:
        with self._lock:
            was = self._pending[scenario]
            self._pending[scenario] = Pending(was.scenario, state, was.submitted, error)
