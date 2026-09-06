# Contracts

## ReputationLedger

**Purpose**: Self-service reputation store keyed by agent address.
Any address can propose a score change for a registered agent,
backed by a cited evidence URL.

**How consensus is used**: `propose_adjustment` fetches `evidence_url`
via `gl.nondet.web.render` inside `leader_fn`, and an LLM approves the
change only if the fetched page content actually corroborates the
stated reason. Only the objective decision field is compared across
validators.

**Safety properties**: an agent can only be registered once; an
evidence_url must be non-empty; a REJECTED verdict leaves the score
untouched and only logs the rejection.

## ReputationArbitration

**Purpose**: A formal, third-party complaint system, distinct from
ReputationLedger's self-service model. Requires the complainant to be
a different address than the target agent, and requires a cited
evidence URL.

**How consensus is used**: `evaluate_case` fetches `evidence_url` and
has an LLM judge whether the fetched content substantiates the
complaint, assigning a verdict (INCREASE/DECREASE) and a delta
restricted to a fixed set (10, 20, 30). `validator_fn` requires both
fields to match exactly across independent runs.

**Safety properties**: an agent cannot open a case against
themselves; a case can only be evaluated once.

## EvidenceCorroboration

**Purpose**: Submits evidence about an agent and reviews it two
different ways.

**How consensus is used**: `evaluate_evidence_strict` requires the
verdict field to match exactly across validators.
`evaluate_evidence_soft` requires the verdict to match AND the
confidence score to be within a 30-point tolerance — a genuinely
different agreement rule.

**Safety properties**: only the original submitter can update,
delete, or reset their own evidence.

## ReputationAdjustmentEngine

**Purpose**: An independent audit and governance log for adjustments
recorded from the other contracts.

**How consensus is used**: `record_adjustment` is fully deterministic.
`request_rollback` uses a leader/validator function where an LLM
judges whether a stated reason describes an actual error in a
previously recorded on-chain adjustment. Unlike ReputationLedger and
ReputationArbitration, the material being judged here is the
contract's own prior on-chain record, not an external real-world
claim, which is why this contract does not require an additional
fetched evidence URL.

**Safety properties**: NEUTRAL adjustments must carry delta 0; an
adjustment can only be rolled back once.
