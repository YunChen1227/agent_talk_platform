from enum import Enum

class AgentStatus(str, Enum):
    IDLE = "IDLE"
    MATCHING = "MATCHING"

class SessionStatus(str, Enum):
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    TERMINATED = "TERMINATED"

class Verdict(str, Enum):
    CONSENSUS = "CONSENSUS"
    DEADLOCK = "DEADLOCK"
    PENDING = "PENDING"
