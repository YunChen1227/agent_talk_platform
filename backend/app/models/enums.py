from enum import Enum

class AgentStatus(str, Enum):
    IDLE = "IDLE"
    MATCHING = "MATCHING"
    PAIRED = "PAIRED"
    DONE = "DONE"

class SessionStatus(str, Enum):
    ACTIVE = "ACTIVE"
    JUDGING = "JUDGING"
    COMPLETED = "COMPLETED"
    TERMINATED = "TERMINATED"

class Verdict(str, Enum):
    CONSENSUS = "CONSENSUS"
    DEADLOCK = "DEADLOCK"
    PENDING = "PENDING"
