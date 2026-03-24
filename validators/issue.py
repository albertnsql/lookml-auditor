"""
Issue model — the shared output type for all validators.
"""
from __future__ import annotations
from enum import Enum
from pydantic import BaseModel


class Severity(str, Enum):
    ERROR   = "error"
    WARNING = "warning"
    INFO    = "info"


class IssueCategory(str, Enum):
    BROKEN_REFERENCE  = "Broken Reference"
    DUPLICATE         = "Duplicate Definition"
    JOIN_INTEGRITY    = "Join Integrity"
    FIELD_QUALITY     = "Field Quality"
    # DOCUMENTATION removed per request


class Issue(BaseModel):
    category: IssueCategory
    severity: Severity
    message: str
    object_type: str          # "view" | "explore" | "field" | "join"
    object_name: str
    source_file: str = ""
    line_number: int = 0
    suggestion: str = ""

    def __str__(self) -> str:
        loc = f" ({self.source_file}:{self.line_number})" if self.source_file else ""
        return f"[{self.severity.upper()}] {self.category} — {self.message}{loc}"
