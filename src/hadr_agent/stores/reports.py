"""Append-only report store: immutable extracted evidence, one row per contact.

Day-1 warm-up: the dataclass and signatures ship; you implement the bodies to
the contracts in the docstrings below (acceptance scenarios STORE-R* in
features/reports.feature). Reports never change after `add`, so conflicting
claims coexist by construction: no update, no delete. Keep the store a dict.

`path` is a write-only JSON log for debugging: the constructor clears it (each
session starts fresh) and every mutation rewrites it. It is never read back, and
it is best-effort - a debug aid must never be able to abort a mutation.
"""

from __future__ import annotations

import json
import logging
import math
from dataclasses import asdict, dataclass
from pathlib import Path

log = logging.getLogger(__name__)


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
        if path is not None:
            try:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.unlink(missing_ok=True)
            except OSError as exc:  # a debug log is never worth failing startup
                log.warning("report debug log unavailable at %s: %s", path, exc)
                self._path = None

    def add(self, report: Report) -> Report:
        """Append evidence and return it (STORE-R1, STORE-R2). Idempotent by
        contact_id: a re-add of an existing contact_id is IGNORED (return the
        original, never overwrite - the store has no update). Log when
        path-backed."""
        existing = self._by_id.get(report.contact_id)
        if existing is not None:
            return existing
        self._by_id[report.contact_id] = report
        self._log()
        return report

    def get(self, contact_id: str) -> Report | None:
        """Return the stored report for contact_id, or None (STORE-R1)."""
        return self._by_id.get(contact_id)

    def all(self) -> list[Report]:
        """All reports in insertion order."""
        return list(self._by_id.values())

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
        found: list[Report] = []
        for report in self._by_id.values():
            # Spatial filter: only active when both halves of the pair are given.
            # Phrased as `not (dist <= radius)` rather than `dist > radius` so a
            # NaN coordinate is excluded rather than silently matching everything.
            if (
                near is not None
                and radius is not None
                and (
                    report.coords is None
                    or not math.dist(report.coords, near) <= radius
                )
            ):
                continue
            # Time filter: active as soon as either bound is set.
            if start is not None or end is not None:
                if report.tick is None:
                    continue
                if start is not None and report.tick < start:
                    continue
                if end is not None and report.tick > end:
                    continue
            found.append(report)
        return found

    def _log(self) -> None:
        """Rewrite the whole debug log. Write-only, and best-effort: extracted
        fields are free-form LLM output, so `default=str` keeps an odd value
        readable rather than unserializable, and any remaining failure is warned
        about rather than raised - the mutation has already happened, and a
        debugging aid must not be able to wedge the store."""
        if self._path is None:
            return
        try:
            rows = [asdict(r) for r in self._by_id.values()]
            self._path.write_text(
                json.dumps(rows, indent=2, default=str), encoding="utf-8"
            )
        except (OSError, TypeError, ValueError) as exc:
            log.warning("report debug log write failed: %s", exc)
