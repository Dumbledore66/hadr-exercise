"""Mutable incident store: the agent's beliefs about suspected fires.

Day-1 warm-up: the dataclass and signatures ship; you implement the bodies to
the contracts in the docstrings below (acceptance scenarios STORE-I* in
features/incidents.feature). Unlike reports, incidents are revised as evidence
accrues: `update` merges new belief, `link` attaches supporting reports,
`close` retires an incident with a reason. The simulator never sees this store;
it is pure participant memory. Keep the store a dict.

`path` is a write-only JSON log for debugging: the constructor clears it (each
session starts fresh) and every mutation rewrites it. It is never read back, and
it is best-effort - a debug aid must never be able to abort a mutation.
"""

from __future__ import annotations

import json
import logging
import math
from dataclasses import asdict, dataclass, field
from dataclasses import fields as dataclass_fields
from pathlib import Path

log = logging.getLogger(__name__)

# Belief lifecycle. These two are the ONLY legal values of `status`: find()
# selects on them, so a free-text status would drop an incident out of both
# find(status="open") and find(status="closed") and strand it.
STATUS_OPEN = "open"
STATUS_CLOSED = "closed"
_STATUSES = frozenset({STATUS_OPEN, STATUS_CLOSED})


class UnknownIncidentError(LookupError):
    """A mutator addressed an incident id the store does not hold.

    Deliberately NOT a KeyError: dispatch._run_tool already catches KeyError to
    mean "the model omitted a tool argument", and would mislabel this one.
    """


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
    # Grown by the warm-up: `building_id` is already a named argument of open();
    # `severity` is asserted by STORE-I1; `close_reason` is close()'s contract.
    # `notes` is not forced by a warm-up scenario but dispatch.file_incident_update
    # already writes it, and update() rejects unknown field names.
    building_id: str | None = None
    # A bare band ("high"), NOT the report's {"value": ...} payload - REC-2 asserts
    # the bare string, so normalizing the claim shape is reconcile's job, not the
    # store's. Keeping the annotation narrow is what forces that decision.
    severity: str | None = None
    close_reason: str | None = None
    notes: str = ""


# Settable belief names, for update()'s unknown-field check.
_FIELD_NAMES = {f.name for f in dataclass_fields(Incident)}


def _check_status(status: object) -> None:
    """Guard the lifecycle vocabulary. `find` selects on exact status, so any
    other value makes the incident invisible to every query the agent runs."""
    if status not in _STATUSES:
        raise ValueError(
            f"status must be one of {sorted(_STATUSES)}, got {status!r}"
        )


class IncidentStore:
    def __init__(self, path: Path | None = None):
        # `_seq` backs fresh ids ("inc-1", "inc-2", ...).
        self._by_id: dict[str, Incident] = {}
        self._seq = 0
        self._path = path  # write-only debug log; clear it here if it exists
        if path is not None:
            try:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.unlink(missing_ok=True)
            except OSError as exc:  # a debug log is never worth failing startup
                log.warning("incident debug log unavailable at %s: %s", path, exc)
                self._path = None

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
        if "status" in fields:
            # open() creates an OPEN incident by definition; a born-closed one is
            # invisible to find() from the start. Retiring goes through close(),
            # which also records the reason.
            raise ValueError("open() always creates an open incident; use close() to retire one")
        self._seq += 1
        incident = Incident(
            incident_id=f"inc-{self._seq}",
            incident_type=incident_type,
            coords=coords,
            created_tick=tick,
            updated_tick=tick,
            building_id=building_id,
            **fields,
        )
        self._by_id[incident.incident_id] = incident
        self._log()
        return incident

    def get(self, incident_id: str) -> Incident | None:
        """Return the incident, or None (STORE-I1)."""
        return self._by_id.get(incident_id)

    def all(self) -> list[Incident]:
        """All incidents."""
        return list(self._by_id.values())

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
        found: list[Incident] = []
        for incident in self._by_id.values():
            if status is not None and incident.status != status:
                continue
            if incident_type is not None and incident.incident_type != incident_type:
                continue
            # Spatial window: only active when both halves of the pair are given.
            if (
                near is not None
                and radius is not None
                and not math.dist(incident.coords, near) <= radius
            ):
                continue
            found.append(incident)
        if near is not None:
            # Stable sort over an insertion-ordered list, so equidistant
            # incidents keep the order they were opened in.
            found.sort(key=lambda i: math.dist(i.coords, near))
        return found

    def update(
        self, incident_id: str, tick: int | None = None, **fields
    ) -> Incident:
        """Set the given belief fields on an incident (an unknown field name is
        an error), bump updated_tick when `tick` is given, log, return it
        (STORE-I3). All-or-nothing: names are validated BEFORE the first write,
        so a rejected update leaves the belief untouched."""
        incident = self._require(incident_id)
        unknown = sorted(set(fields) - _FIELD_NAMES)
        if unknown:
            raise ValueError(
                "unknown incident field(s): " + ", ".join(repr(n) for n in unknown)
            )
        if "status" in fields:
            _check_status(fields["status"])
        for name, value in fields.items():
            setattr(incident, name, value)
        if tick is not None:
            incident.updated_tick = tick
        self._log()
        return incident

    def link(
        self, incident_id: str, report_id: str, tick: int | None = None
    ) -> Incident:
        """Attach a supporting report_id (idempotent - no duplicates), bump
        updated_tick when `tick` is given, log, return it (STORE-I4)."""
        incident = self._require(incident_id)
        if report_id not in incident.report_ids:
            incident.report_ids.append(report_id)
        if tick is not None:
            incident.updated_tick = tick
        self._log()
        return incident

    def close(
        self, incident_id: str, reason: str, tick: int | None = None
    ) -> Incident:
        """Retire an incident: status closed, close_reason = reason, bump
        updated_tick when `tick` is given, log. A closed incident is excluded
        from find(status="open") (STORE-I5)."""
        incident = self._require(incident_id)
        incident.status = STATUS_CLOSED
        incident.close_reason = reason
        if tick is not None:
            incident.updated_tick = tick
        self._log()
        return incident

    def _require(self, incident_id: str) -> Incident:
        """The mutators address an incident by id; an unknown id is a caller bug,
        not a belief state, so it raises rather than returning None like get()."""
        incident = self._by_id.get(incident_id)
        if incident is None:
            raise UnknownIncidentError(incident_id)
        return incident

    def _log(self) -> None:
        """Rewrite the whole debug log. Write-only, and best-effort: a belief the
        agent invented is free-form, so `default=str` keeps an odd value readable
        rather than unserializable, and any remaining failure is warned about
        rather than raised - the mutation has already happened, and a debugging
        aid must not be able to wedge the store."""
        if self._path is None:
            return
        try:
            rows = [asdict(i) for i in self._by_id.values()]
            self._path.write_text(
                json.dumps(rows, indent=2, default=str), encoding="utf-8"
            )
        except (OSError, TypeError, ValueError) as exc:
            log.warning("incident debug log write failed: %s", exc)
