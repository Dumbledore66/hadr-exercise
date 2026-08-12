# Dispatch queue-sense agent — product brief

An agent that tells a fire dispatch operator how many things are actually happening during a call
surge. This brief records the problem, the boundary, and the first build, as agreed by the team.

---

## Primary user

A fire dispatch operator working a live board during an incident surge. Not an analyst, not a
commander — the person taking calls and committing units in the moment, whose attention is the
scarce resource and who is judged on what they sent and when.

## Their problem

During a surge, calls arrive faster than they can be reconciled, and most are about things the
operator already knows. Their first question is not "what should I send?" but **"how many things are
actually happening?"** Answering it means holding a shifting map of which caller is describing which
event, across inconsistent wording, partial addresses, second-hand accounts, and reports that arrive
well after the thing they describe. That reconciliation happens in the operator's head, under time
pressure, and it degrades exactly when volume is highest.

## The decision the system supports

Two layers, built in order.

1. **What exists.** Whether an incoming report describes something already on the board or something
   new — and consequently what the board says is happening right now. The system commits to an
   answer rather than presenting options.
2. **What follows from it** (specified, not in the first build). Which unit goes where, with
   graduated authority: routine allocations execute on the agent's own authority, consequential ones
   go to the operator.

## The most consequential failure

Two candidates, in different units. They need different evidence to weigh, and should not be ranked
by instinct.

- **Fragmentation** — one event appearing as several board entries during a surge. Frequent,
  individually survivable, and it scales with load: calls outnumber events several to one, so this
  multiplies while other errors stay flat. It splits attention across phantom incidents and invites
  duplicate commitment. **This is the failure the first build is judged on.**
- **A consequential decision mis-filed as routine** — rare, unsupervised, and discovered late.
  Belongs to the allocation layer.

**Accepted cost, recorded as deliberate:** a real incident held below the promotion bar and never
surfaced. The team chose a board that earns trust by refusing to cry wolf. This will look like
underperformance the first time a held report turns out to have been real.

## The human–agent boundary

**Agent owns:** what exists. Grouping reports onto events; holding unevidenced reports silently;
promoting them when evidence accumulates. Later: routine allocation.

**Reasoning is retained, not displayed.** The live board carries entries, not their derivation.
Which reports back an entry, from which channels, at what times, and what contradicts it stays
reconstructible for review, handover, and inquiry — but does not occupy the working screen, on the
grounds that a busy operator will not read it in the moment it was built for. Retention is not
optional: two commitments below depend on it.

**Operator owns:** priority and commitment. Later, specifically: abandoning an incident, pulling a
committed unit, and acting on evidence the agent itself rates as thin, plus override on any
allocation the agent proposes or makes.

**The board's structure is not overridable.** The operator cannot split an entry the agent merged or
merge two it kept apart. Groupings have one author, so the board always means one thing, and the
fragmentation measure stays honest rather than being quietly repaired by the person it is measured
against. The cost is that a wrong grouping persists for the whole incident, unexplained on the
screen and uncorrectable by the only person who might know better.

**Escalation rule** (allocation layer): keyed on stakes and irreversibility, with unknown stakes
treated as high. Note the split — irreversibility the agent estimates well, since commitment length
follows from mechanics; stakes it estimates badly, since they arrive only as claimed headcounts.

**The escape hatch.** The operator may commit a unit anywhere, regardless of what the board says,
and doing so is recorded as acting against the picture. Board authorship stays clean while
disagreement has somewhere to go, so a board the operator believes is wrong never blocks a correct
response.

**Consequence to design around:** because groupings are final and their reasoning is off the working
screen, the agent's judgment is both unexplained in the moment and uncorrectable. Every merge is
irreversible within an incident, and the bar for making one is materially higher than in a system
that allowed correction. Recorded departures are the compensating instrument — the only channel
through which operator disagreement becomes visible.

## Success measures

**First build**

- **Entries per event during a surge** — the ratio the operator feels. One is the target.
- **Phantom rate** — entries corresponding to nothing real, counted after the fact.
- **Promotion latency** — first report of a real event to its appearance on the board. Where the
  accepted cost of the no-phantom stance becomes measurable rather than theoretical.
- **Operator agreement** — how often the operator, reviewing afterwards, endorses a grouping. Only
  computable against the retained trail, since endorsing a grouping means seeing why it was made.
- **Departure rate** — how often the operator commits a unit against the picture. With correction
  removed, this is the sole live signal of disagreement, and the richest pointer to where the
  grouping is wrong. Rising departures mean the board is being worked around rather than used.

**Allocation layer**

