"""Mutable incident store: the agent's beliefs about suspected fires.

Day-1 warm-up: the dataclass and signatures ship; you implement the bodies to
the contracts in the docstrings below (acceptance scenarios STORE-I* in
features/incidents.feature). Unlike reports, incidents are revised as evidence
accrues: `update` merges new belief, `link` attaches supporting reports,
`close` retires an incident with a reason. The simulator never sees this store;
it is pure participant memory. Keep the store a dict.

`path` is a write-only JSON log for debugging: the constructor clears it (each
session starts fresh) and every mutation rewrites it. It is never read back.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

# Belief lifecycle.
STATUS_OPEN = "open"
STATUS_CLOSED = "closed"


@dataclass
class Incident:
    """The minimal starting belief. Fields you discover as evidence accrues
    (building_id, severity, headcount, contradiction, close_reason, a
    confidence/belief-strength of your own design, ...) are deliberately absent -
    add them when a scenario forces your hand. `open` and `update` take **fields,
    so the belief grows without changing their signatures."""

    incident_id: str
    incident_type: str
    coords: tuple[float, float]
    status: str = STATUS_OPEN
    report_ids: list[str] = field(default_factory=list)
    created_tick: int = 0
    updated_tick: int = 0


class IncidentStore:
    def __init__(self, path: Path | None = None):
        # `_seq` backs fresh ids ("inc-1", "inc-2", ...).
        self._by_id: dict[str, Incident] = {}
        self._seq = 0
        self._path = path  # write-only debug log; clear it here if it exists

    def open(
        self,
        incident_type: str,
        coords: tuple[float, float],
        tick: int,
        building_id: str | None = None,
        **fields,
    ) -> Incident:
        """Create a new incident with a fresh unique id, status open, and
        created/updated tick = tick (STORE-I1). Extra belief fields (severity,
        headcount, ...) arrive as kwargs. Log. Return it."""
        raise NotImplementedError("warm-up: open")

    def get(self, incident_id: str) -> Incident | None:
        """Return the incident, or None (STORE-I1)."""
        raise NotImplementedError("warm-up: get")

    def all(self) -> list[Incident]:
        """All incidents."""
        raise NotImplementedError("warm-up: all")

    def find(
        self,
        near: tuple[float, float] | None = None,
        radius: float | None = None,
        incident_type: str | None = None,
        status: str | None = STATUS_OPEN,
    ) -> list[Incident]:
        """Incidents matching an optional status (default open; status=None
        matches any), an optional incident_type, and an optional spatial window
        (near+radius together), sorted NEAREST FIRST when `near` is given
        (STORE-I2, STORE-I5, STORE-I6). Signposts reconciliation's match step."""
        raise NotImplementedError("warm-up: find")

    def update(
        self, incident_id: str, tick: int | None = None, **fields
    ) -> Incident:
        """Set the given belief fields on an incident (an unknown field name is
        an error), bump updated_tick when `tick` is given, log, return it
        (STORE-I3)."""
        raise NotImplementedError("warm-up: update")

    def link(
        self, incident_id: str, report_id: str, tick: int | None = None
    ) -> Incident:
        """Attach a supporting report_id (idempotent - no duplicates), bump
        updated_tick when `tick` is given, log, return it (STORE-I4)."""
        raise NotImplementedError("warm-up: link")

    def close(
        self, incident_id: str, reason: str, tick: int | None = None
    ) -> Incident:
        """Retire an incident: status closed, close_reason = reason, bump
        updated_tick when `tick` is given, log. A closed incident is excluded
        from find(status="open") (STORE-I5)."""
        raise NotImplementedError("warm-up: close")
