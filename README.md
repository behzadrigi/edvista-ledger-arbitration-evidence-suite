# EdVista: GenLayer Reputation & Arbitration Suite

A collection of four standalone GenLayer Intelligent Contracts that
together form a reputation, evidence-review, dispute, and governance
stack: an agent's reputation can be adjusted through self-reported
claims, formally disputed by a third party, backed by independently
reviewed evidence, and audited with a reversible governance log.

## Why this exists

A single reputation number is only trustworthy if there is a fair way
to change it. This suite splits that problem into four independent,
reusable pieces, each validated by GenLayer's decentralized consensus
in a genuinely different way.

## Contracts

| Contract | Purpose | Consensus pattern |
|---|---|---|
| [ReputationLedger](contracts/ReputationLedger.py) | Self-service reputation adjustments: any address proposes an INCREASE/DECREASE/RESET with a written reason; validators judge whether the reason is legitimate | Custom leader/validator, partial field matching on the decision |
| [ReputationArbitration](contracts/ReputationArbitration.py) | Formal third-party complaints against an agent; validators judge severity and assign a verdict and delta from a fixed set | Custom leader/validator, partial field matching on verdict and delta together |
| [EvidenceCorroboration](contracts/EvidenceCorroboration.py) | Submits and reviews evidence with two distinct evaluation modes | Strict equality on verdict (evaluate_evidence_strict) vs. tolerance-based agreement on a numeric confidence score (evaluate_evidence_soft) |
| [ReputationAdjustmentEngine](contracts/ReputationAdjustmentEngine.py) | Independent audit log of adjustments with consensus-judged rollback | Custom leader/validator, replacing a hardcoded multi-sig with GenLayer's own validator quorum |

See [CONTRACTS.md](CONTRACTS.md) for a detailed explanation of each
contract, and [DECISIONS.md](DECISIONS.md) for the design rationale
and tradeoffs behind the suite.

## Deployed and tested on GenLayer Studio

- ReputationLedger deploy: `0xbd7e761f10ac9872beaa71d3466b732c0e211773df1ce6e926bd5ccfe559aab7`
- ReputationLedger register_agent: `0xc19f94300f68fa6ef7fb72991cf2b14d76995134b10e25e2826c631494fe69b1`
- ReputationLedger propose_adjustment INCREASE (approved): `0x65f05120f20372afe40ac2cc7a4d52560c616b56d50eb1eefccf733947bfdc33`
- ReputationLedger propose_adjustment INCREASE (rejected): `0xf7d0b2810c9dbacdc0be81c53eeb3bf4726a93e328dd8941c2b4eae10e016244`
- ReputationLedger propose_adjustment DECREASE (approved): `0x856a860eb32b8a2a0cf57d2c2f284059ad47c8a82293d6d13cda1175337c07cb`
- ReputationLedger propose_adjustment RESET (rejected): `0xe2ed154d5a9fde2359689b57770a3f963b70381b6a8b0e06833c900a3205f24c`
- ReputationArbitration open_case (serious complaint): `0xd2b2aa45353e1e5a88dab8b1292973bffe432eafbe3092e77a61f7cbcc5d3a61`
- ReputationArbitration open_case (self-complaint, blocked): `0xf17e0ea0fae174e1a2f94ef2e8732c2d4f403a0904b717d5821e41d73cfb1662`
- ReputationArbitration evaluate_case (serious → DECREASE:30): `0x32747e957462b3bd9e6e37fd44ed73a462e98d576f8176c9a928733466e65339`
- ReputationArbitration evaluate_case (double-eval blocked): `0x61cf2ff771bc53dbc8db3a42c4047634a3c94be4580b26584663e49b691ba9b6`
- ReputationArbitration open_case (weak complaint): `0x63b0ef6f39252d79b4fa51e3bb8dbd590c18324e510870ddee8ef66b7f00dde7`
- ReputationArbitration evaluate_case (weak → DECREASE:10): `0xd22b90eab9ad774248dce2ddf686cc1283b5537fa39f2b80350ec9bc8935bfc8`
- EvidenceCorroboration deploy: `0xc3357ce526592535033cd61227d9642c919e8ea3b4b224a5e39e372e84853d2e`
- EvidenceCorroboration submit_evidence: `0x13683882aac07352e0afb0671e761db030e742cf8869484e44205356d13cd0b6`
- EvidenceCorroboration evaluate_evidence_soft: `0xc49a3047093b3b84dc4eaa14742bed6643e55d4eaff873c8b2e0331a6aed1b62`
- EvidenceCorroboration evaluate_evidence_strict (blocked): `0x1675e217200b50f67bc8c26eca9acdf18fffa2aa169d8cc00c5826f89dc8533f`
- EvidenceCorroboration update_evidence (unauthorized): `0xde720a17d3ce80e8bdd7a7bcaffbd7a1465e1f970207b5a359e209002713954d`
- EvidenceCorroboration update_evidence (authorized): `0x839a890f4a02b9c0745a12350581ad104cb9fe783874da52ab9a84733488bead`
- EvidenceCorroboration delete_evidence (unauthorized): `0xe41e1209552fcef0b29a933e99bf6d359722524b33d4d6d0bf281ad04db95091`
- EvidenceCorroboration delete_evidence (authorized): `0x00394a4d886a7b18bbeff2692d8f998ecc9f8ac854b0cfe80d57f737dfbff537`
- EvidenceCorroboration submit_evidence (2nd record): `0x9960e9d7f155cada2c8279e6dcc63f954b2db1ea2662e8be86766a223ca8cd12`
- EvidenceCorroboration update_evidence 2nd (unauthorized): `0xc0c3cd7138a54a39175befe7e2defaa10fe172d77d76b15679dd2219b0ab1197`
- EvidenceCorroboration update_evidence 2nd (authorized): `0x4ba1c25477b24dad040ccf7d7493e8dcce16c473d568d30971b061220bd4f68f`
- ReputationAdjustmentEngine deploy: `0x1ac7dccc3d54004688c6e53732b56d37b87693f64216693fd886a890c005af50`
- ReputationAdjustmentEngine record_adjustment (DECREASE): `0x7be52653eb288e40f67822310022d021ed4bb0b9287b926594b375c97ffbb2c6`
- ReputationAdjustmentEngine record_adjustment (NEUTRAL): `0x91923c9ab04518ba47cfc4c727e2ad69a6d7343a857f1ced16f979120a92a3e4`
- ReputationAdjustmentEngine record_adjustment (invalid NEUTRAL, blocked): `0x8ee4e55458e01a449cdc46f50d3cf0fb7ebda03e88cf40860caedf30c0f4957f`
- ReputationAdjustmentEngine request_rollback (approved): `0xc0b8879269e68ccf4169c82f6cbe5b080348799b5df24c66c7c754b99ddaf353`
- ReputationAdjustmentEngine request_rollback (double, blocked): `0x23b529ba61fa4f2014ba2cc7047d68e66eb65a877dd52bc7cc8b4736e89cd646`
- ReputationAdjustmentEngine request_rollback (rejected): `0x67fc7255f4882260fdedb815d14daeb9cac3367b32f7cd56a439f70e202540bd`

## License

MIT
