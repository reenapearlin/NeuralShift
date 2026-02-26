from enum import Enum


class UserRole(str, Enum):
    ADMIN = "admin"
    LAWYER = "lawyer"


class CaseStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
