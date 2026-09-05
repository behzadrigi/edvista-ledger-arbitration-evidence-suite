# Contracts

## ReputationLedger

**Purpose**: Self-service reputation store keyed directly by agent
address. Any address can propose a score change for a registered
agent with a written reason.

**How consensus is used**: `propose_adjustment` runs a leader/validator
function where an LLM judges whether the written reason substantiates
the proposed INCREASE, DECREASE, or RESET. Only the objective decision
field is compared across validators.

**Safety properties**: an agent can only be registered once; only a
registered agent can have adjustments proposed against it; a REJECTED
verdict leaves the score untouched and only logs the rejection.

## ReputationArbitration

**Purpose**: A formal, third-party complaint system, distinct from
ReputationLedger's self-service model. `open_case` explicitly requires
the complainant to be a different address than the target agent.

**How consensus is used**: `evaluate_case` runs a leader/validator
function where an LLM assigns a verdict (INCREASE/DECREASE) and a
delta restricted to a fixed set (10, 20, 30) based on severity.
`validator_fn` requires both the verdict and the delta to match
exactly across independent runs.

**Safety properties**: an agent cannot open a case against themselves;
a case can only be evaluated once; case complainant, agent, reason,
and verdict are all readable after resolution.

## EvidenceCorroboration

**Purpose**: Submits evidence about an agent and reviews it two
different ways depending on how much tolerance is appropriate for
the evaluation.

**How consensus is used**: `evaluate_evidence_strict` requires the
verdict field (VALID/INVALID) to match exactly across validators
(confidence is checked for validity but not required to match).
`evaluate_evidence_soft` requires the verdict to match exactly AND
the confidence score to be within a fixed tolerance (30 points) of
the leader's confidence — a genuinely different agreement rule, not
just a different prompt.

**Safety properties**: only the original submitter can update,
delete, or reset their own evidence; evidence can only be evaluated
once (by either method) while still PENDING.

## ReputationAdjustmentEngine

**Purpose**: An independent audit and governance log. It does not
call the other three contracts on-chain (see DECISIONS.md); it
records adjustments as an auditable, reversible ledger.

**How consensus is used**: `record_adjustment` is fully deterministic
(no LLM). `request_rollback` uses a leader/validator function where
an LLM judges whether a stated reason describes an actual error in a
prior adjustment, replacing a hardcoded multi-signature scheme with
GenLayer's own validator quorum.

**Safety properties**: NEUTRAL adjustments must carry delta 0; an
adjustment can only be rolled back once; rollback requires validator
approval, not a single caller's assertion.
