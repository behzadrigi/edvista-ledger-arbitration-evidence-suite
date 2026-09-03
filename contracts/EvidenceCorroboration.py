# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

from genlayer import *
from dataclasses import dataclass
import json


@allow_storage
@dataclass
class EvidenceRecord:
    evidence_id: u256
    agent: Address
    content: str
    verdict: str
    confidence: u256
    status: str


class EvidenceCorroboration(gl.Contract):
    evidences: TreeMap[u256, EvidenceRecord]
    next_id: u256

    def __init__(self):
        self.next_id = u256(0)

    # ================= CREATE EVIDENCE =================

    @gl.public.write
    def submit_evidence(self, agent: str, content: str) -> u256:
        assert content.strip() != "", "Content cannot be empty"

        eid = self.next_id
        self.next_id += u256(1)

        self.evidences[eid] = EvidenceRecord(
            evidence_id=eid,
            agent=Address(agent),
            content=content,
            verdict="",
            confidence=u256(0),
            status="PENDING"
        )

        return eid

    # ================= NONDET CORROBORATION =================

    @gl.public.write
    def evaluate_evidence(self, evidence_id: u256):
        assert evidence_id in self.evidences, "Evidence not found"

        ev = self.evidences[evidence_id]
        assert ev.status == "PENDING", "Already evaluated"

        content = ev.content

        def leader_fn():
            prompt = f"""
            You are an impartial evidence analyst.

            Evidence content:
            {content}

            Respond ONLY with JSON:
            {{
                "verdict": "VALID" or "INVALID",
                "confidence": <integer: 60, 70, 80, 90>
            }}

            Rules:
            - VALID: evidence supports the claim.
            - INVALID: evidence does not support the claim.
            - confidence must be one of: 60, 70, 80, 90.
            """

            response = gl.nondet.exec_prompt(prompt)
            try:
                data = json.loads(response)
            except Exception:
                raise gl.vm.UserError("[LLM_ERROR] invalid JSON")

            verdict = str(data.get("verdict", "")).upper()
            confidence = int(data.get("confidence", 0))

            assert verdict in ("VALID", "INVALID"), "[LLM_ERROR] invalid verdict"
            assert confidence in (60, 70, 80, 90), "[LLM_ERROR] invalid confidence"

            return {"verdict": verdict, "confidence": confidence}

        def validator_fn(leader_result) -> bool:
            if not isinstance(leader_result, gl.vm.Return):
                return False

            leader_data = leader_result.calldata
            verdict = leader_data.get("verdict")
            confidence = leader_data.get("confidence")

            validator_data = leader_fn()

            return (
                verdict == validator_data.get("verdict")
                and confidence == validator_data.get("confidence")
            )

        result = gl.vm.run_nondet_unsafe(leader_fn, validator_fn)

        verdict = result["verdict"]
        confidence = u256(result["confidence"])

        ev.verdict = verdict
        ev.confidence = confidence
        ev.status = "RESOLVED"
        self.evidences[evidence_id] = ev

        return {"verdict": verdict, "confidence": int(confidence)}

    # ================= VIEW =================

    @gl.public.view
    def get_evidence(self, evidence_id: u256) -> str:
        if evidence_id not in self.evidences:
            return "NOT_FOUND"
        ev = self.evidences[evidence_id]
        return f"{ev.status}:{ev.verdict}:{int(ev.confidence)}"

    # ================= REQUIRED NONDET PLACEHOLDER =================

    def nondet(self):
        return {"nondet": "noop"}
