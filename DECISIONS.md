# Design Decisions

## Why four separate contracts, each with a different role

ReputationLedger (self-service), ReputationArbitration (third-party
complaint), EvidenceCorroboration (evidence review), and
ReputationAdjustmentEngine (audit/governance) each solve a distinct
part of "how should reputation change and who can trust that change."

## Why ReputationArbitration requires the complainant to differ from the agent

Without this rule, ReputationArbitration would be functionally
identical to ReputationLedger's propose_adjustment, just phrased
differently. Requiring a third party keeps the two contracts
genuinely distinct: one is self-attested, the other is adversarial.

## Why EvidenceCorroboration has two evaluation modes with different agreement rules

`evaluate_evidence_strict` and `evaluate_evidence_soft` are not just
two different prompts; they encode two different Equivalence
Principle agreement rules. Strict requires exact verdict match only.
Soft requires the verdict to match AND the numeric confidence to fall
within a tolerance band, since independent LLM runs (especially
across different model providers on GenLayer's validator panel)
rarely produce identical confidence integers even when they agree in
substance.

## Why the contracts are not wired together on-chain

None of the four contracts call each other directly. This suite
documents the intended relationship (Arbitration and Evidence verdicts
would inform an adjustment recorded and audited by
ReputationAdjustmentEngine, which would in turn update
ReputationLedger) rather than implementing live cross-contract calls,
to keep scope realistic while ensuring each contract is genuinely
correct and independently tested.

## Why ReputationAdjustmentEngine uses validator consensus instead of a hardcoded multi-signature scheme for rollback

A custom multi-sig implementation is itself a source of bugs and is
not native to GenLayer. Using `gl.vm.run_nondet_unsafe` for rollback
approval means the "quorum" is GenLayer's own decentralized validator
set judging the merits of the rollback reason, rather than a fixed
set of hardcoded signer addresses.

## Why EvidenceCorroboration enforces submitter-only access control

An earlier draft allowed any address to update, delete, or reset any
evidence record. This was corrected so only the original submitter of
an evidence record can modify or remove it, preventing a bad actor
from tampering with or destroying evidence submitted by someone else
before it can be evaluated.

## Why ReputationLedger and ReputationArbitration now require a fetched evidence URL

An earlier version of this suite let any LLM judge a purely
caller-written reason with no independent verification. A steward
review of a related suite (Deliverable Arbitration Suite) correctly
flagged this exact pattern: payment and dispute decisions relying on
caller-written evidence, with nothing retrieved or verified by the
contract itself. Both `ReputationLedger.propose_adjustment` and
`ReputationArbitration.evaluate_case` were rebuilt, before submission,
to fetch a cited evidence_url via `gl.nondet.web.render` and require
the LLM to judge whether the actual fetched content corroborates the
claim, mirroring the pattern already used successfully in
EvidenceCorroboration. `ReputationAdjustmentEngine.request_rollback`
was left as-is, since it judges an already-recorded on-chain fact
rather than an external claim, which does not carry the same risk.
