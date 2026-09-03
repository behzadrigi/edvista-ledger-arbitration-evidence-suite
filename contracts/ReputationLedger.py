# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

from genlayer import *
from dataclasses import dataclass


@allow_storage
@dataclass
class ReputationRecord:
    agent: Address
    score: u256
    history: str   # JSON log of changes


class ReputationLedger(gl.Contract):
    records: TreeMap[u256, ReputationRecord]
    next_id: u256

    def __init__(self):
        self.next_id = u256(0)

    # ================= REGISTER AGENT =================

    @gl.public.write
    def register_agent(self, agent: str, initial_score: u256) -> u256:
        assert initial_score >= 0, "Initial score must be non-negative"

        agent_address = Address(agent)
        record_id = self.next_id
        self.next_id += u256(1)

        self.records[record_id] = ReputationRecord(
            agent=agent_address,
            score=initial_score,
            history=f"[REGISTERED:{int(initial_score)}]"
        )

        return record_id

    # ================= UPDATE SCORE =================

    @gl.public.write
    def update_score(self, record_id: u256, delta: u256):
        assert record_id in self.records, "Record not found"

        record = self.records[record_id]
        new_score = u256(int(record.score) + int(delta))

        record.score = new_score
        record.history += f";UPDATE:{int(delta)}"
        self.records[record_id] = record

        return {"new_score": int(new_score)}

    # ================= VIEW METHODS =================

    @gl.public.view
    def get_score(self, record_id: u256) -> u256:
        if record_id not in self.records:
            return u256(0)
        return self.records[record_id].score

    @gl.public.view
    def get_history(self, record_id: u256) -> str:
        if record_id not in self.records:
            return "NOT_FOUND"
        return self.records[record_id].history

    # ================= REQUIRED NONDET =================

    def nondet(self):
        return {"nondet": "noop"}
