"""Deterministic reconciliation: reports + truck vision -> incident beliefs.

No LLM. This is the stage-3 lesson: match each new report to an existing incident
by spatial proximity, time window, and type compatibility, then decide an outcome;
truck-vision observations are ground truth that can confirm or close an incident.

Ships: the outcome vocabulary (constants + Outcome) and the two function
signatures. HOLES: the matching/decision logic and the tuning thresholds. Callers
resolve every report/observation location to a public point (via
`building_to_coords`) BEFORE calling in, so this module stays pure and testable
without the engine.

Decision table your reconcile_reports should implement (scenarios REC-*):

  incident_type  match found?          action
  -------------  --------------------  -------------------------------------------
  none           no open incident near IGNORED (a denial opens nothing)
  none           open incident near    FALSE_ALARM: link the report, keep the
                                        incident open (uncertainty retained, never
                                        closed by a denial alone)
  fire/unknown   no match              OPEN a new incident (link the report)
  fire/unknown   match                 link, then merge:
                                          unknown incident + fire report -> UPDATE type
                                          higher severity band            -> UPDATE
                                          headcount all_out vs trapped    -> CONTRADICTION
                                            (retain the MORE CAUTIOUS belief, flag it)
                                          new headcount, none held yet    -> UPDATE (adopt it)
                                          otherwise                       -> DUPLICATE

reconcile_vision (scenarios REC-6/REC-7):
  a building seen `normal`    -> close a co-located incident (RESOLVED_VISION)
  a building seen `burning`   -> confirm/open an incident (CONFIRMED_VISION)
  a building seen `collapsed` -> terminal: the building is lost, no dispatch
    target. BuildingStatus has these three values; the reference takes no
    reconcile action on `collapsed` (nothing left to serve).
"""

from __future__ import annotations

from dataclasses import dataclass

from .stores.incidents import IncidentStore
from .stores.reports import Report, ReportStore

# HOLE (stage 3): tune these thresholds. A report within MATCH_RADIUS world units
# and TIME_WINDOW ticks of an incident may be the same event.
MATCH_RADIUS: float | None = None
TIME_WINDOW: int | None = None

# Outcome tags (also the reconciliation log vocabulary). Tests and scenarios
# reference these, so they ship with stable values.
OPEN = "open"
UPDATE = "update"
DUPLICATE = "link-duplicate"
CONTRADICTION = "contradiction-retain"
FALSE_ALARM = "possible-false-alarm"
RESOLVED_VISION = "resolved-by-vision"
CONFIRMED_VISION = "confirmed-by-vision"
IGNORED = "ignored"


@dataclass
class Outcome:
    action: str
    incident_id: str | None
    contact_id: str | None = None
    detail: str = ""


def reconcile_reports(
    reports: list[Report],
    incidents: IncidentStore,
    report_store: ReportStore,
    tick: int,
) -> list[Outcome]:
    """HOLE (stage 1/3): fold each new report into the incident store per the
    decision table above; append every report to `report_store`. Reports carry a
    resolved `coords`. Return one Outcome per report (for logging)."""
    raise NotImplementedError("stage 3: implement deterministic reconciliation")


def reconcile_vision(
    observations: list[dict],
    incidents: IncidentStore,
    tick: int,
    coords_of: dict[str, tuple[float, float]],
) -> list[Outcome]:
    """HOLE (stage 3): apply truck-vision building statuses (ground truth).
    `observations` are TruckObservation payload dicts; `coords_of` maps
    building_id -> point. See the vision rows of the decision table."""
    raise NotImplementedError("stage 3: apply truck vision to incident beliefs")
