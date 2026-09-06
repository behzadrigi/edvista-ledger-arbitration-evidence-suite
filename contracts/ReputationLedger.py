# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

import json

from genlayer import *
from dataclasses import dataclass


@allow_storage
@dataclass
class ReputationRecord:
    registered: bool
    score: u256
    history: str


def _validate_direction(direction: str):
    assert direction in ("INCREASE", "DECREASE", "RESET"), \
        "direction must be INCREASE, DECREASE, or RESET"


class ReputationLedger(gl.Contract):
    records: TreeMap[Address, ReputationRecord]

    def __init__(self):
        pass

    # ================= REGISTRATION =================

    @gl.public.write
    def register_agent(self, agent: str):
        agent_address = Address(agent)

        assert agent_address not in self.records, "Agent already registered"

        self.records[agent_address] = ReputationRecord(
            registered=True,
            score=u256(0),
            history="[REGISTERED:0]",
        )

    # ================= CONSENSUS-JUDGED, EVIDENCE-BACKED ADJUSTMENT =================

    @gl.public.write
    def propose_adjustment(
        self, agent: str, direction: str, amount: u256, reason: str, evidence_url: str
    ):
        agent_address = Address(agent)
        assert agent_address in self.records, "Agent is not registered"

        direction_upper = direction.upper()
        _validate_direction(direction_upper)
        assert reason.strip() != "", "reason cannot be empty"
        assert evidence_url.strip() != "", "evidence_url cannot be empty"

        if direction_upper != "RESET":
            assert int(amount) > 0, "amount must be positive for INCREASE or DECREASE"

        record = self.records[agent_address]
        current_score = int(record.score)

        def leader_fn():
            page_content = gl.nondet.web.render(evidence_url, mode='html')

            prompt = f"""
            You are reviewing a proposed reputation score adjustment on a
            decentralized reputation ledger.

            Current score: {current_score}
            Proposed change: {direction_upper} by {int(amount)}
            Reason given for this change:
            {reason}

            Content fetched from the evidence URL the proposer cited:
            {page_content}

            Approve the change ONLY if the fetched page content actually
            supports the stated reason with specific, verifiable detail.
            Reject if the page does not corroborate the reason, is
            unrelated, or the reason is vague even where the page might be
            relevant.

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
        decision = result["decision"]

        if decision == "APPROVED":
            if direction_upper == "INCREASE":
                new_score = u256(current_score + int(amount))
            elif direction_upper == "DECREASE":
                new_score = u256(max(0, current_score - int(amount)))
            else:
                new_score = u256(0)

            record.score = new_score
            record.history += ";" + direction_upper + ":" + str(int(amount)) + ":APPROVED"
        else:
            record.history += ";" + direction_upper + ":" + str(int(amount)) + ":REJECTED"

        self.records[agent_address] = record

    # ================= PUBLIC VIEW METHODS =================

    @gl.public.view
    def get_score(self, agent: str) -> u256:
        agent_address = Address(agent)
        if agent_address not in self.records:
            return u256(0)
        return self.records[agent_address].score

    @gl.public.view
    def get_history(self, agent: str) -> str:
        agent_address = Address(agent)
        if agent_address not in self.records:
            return "NOT_FOUND"
        return self.records[agent_address].history

    @gl.public.view
    def is_registered(self, agent: str) -> bool:
        agent_address = Address(agent)
        return agent_address in self.records
