"""Append-only report store: immutable extracted evidence, one row per contact.

Day-1 warm-up: the dataclass and signatures ship; you implement the bodies to
the contracts in the docstrings below (acceptance scenarios STORE-R* in
features/reports.feature). Reports never change after `add`, so conflicting
claims coexist by construction: no update, no delete. Keep the store a dict.

`path` is a write-only JSON log for debugging: the constructor clears it (each
session starts fresh) and every mutation rewrites it. It is never read back.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class Report:
    """One extracted contact - the minimal starting schema. Extraction fields you
    discover in later stages (severity, headcount, event_time, source_type) are
    deliberately absent; add them when a scenario forces your hand. `coords` and
    `tick` are reconciliation aids: the reported location resolved to a public
    point, and delivered_at for the time-window query."""

    contact_id: str
    # Raw location, verbatim from the contact envelope (a building_id or a public
    # point). The intake bot is graded on this field in a later stage
    # (report.schema.json + the INT-* scenarios), so it stays even though the store
    # itself filters on the resolved `coords`.
    reported_location: dict
    incident_type: str
    coords: tuple[float, float] | None = None
    tick: int | None = None
    notes: str = ""


class ReportStore:
    def __init__(self, path: Path | None = None):
        self._by_id: dict[str, Report] = {}  # dicts preserve insertion order
        self._path = path  # write-only debug log; clear it here if it exists

    def add(self, report: Report) -> Report:
        """Append evidence and return it (STORE-R1, STORE-R2). Idempotent by
        contact_id: a re-add of an existing contact_id is IGNORED (return the
        original, never overwrite - the store has no update). Log when
        path-backed."""
        raise NotImplementedError("warm-up: add")

    def get(self, contact_id: str) -> Report | None:
        """Return the stored report for contact_id, or None (STORE-R1)."""
        raise NotImplementedError("warm-up: get")

    def all(self) -> list[Report]:
        """All reports in insertion order."""
        raise NotImplementedError("warm-up: all")

    def find_reports(
        self,
        near: tuple[float, float] | None = None,
        radius: float | None = None,
        start: int | None = None,
        end: int | None = None,
    ) -> list[Report]:
        """Reports within `radius` of `near` AND with start <= tick <= end, in
        insertion order (STORE-R3, STORE-R4, STORE-R5). Edge cases: `near` and
        `radius` are a pair - both required for the spatial filter; a report
        whose coords is None is excluded while the spatial filter is active. A
        None time bound is open; a report whose tick is None is excluded when a
        time bound is set."""
        raise NotImplementedError("warm-up: find_reports")
