from enum import Enum, auto
from dataclasses import dataclass
from typing import Optional


class DisputeState(Enum):
    REGISTERED = auto()          # Agent registered, no dispute yet
    OPEN = auto()                # Dispute opened
    EVIDENCE_SUBMITTED = auto()  # Evidence submitted
    UNDER_CONSENSUS = auto()     # Consensus running (leader + validators)
    SETTLED = auto()             # Final score applied, dispute closed
    CANCELLED = auto()           # Dispute cancelled (before or after evidence)
    TIMEOUT_RECOVERY = auto()    # Timeout path triggered
    CLOSED = auto()              # Fully closed, no further actions


@dataclass
class Dispute:
    dispute_id: str
    agent_id: str
    current_state: DisputeState
    initial_score: int
    final_score: Optional[int] = None
    evidence: Optional[str] = None
    consensus_decision: Optional[str] = None
    consensus_percent_change: Optional[float] = None
    timeout_triggered: bool = False
    cancelled: bool = False


class InvalidTransition(Exception):
    pass


class DisputeStateMachine:
    def __init__(self, dispute: Dispute):
        self.dispute = dispute

    def open_dispute(self):
        if self.dispute.current_state != DisputeState.REGISTERED:
            raise InvalidTransition("Can only open dispute from REGISTERED state.")
        self.dispute.current_state = DisputeState.OPEN

    def submit_evidence(self, evidence: str):
        if self.dispute.current_state != DisputeState.OPEN:
            raise InvalidTransition("Can only submit evidence from OPEN state.")
        self.dispute.evidence = evidence
        self.dispute.current_state = DisputeState.EVIDENCE_SUBMITTED

    def start_consensus(self):
        if self.dispute.current_state != DisputeState.EVIDENCE_SUBMITTED:
            raise InvalidTransition("Can only start consensus after evidence is submitted.")
        self.dispute.current_state = DisputeState.UNDER_CONSENSUS

    def apply_settlement(self, final_score: int, decision: str, percent_change: float):
        if self.dispute.current_state != DisputeState.UNDER_CONSENSUS:
            raise InvalidTransition("Can only settle from UNDER_CONSENSUS state.")
        self.dispute.final_score = final_score
        self.dispute.consensus_decision = decision
        self.dispute.consensus_percent_change = percent_change
        self.dispute.current_state = DisputeState.SETTLED

    def trigger_timeout_recovery(self):
        if self.dispute.current_state not in (
            DisputeState.EVIDENCE_SUBMITTED,
            DisputeState.UNDER_CONSENSUS,
        ):
            raise InvalidTransition("Timeout recovery only valid after evidence submission.")
        self.dispute.timeout_triggered = True
        self.dispute.current_state = DisputeState.TIMEOUT_RECOVERY

    def cancel_before_submission(self):
        if self.dispute.current_state != DisputeState.OPEN:
            raise InvalidTransition("Can only cancel before evidence from OPEN state.")
        self.dispute.cancelled = True
        self.dispute.current_state = DisputeState.CANCELLED

    def cancel_after_submission(self):
        if self.dispute.current_state not in (
            DisputeState.EVIDENCE_SUBMITTED,
            DisputeState.UNDER_CONSENSUS,
            DisputeState.TIMEOUT_RECOVERY,
        ):
            raise InvalidTransition("Can only cancel after evidence from valid post-submission states.")
        self.dispute.cancelled = True
        self.dispute.current_state = DisputeState.CANCELLED

    def close_dispute(self):
        if self.dispute.current_state not in (
            DisputeState.SETTLED,
            DisputeState.CANCELLED,
            DisputeState.TIMEOUT_RECOVERY,
        ):
            raise InvalidTransition("Can only close dispute from terminal states.")
        self.dispute.current_state = DisputeState.CLOSED
