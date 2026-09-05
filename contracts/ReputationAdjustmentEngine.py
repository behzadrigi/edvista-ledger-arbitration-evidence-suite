# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

import json

from genlayer import *
from dataclasses import dataclass


@allow_storage
@dataclass
class AdjustmentRecord:
    agent: Address
    delta: u256
    verdict: str
    source: str
    resulting_score: u256
    rolled_back: bool


class ReputationAdjustmentEngine(gl.Contract):
    adjustments: TreeMap[u256, AdjustmentRecord]
    next_id: u256

    def __init__(self):
        self.next_id = u256(0)

    # ================= RECORD ADJUSTMENT (AUDIT LOG) =================

    @gl.public.write
    def record_adjustment(
        self,
        agent: str,
        delta: u256,
        verdict: str,
        source: str,
        resulting_score: u256,
    ) -> u256:
        agent_address = Address(agent)
        verdict_upper = verdict.upper()

        assert verdict_upper in ("INCREASE", "DECREASE", "NEUTRAL"), \
            "verdict must be INCREASE, DECREASE, or NEUTRAL"
        if verdict_upper == "NEUTRAL":
            assert int(delta) == 0, "NEUTRAL verdict must carry delta 0"
        else:
            assert int(delta) > 0, "INCREASE or DECREASE must carry a positive delta"
        assert source.strip() != "", "source cannot be empty"

        adjustment_id = self.next_id
        self.next_id += u256(1)

        self.adjustments[adjustment_id] = AdjustmentRecord(
            agent=agent_address,
            delta=delta,
            verdict=verdict_upper,
            source=source,
            resulting_score=resulting_score,
            rolled_back=False,
        )

        return adjustment_id

    # ================= CONSENSUS-JUDGED ROLLBACK (QUORUM) =================

    @gl.public.write
    def request_rollback(self, adjustment_id: u256, reason: str):
        # Instead of a custom hardcoded multi-signature scheme, rollback
        # approval uses GenLayer's own validator consensus as the quorum:
        # every validator independently judges whether the stated reason
        # justifies reversing a previously recorded adjustment.
        assert adjustment_id in self.adjustments, "Adjustment not found"
        record = self.adjustments[adjustment_id]

        assert not record.rolled_back, "Adjustment already rolled back"
        assert reason.strip() != "", "reason cannot be empty"

        verdict = record.verdict
        delta = int(record.delta)
        source = record.source

        def leader_fn():
            prompt = f"""
            You are reviewing a request to roll back a previously recorded
            reputation adjustment.

            Original adjustment: {verdict} by {delta}
            Original source: {source}
            Rollback reason given:
            {reason}

            Approve the rollback only if the reason describes a specific,
            concrete error or injustice in the original adjustment (for
            example: wrong agent, factually incorrect basis, duplicate
            entry). Reject vague disagreement or a reason that does not
            point to an actual error.

            Respond with ONLY a JSON object in exactly this format,
            and nothing else:
            {{"decision": "APPROVED" or "REJECTED"}}
            """
            response = gl.nondet.exec_prompt(prompt)
            try:
                data = json.loads(response)
            except Exception:
                raise gl.vm.UserError("[LLM_ERROR] validator returned invalid JSON")

            decision = str(data.get("decision", "")).upper()
            if decision not in ("APPROVED", "REJECTED"):
                raise gl.vm.UserError("[LLM_ERROR] validator returned an invalid decision")

            return {"decision": decision}

        def validator_fn(leader_result) -> bool:
            if not isinstance(leader_result, gl.vm.Return):
                return False

            leader_data = leader_result.calldata
            if leader_data.get("decision") not in ("APPROVED", "REJECTED"):
                return False

            validator_data = leader_fn()

            return leader_data["decision"] == validator_data["decision"]

        result = gl.vm.run_nondet_unsafe(leader_fn, validator_fn)

        if result["decision"] == "APPROVED":
            record.rolled_back = True
            self.adjustments[adjustment_id] = record

    # ================= PUBLIC VIEW METHODS =================

    @gl.public.view
    def get_adjustment(self, adjustment_id: u256) -> str:
        if adjustment_id not in self.adjustments:
            return "NOT_FOUND"
        record = self.adjustments[adjustment_id]
        return (
            record.verdict + ":" + str(int(record.delta)) + ":"
            + str(int(record.resulting_score)) + ":"
            + ("ROLLED_BACK" if record.rolled_back else "ACTIVE")
        )

    @gl.public.view
    def get_adjustment_count(self) -> u256:
        return self.next_id

    @gl.public.view
    def is_rolled_back(self, adjustment_id: u256) -> bool:
        if adjustment_id not in self.adjustments:
            return False
        return self.adjustments[adjustment_id].rolled_back
