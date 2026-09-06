# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

import json

from genlayer import *
from dataclasses import dataclass


@allow_storage
@dataclass
class ArbitrationCase:
    complainant: Address
    agent: Address
    reason: str
    evidence_url: str
    status: str
    delta: u256
    verdict: str


class ReputationArbitration(gl.Contract):
    cases: TreeMap[u256, ArbitrationCase]
    next_id: u256

    def __init__(self):
        self.next_id = u256(0)

    # ================= OPEN CASE =================

    @gl.public.write
    def open_case(self, agent: str, reason: str, evidence_url: str) -> u256:
        assert reason.strip() != "", "Reason cannot be empty"
        assert evidence_url.strip() != "", "evidence_url cannot be empty"

        agent_address = Address(agent)
        assert gl.message.sender_address != agent_address, \
            "An agent cannot open a case against themselves; use ReputationLedger.propose_adjustment for self-reported changes"

        case_id = self.next_id
        self.next_id += u256(1)

        self.cases[case_id] = ArbitrationCase(
            complainant=gl.message.sender_address,
            agent=agent_address,
            reason=reason,
            evidence_url=evidence_url,
            status="OPEN",
            delta=u256(0),
            verdict="",
        )

        return case_id

    # ================= NONDET ARBITRATION (NOW EVIDENCE-BACKED) =================

    @gl.public.write
    def evaluate_case(self, case_id: u256):
        assert case_id in self.cases, "Case not found"

        case = self.cases[case_id]
        assert case.status == "OPEN", "Case already resolved"

        reason = case.reason
        evidence_url = case.evidence_url

        def leader_fn():
            page_content = gl.nondet.web.render(evidence_url, mode='html')

            prompt = f"""
            You are an impartial reputation arbitration judge reviewing a
            formal complaint filed by one party against another.

            Complaint reason:
            {reason}

            Content fetched from the evidence URL the complainant cited:
            {page_content}

            First, decide whether the fetched page content actually
            supports the complaint reason with specific, verifiable
            detail. If it does not, the complaint is unsubstantiated.

            Respond ONLY with JSON:
            {{"verdict": "INCREASE" or "DECREASE", "delta": <integer>}}

            Rules:
            - DECREASE: the fetched page content substantiates a real,
              specific, verifiable failure or violation by the agent.
            - INCREASE: the fetched page content does NOT substantiate
              the complaint, or actually reflects well on the agent
              instead (an unsubstantiated or misdirected complaint).
            - delta must be exactly one of: 10, 20, or 30, based on how
              severe the substantiated behavior is (10 for weak or
              unsubstantiated, 30 for severe and well-substantiated).
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
            if leader_data.get("verdict") not in ("INCREASE", "DECREASE"):
                return False
            if leader_data.get("delta") not in (10, 20, 30):
                return False

            validator_data = leader_fn()

            return (
                leader_data.get("verdict") == validator_data.get("verdict")
                and leader_data.get("delta") == validator_data.get("delta")
            )

        result = gl.vm.run_nondet_unsafe(leader_fn, validator_fn)

        verdict = result["verdict"]
        delta = u256(result["delta"])

        case.verdict = verdict
        case.delta = delta
        case.status = "RESOLVED"
        self.cases[case_id] = case

    # ================= PUBLIC VIEW METHODS =================

    @gl.public.view
    def get_case(self, case_id: u256) -> str:
        if case_id not in self.cases:
            return "NOT_FOUND"
        case = self.cases[case_id]
        return case.status + ":" + case.verdict + ":" + str(int(case.delta))

    @gl.public.view
    def get_case_agent(self, case_id: u256) -> str:
        if case_id not in self.cases:
            return "NOT_FOUND"
        return str(self.cases[case_id].agent)