- **Share of allocations escalated.** As this approaches all of them, graduated authority is nominal
  and you are back to a full approval gate without having chosen one.
- **Escalations the operator overturned** — the only read on whether the agent's sense of
  "consequential" matches theirs.

## The first useful slice

Given a burst of calls, tell the operator **how many distinct events they are looking at, and which
calls belong to each.**

Nothing else: not whether each is real, not how severe, not who to send. It answers the operator's
actual first question, and it is the substrate everything else runs on — evidence cannot accumulate
toward promotion until reports are attributed to events, and allocation cannot be sane on a
fragmented board.

**Built as a probe, not as a candidate system.** Its purpose is to establish what evidence would be
needed to judge the design, not to be the design. It succeeds if it answers: can event count be
established as ground truth outside a simulator; what does a genuine duplicate look like as against
an authored one; where does grouping break first; and which of the six measures can actually be
computed from data anyone has. It does not succeed by scoring well.

**Two guardrails, because a probe that works becomes a product nobody will discard.** Decide the
discard criteria before building rather than after, and keep it cheap enough that discarding it is
not a loss worth arguing about. The failure mode here is organisational, not technical.

## Explicit non-goals

- Executing or recommending allocations in the first build
- Extraction quality on headcount, severity, and timing — deferred, independently assessable
- Classifying benign causes and hoaxes as such
- Adjudicating contradictions between reports about one event
- Learning from operator corrections
- Competing on the simulator's casualty score. A permissive agent will beat this one on that number;
  that is expected, not a defect.

## Known limits of the design as specified

- **Mis-addressed reports defeat the corroboration rule.** A call with the wrong address is
  textually indistinguishable from a correct one, and corroborating callers describe what they see
  while only the address is wrong. No accumulation of human evidence fixes it; only a responder's
  own observation does.
- **Correlated callers are not independent evidence.** Several people watching one benign event
  accumulate weight and auto-promote. Volume of agreement and independence of agreement are
  different quantities, and surge tempo produces the first while resembling the second.
- **The unknown-stakes rule cannot be validated in simulation.** In this environment a missing
  headcount correlates with the report not being real, so "unknown → escalate" would escalate
  disproportionately on noise. Treat that as an artifact of how the simulator authors calls, and do
  not assume in-sim results transfer.
- **Two measures need infrastructure decisions.** Fragmentation requires ground truth on how many
  events there really were — easy in simulation, hard in the field. Promotion latency only exists if
  held reports that never got promoted are retained.
- **Trust is earned by track record, not by visible reasoning.** With the derivation off the working
  screen and a weighting that expresses degrees of evidence rather than a flat rule, the operator
  cannot audit an entry in the moment — only afterwards. That is a deliberate trade of live
  legibility for a clean board, and it means the first wrong entry is paid for in full.

## Evidence posture

**The simulator is a construction tool, not a measuring instrument.** It exercises the system end to
end and catches what is broken. No number it produces is evidence about the field.

The operational rule that follows, and it is easy to violate by accident: **building against sim
data is fine; fitting to it is not.** Anything distributional — the promotion bar, the weighting,
the stakes rule — must not be tuned on authored noise, because tuning is measuring. Two known
divergences make this concrete: in-sim, a missing headcount correlates with a report not being real,
which would invert the unknown-stakes rule; and fragmentation is measurable there only because the
simulator knows how many events truly existed.

Consequence to hold consciously: the success measures above are **specified but uninstantiated.**
They are correctly defined and carry no evidence until real call data exists. Obtaining it is a
prerequisite to trusting the system, not a later refinement.

## Decisions considered and set aside

| Considered | Resolution |
| --- | --- |
| Surfacing ambiguity rather than resolving it (a board with its seams showing) | Rejected — the agent commits. |
| Dropping unevidenced reports outright instead of holding them | Rejected — holding is the substrate accumulated weight runs on; without it, corroboration collapses to judging each call alone. |
| Replacing accumulated weight with a flat bar (two independent reports, or one trusted channel) | Rejected — degrees of evidence retained, at the cost of in-the-moment accountability. |
| Per-entry reasoning on the live board | **Cut** — retained for review, removed from the working screen. |
| Full approval gate on every allocation | Rejected — routine allocations execute on the agent's authority; approval is reserved for consequential ones. |
| Building any of the allocation layer first | Rejected — first build is the board alone. |
| Letting the operator restructure the board (split or merge entries) | Rejected — one author, so the board always means one thing and the fragmentation measure is not repaired by the person it measures. |
| Feeding operator corrections back into future grouping | Rejected — remains a non-goal; no correction channel exists to learn from. |
| Treating the simulator as the proving ground | Rejected — it builds the system; it does not measure it. |
