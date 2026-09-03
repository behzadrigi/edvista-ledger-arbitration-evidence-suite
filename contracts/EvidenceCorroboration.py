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
            STRICT MODE:

            Evidence:
            {content}

            Respond ONLY with JSON:
            {{
                "verdict": "VALID" or "INVALID",
                "confidence": <integer: 80, 90>
            }}
            """

            response = gl.nondet.exec_prompt(prompt)
            try:
                data = json.loads(response)
            except:
                raise gl.vm.UserError("[LLM_ERROR] invalid JSON")

            verdict = str(data.get("verdict", "")).upper()
            confidence = int(data.get("confidence", 0))

            assert verdict in ("VALID", "INVALID"), "[LLM_ERROR] invalid verdict"
            assert confidence in (80, 90), "[LLM_ERROR] invalid confidence"

            return {"verdict": verdict, "confidence": confidence}

        def validator_fn(leader_result):
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

        ev.verdict = result["verdict"]
        ev.confidence = u256(result["confidence"])
        ev.status = "RESOLVED"
        self.evidences[evidence_id] = ev

        return result

    # ================= SOFT EVALUATION =================

    @gl.public.write
    def evaluate_evidence_soft(self, evidence_id: u256):
        assert evidence_id in self.evidences, "Evidence not found"

        ev = self.evidences[evidence_id]
        assert ev.status == "PENDING", "Already evaluated"

        content = ev.content

        def leader_fn():
            prompt = f"""
            SOFT MODE:

            Evidence:
            {content}

            Respond ONLY with JSON:
            {{
                "verdict": "VALID" or "INVALID",
                "confidence": <integer: 60, 70>
            }}
            """

            response = gl.nondet.exec_prompt(prompt)
            try:
                data = json.loads(response)
            except:
                raise gl.vm.UserError("[LLM_ERROR] invalid JSON")

            verdict = str(data.get("verdict", "")).upper()
            confidence = int(data.get("confidence", 0))

            assert verdict in ("VALID", "INVALID"), "[LLM_ERROR] invalid verdict"
            assert confidence in (60, 70), "[LLM_ERROR] invalid confidence"

            return {"verdict": verdict, "confidence": confidence}

        def validator_fn(leader_result):
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
