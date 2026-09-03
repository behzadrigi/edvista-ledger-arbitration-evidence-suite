# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

from genlayer import *
from dataclasses import dataclass
import json


@allow_storage
@dataclass
class ArbitrationCase:
    record_id: u256
    agent: Address
    reason: str
    status: str
    delta: u256
    verdict: str


class ReputationArbitration(gl.Contract):
    cases: TreeMap[u256, ArbitrationCase]
    next_id: u256

    def __init__(self):
        self.next_id = u256(0)

    # ================= CREATE CASE =================

    @gl.public.write
    def open_case(self, record_id: u256, agent: str, reason: str) -> u256:
        assert reason.strip() != "", "Reason cannot be empty"

        case_id = self.next_id
        self.next_id += u256(1)

        self.cases[case_id] = ArbitrationCase(
            record_id=record_id,
            agent=Address(agent),
            reason=reason,
            status="OPEN",
            delta=u256(0),
            verdict=""
        )

        return case_id

    # ================= NONDET ARBITRATION =================

    @gl.public.write
    def evaluate_case(self, case_id: u256):
        assert case_id in self.cases, "Case not found"

        case = self.cases[case_id]
        assert case.status == "OPEN", "Case already resolved"

        reason = case.reason

        def leader_fn():
            prompt = f"""
            You are an impartial reputation judge.

            Case reason:
            {reason}

            Respond ONLY with JSON:
            {{"verdict": "INCREASE" or "DECREASE", "delta": <integer>}}

            Rules:
            - INCREASE: agent deserves higher reputation.
            - DECREASE: agent deserves lower reputation.
            - delta must be one of: 10, 20, 30.
            """

            response = gl.nondet.exec_prompt(prompt)
            try:
                data = json.loads(response)
            except Exception:
                raise gl.vm.UserError("[LLM_ERROR] invalid JSON")

            verdict = str(data.get("verdict", "")).upper()
            delta = int(data.get("delta", 0))

            assert verdict in ("INCREASE", "DECREASE"), "[LLM_ERROR] invalid verdict"
            assert delta in (10, 20, 30), "[LLM_ERROR] invalid delta"

            return {"verdict": verdict, "delta": delta}

        def validator_fn(leader_result) -> bool:
            if not isinstance(leader_result, gl.vm.Return):
                return False

            leader_data = leader_result.calldata
            verdict = leader_data.get("verdict")
            delta = leader_data.get("delta")

            validator_data = leader_fn()

            return (
                verdict == validator_data.get("verdict")
                and delta == validator_data.get("delta")
            )

        result = gl.vm.run_nondet_unsafe(leader_fn, validator_fn)

        verdict = result["verdict"]
        delta = u256(result["delta"])

        case.verdict = verdict
        case.delta = delta
        case.status = "RESOLVED"
        self.cases[case_id] = case

        return {"verdict": verdict, "delta": int(delta)}

    # ================= VIEW METHODS =================

    @gl.public.view
    def get_case(self, case_id: u256) -> str:
        if case_id not in self.cases:
            return "NOT_FOUND"
        case = self.cases[case_id]
        return f"{case.status}:{case.verdict}:{int(case.delta)}"

    # ================= REQUIRED NONDET PLACEHOLDER =================

    def nondet(self):
        return {"nondet": "noop"}
