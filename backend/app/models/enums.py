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

class MediaFileType(str, Enum):
    IMAGE = "image"
    VIDEO = "video"

class ProductStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class MatchStatus(str, Enum):
    CONSENSUS = "CONSENSUS"
    CHATTING = "CHATTING"
    DEADLOCK = "DEADLOCK"
    NOT_MATCHED = "NOT_MATCHED"
