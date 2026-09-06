# EdVista: GenLayer Reputation & Arbitration Suite

A collection of four standalone GenLayer Intelligent Contracts that
together form a reputation, evidence-review, dispute, and governance
stack.

## Contracts

| Contract | Purpose | Consensus pattern |
|---|---|---|
| [ReputationLedger](contracts/ReputationLedger.py) | Self-service reputation adjustments backed by a fetched evidence URL; validators judge whether the fetched page actually corroborates the stated reason | Custom leader/validator, evidence-grounded partial field matching |
| [ReputationArbitration](contracts/ReputationArbitration.py) | Formal third-party complaints against an agent, also backed by a fetched evidence URL; validators agree on both verdict and delta | Custom leader/validator, evidence-grounded, partial field matching on verdict and delta together |
| [EvidenceCorroboration](contracts/EvidenceCorroboration.py) | Submits and reviews evidence with two distinct evaluation modes | Strict equality on verdict vs. tolerance-based agreement on a numeric confidence score |
| [ReputationAdjustmentEngine](contracts/ReputationAdjustmentEngine.py) | Independent audit log of adjustments with consensus-judged rollback | Custom leader/validator judging an on-chain recorded fact, replacing a hardcoded multi-sig with GenLayer's own validator quorum |

See [CONTRACTS.md](CONTRACTS.md) for details and
[DECISIONS.md](DECISIONS.md) for design rationale.

## Deployed and tested on GenLayer Studio

### ReputationLedger (evidence-backed)
- deploy: `0xec7ce093c29be763af617d6138f9d775473ca6f6928881e77b6ed0937f04e690`
- register_agent: `0xe513c6e9222ed950f5e00c88d3f8399843462910cd8a5a2b0d01c4512a54f0a4`
- propose_adjustment INCREASE (rejected, weak evidence): `0xfa0dbc7b02f7936a4f4525884fac019a4391d99c9ed2623f42acfd1379c71385`
- propose_adjustment INCREASE (rejected, unrelated evidence): `0x2e0dda0744655dcb0e654828e7c382c23c4f1250968492cf492474933a992378`
- propose_adjustment (empty evidence_url, blocked): `0xca802507c0a9dc7612aa3e56844371eb616d6ee85482cb5b9bf2ed02dfa2ec7b`
- propose_adjustment (unregistered agent, blocked): `0x43fcf29b954592a2ad0be990eae748e25d2331f05e4afbb84ac50dc7fc20235a`
- propose_adjustment INCREASE (approved): `0x5956bf9df67e8b1d0c90232ec7b35bb618e5979d97ef57a68f1d2bf6761b361c`
- propose_adjustment DECREASE (approved): `0x3795a64d1cb0fe70e3a4729079c8fac33c8e77f66fd9a552ed0f500451585bb5`

### ReputationArbitration (evidence-backed)
- deploy: `0xa69b8f638495dbb1a3b0b14afeda333c2df6d5542ef4acf698c9561d4897b567`
- open_case #0: `0x9bdf23f6834b91c6bf49ed59f1ac705e9b519e0f4daeff3a4a9eee0df32c4988`
- open_case (self-complaint, blocked): `0xd60a0835344520a3cc15cfc0eafbde17e1e0afae5266068ee1cd22c79b13824e`
- evaluate_case #0: `0xb88f0167620a31dac5860f87dfec6138d083d83b0ad4e0ef657cb3c227334cd0`
- evaluate_case #0 again (blocked): `0x37d42e3c11a25e81777f49d00a469c0cbd110a7e35a5b54bd3a4b2dbf3cc87f5`
- open_case #1 (unrelated evidence): `0x25d002f7b0b1a3562f262428559b8ae3447dcc4949fa803c794e4aa9ddc40dbd`
- evaluate_case #1: `0xefe3b005b3a9fcf582f5e28d2bb2f8e1c705cd3d75483a51a7adff4c9ec079ea`
- evaluate_case #1 again (blocked): `0x282a38c75f93c25e458bf94fc597942acc5e48c3d0c35370444cbda8f59ccd48`

### EvidenceCorroboration
- deploy: `0xc3357ce526592535033cd61227d9642c919e8ea3b4b224a5e39e372e84853d2e`
- submit_evidence: `0x13683882aac07352e0afb0671e761db030e742cf8869484e44205356d13cd0b6`
- evaluate_evidence_soft: `0xc49a3047093b3b84dc4eaa14742bed6643e55d4eaff873c8b2e0331a6aed1b62`
- evaluate_evidence_strict (blocked): `0x1675e217200b50f67bc8c26eca9acdf18fffa2aa169d8cc00c5826f89dc8533f`
- update_evidence (unauthorized): `0xde720a17d3ce80e8bdd7a7bcaffbd7a1465e1f970207b5a359e209002713954d`
- update_evidence (authorized): `0x839a890f4a02b9c0745a12350581ad104cb9fe783874da52ab9a84733488bead`
- delete_evidence (unauthorized): `0xe41e1209552fcef0b29a933e99bf6d359722524b33d4d6d0bf281ad04db95091`
- delete_evidence (authorized): `0x00394a4d886a7b18bbeff2692d8f998ecc9f8ac854b0cfe80d57f737dfbff537`
- submit_evidence (2nd): `0x9960e9d7f155cada2c8279e6dcc63f954b2db1ea2662e8be86766a223ca8cd12`
- update_evidence 2nd (unauthorized): `0xc0c3cd7138a54a39175befe7e2defaa10fe172d77d76b15679dd2219b0ab1197`
- update_evidence 2nd (authorized): `0x4ba1c25477b24dad040ccf7d7493e8dcce16c473d568d30971b061220bd4f68f`

### ReputationAdjustmentEngine
- deploy: `0x1ac7dccc3d54004688c6e53732b56d37b87693f64216693fd886a890c005af50`
- record_adjustment (DECREASE): `0x7be52653eb288e40f67822310022d021ed4bb0b9287b926594b375c97ffbb2c6`
- record_adjustment (NEUTRAL): `0x91923c9ab04518ba47cfc4c727e2ad69a6d7343a857f1ced16f979120a92a3e4`
- record_adjustment (invalid NEUTRAL, blocked): `0x8ee4e55458e01a449cdc46f50d3cf0fb7ebda03e88cf40860caedf30c0f4957f`
- request_rollback (approved): `0xc0b8879269e68ccf4169c82f6cbe5b080348799b5df24c66c7c754b99ddaf353`
- request_rollback (double, blocked): `0x23b529ba61fa4f2014ba2cc7047d68e66eb65a877dd52bc7cc8b4736e89cd646`
- request_rollback (rejected): `0x67fc7255f4882260fdedb815d14daeb9cac3367b32f7cd56a439f70e202540bd`

## License

MIT
