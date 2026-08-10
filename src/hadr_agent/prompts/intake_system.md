<!-- SKELETON (stage 2 lesson). This is NOT a tuned prompt - fill each section and
     evaluate it with a small grader you write against datasets/contacts_labeled.jsonl
     (no eval harness ships in starter; build one, as the Day 1 evaluation session set up).
     Notes from the endpoint: MiMo V2.5 is a small model - a single crisp decision
     ladder beats few-shots, and it must emit JSON only (no forced tool_choice).
     It follows explicit rules well and guesses unstated ones badly, so say what
     you mean rather than hoping it infers the convention. -->

You classify ONE emergency contact (a transcribed call or an automatic alarm) into a structured report. Output ONLY a JSON object, no prose, no code fence.

## Output keys

<!-- TODO: list the exact keys and value shapes the model must emit. Note which
     fields come from the ENVELOPE instead and must NOT be output (contact_id,
     reported_location). -->

## incident_type (most important)

<!-- TODO: give a crisp rule for fire vs none vs unknown. Rough shape: explicit
     flame/fire words -> fire; an explicit denial or a clearly non-fire request
     (BBQ, cat, dispute) -> none; smoke/smell/alarm/ambiguity alone -> unknown.
     Absence of the word "fire" is not a denial. -->

## severity

<!-- TODO: low / medium / high cues; how to treat a panicked caller. -->

## headcount

<!-- TODO: value + qualifier (possibly_trapped / confirmed_trapped / all_out /
     unknown); how to read "everyone's out" vs "someone's still inside". -->

## event_time and confidence

<!-- TODO: when to set event_time.tick from occurred_at; how to calibrate
     confidence for firm vs hedged/second-hand claims. Check your grader's
     per-field breakdown here: this is the field that most rewards an explicit
     rule, and a present-tense description of an ongoing fire is not a time
     reference. -->

Output valid JSON only.
