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

    # ================= CREATE =================

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

    # ================= UPDATE =================

    @gl.public.write
    def update_evidence(self, evidence_id: u256, new_content: str):
        assert evidence_id in self.evidences, "Evidence not found"
        assert new_content.strip() != "", "Content cannot be empty"

        ev = self.evidences[evidence_id]
        assert ev.status == "PENDING", "Cannot update resolved evidence"

        ev.content = new_content
        self.evidences[evidence_id] = ev

        return True

    # ================= DELETE =================

    @gl.public.write
    def delete_evidence(self, evidence_id: u256):
        assert evidence_id in self.evidences, "Evidence not found"

        ev = self.evidences[evidence_id]
        assert ev.status == "PENDING", "Cannot delete resolved evidence"

        del self.evidences[evidence_id]
        return True

    # ================= RESET =================

    @gl.public.write
    def reset_evidence(self, evidence_id: u256):
        assert evidence_id in self.evidences, "Evidence not found"

        ev = self.evidences[evidence_id]
        ev.status = "PENDING"
        ev.verdict = ""
        ev.confidence = u256(0)
        self.evidences[evidence_id] = ev

        return True

    # ================= STRICT EVALUATION =================

    @gl.public.write
    def evaluate_evidence_strict(self, evidence_id: u256):
        assert evidence_id in self.evidences, "Evidence not found"

        ev = self.evidences[evidence_id]
        assert ev.status == "PENDING", "Already evaluated"

        content = ev.content

        def leader_fn():
            prompt = f"""
            You are performing a STRICT evidence validity check.

            Evidence:
            {content}

            Decide whether this evidence is VALID or INVALID, and how
            confident you are on a scale from 0 to 100.

            Respond with ONLY a JSON object, nothing else, no explanation,
            no markdown formatting. confidence must be a single whole
            number from 0 to 100.

            Example of a correctly formatted response:
            {{"verdict": "VALID", "confidence": 87}}

            Your response:
            """

            response = gl.nondet.exec_prompt(prompt)
            try:
                data = json.loads(response)
            except Exception:
                raise gl.vm.UserError("[LLM_ERROR] invalid JSON")

            verdict = str(data.get("verdict", "")).upper()
            try:
                confidence = int(data.get("confidence", -1))
            except (TypeError, ValueError):
                raise gl.vm.UserError("[LLM_ERROR] invalid confidence")

            assert verdict in ("VALID", "INVALID"), "[LLM_ERROR] invalid verdict"
            assert 0 <= confidence <= 100, "[LLM_ERROR] confidence out of range"

            return {"verdict": verdict, "confidence": confidence}

        def validator_fn(leader_result):
            # Strict Equality pattern: the categorical verdict must match
            # exactly across independent runs. confidence is a real 0-100
            # value and is not required to match exactly (two independent
            # LLM runs will rarely land on the identical integer) — it is
            # only validated as a well-formed number in range. This keeps
            # "strict" meaningfully different from the tolerance-based
            # "soft" evaluation below.
            if not isinstance(leader_result, gl.vm.Return):
                return False

            leader_data = leader_result.calldata
            leader_verdict = leader_data.get("verdict")
            leader_confidence = leader_data.get("confidence")

            if leader_verdict not in ("VALID", "INVALID"):
                return False
            if not isinstance(leader_confidence, int) or not (0 <= leader_confidence <= 100):
                return False

            validator_data = leader_fn()

            return leader_verdict == validator_data.get("verdict")

        result = gl.vm.run_nondet_unsafe(leader_fn, validator_fn)

        ev.verdict = result["verdict"]
        ev.confidence = u256(result["confidence"])
        ev.status = "RESOLVED"
        self.evidences[evidence_id] = ev

        return result

    # ================= SOFT EVALUATION (Tolerance-Based Pattern) =================

    @gl.public.write
    def evaluate_evidence_soft(self, evidence_id: u256):
        assert evidence_id in self.evidences, "Evidence not found"

        ev = self.evidences[evidence_id]
        assert ev.status == "PENDING", "Already evaluated"

        content = ev.content

        # Tolerance band for confidence agreement: two independent LLM runs
        # -- often from genuinely different model providers on GenLayer's
        # validator panel -- rarely produce the identical confidence
        # integer, and different providers have different "calibration"
        # (some report consistently higher or lower confidence for the same
        # judgment). A narrow tolerance treats that calibration gap as
        # disagreement even when the underlying verdict reasoning agrees.
        # Validators agree if verdicts match exactly and confidence scores
        # are within this many points of each other.
        CONFIDENCE_TOLERANCE = 30

        def leader_fn():
            prompt = f"""
            You are performing a SOFT evidence validity check, allowing for
            reasonable interpretive judgment.

            Evidence:
            {content}

            Decide whether this evidence is VALID or INVALID, and how
            confident you are on a scale from 0 to 100.

            Respond with ONLY a JSON object, nothing else, no explanation,
            no markdown formatting. confidence must be a single whole
            number from 0 to 100.

            Example of a correctly formatted response:
            {{"verdict": "INVALID", "confidence": 63}}

            Your response:
            """

            response = gl.nondet.exec_prompt(prompt)
            try:
                data = json.loads(response)
            except Exception:
                raise gl.vm.UserError("[LLM_ERROR] invalid JSON")

            verdict = str(data.get("verdict", "")).upper()
            try:
                confidence = int(data.get("confidence", -1))
            except (TypeError, ValueError):
                raise gl.vm.UserError("[LLM_ERROR] invalid confidence")

            assert verdict in ("VALID", "INVALID"), "[LLM_ERROR] invalid verdict"
            assert 0 <= confidence <= 100, "[LLM_ERROR] confidence out of range"

            return {"verdict": verdict, "confidence": confidence}

        def validator_fn(leader_result):
            # Tolerance-Based pattern: the categorical verdict must still
            # match exactly, but confidence only needs to be "close enough"
            # (within CONFIDENCE_TOLERANCE points) rather than identical.
            # This is a genuinely different agreement rule from the strict
            # evaluation above, not just a different prompt.
            if not isinstance(leader_result, gl.vm.Return):
                return False

            leader_data = leader_result.calldata
            leader_verdict = leader_data.get("verdict")
            leader_confidence = leader_data.get("confidence")

            if leader_verdict not in ("VALID", "INVALID"):
                return False
            if not isinstance(leader_confidence, int) or not (0 <= leader_confidence <= 100):
                return False

            validator_data = leader_fn()

            if leader_verdict != validator_data.get("verdict"):
                return False

            return abs(leader_confidence - validator_data.get("confidence")) <= CONFIDENCE_TOLERANCE

        result = gl.vm.run_nondet_unsafe(leader_fn, validator_fn)

        ev.verdict = result["verdict"]
        ev.confidence = u256(result["confidence"])
        ev.status = "RESOLVED"
        self.evidences[evidence_id] = ev

        return result

    # ================= VIEW =================

    @gl.public.view
    def get_evidence(self, evidence_id: u256) -> str:
        if evidence_id not in self.evidences:
            return "NOT_FOUND"
        ev = self.evidences[evidence_id]
        return f"{ev.status}:{ev.verdict}:{int(ev.confidence)}"

    @gl.public.view
    def get_evidence_details(self, evidence_id: u256) -> str:
        if evidence_id not in self.evidences:
            return "NOT_FOUND"
        ev = self.evidences[evidence_id]
        return json.dumps({
            "id": int(ev.evidence_id),
            "agent": str(ev.agent),
            "content": ev.content,
            "verdict": ev.verdict,
            "confidence": int(ev.confidence),
            "status": ev.status
        })

    @gl.public.view
    def list_evidences(self) -> str:
        items = []
        for key in self.evidences:
            ev = self.evidences[key]
            items.append(f"{int(ev.evidence_id)}:{ev.status}")
        return ",".join(items)

    @gl.public.view
    def get_agent_evidences(self, agent: str) -> str:
        items = []
        for key in self.evidences:
            ev = self.evidences[key]
            if str(ev.agent) == agent:
                items.append(str(int(ev.evidence_id)))
        return ",".join(items)

    # ================= REQUIRED NONDET PLACEHOLDER =================

    def nondet(self):
        return {"nondet": "noop"}
