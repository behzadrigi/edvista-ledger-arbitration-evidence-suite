# ReputationLedger.py

class ReputationLedger:

    def __init__(self):
        # State: mapping agent_id -> reputation score
        self.scores = {}

    def register_agent(self, agent_id: str, initial_score: int):
        """
        Register a new agent with an initial reputation score.
        """
        if agent_id in self.scores:
            return {"error": "Agent already registered"}

        self.scores[agent_id] = initial_score
        return {"status": "registered", "agent_id": agent_id, "score": initial_score}

    def get_score(self, agent_id: str):
        """
        Return the current reputation score of an agent.
        """
        if agent_id not in self.scores:
            return {"error": "Agent not found"}

        return {"agent_id": agent_id, "score": self.scores[agent_id]}

    def update_score(self, agent_id: str, delta: int):
        """
        Update reputation score by a delta (positive or negative).
        """
        if agent_id not in self.scores:
            return {"error": "Agent not found"}

        self.scores[agent_id] += delta
        return {"agent_id": agent_id, "new_score": self.scores[agent_id]}

    def nondet(self):
        """
        Required nondeterministic function for GenLayer contracts.
        This contract does not use nondet logic, but must define it.
        """
        return {"nondet": "noop"}
