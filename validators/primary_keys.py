"""
Validator: Primary Key Checks
------------------------------
Flags views that have no primary_key: yes dimension defined.
A missing primary key causes fanout bugs and incorrect counts in Looker.
"""
from __future__ import annotations
from lookml_parser.models import LookMLProject
from .issue import Issue, IssueCategory, Severity


def check_primary_keys(project: LookMLProject) -> list[Issue]:
    issues = []

    for view in project.views:
        if not view.has_primary_key:
            issues.append(Issue(
                category=IssueCategory.FIELD_QUALITY,
                severity=Severity.WARNING,
                message=f"View '{view.name}' has no primary key defined (missing 'primary_key: yes')",
                object_type="view",
                object_name=view.name,
                source_file=view.source_file,
                line_number=view.line_number,
                suggestion=(
                    f"Add 'primary_key: yes' to the unique identifier dimension in view '{view.name}'. "
                    "This prevents fanout and ensures correct COUNT DISTINCT behavior."
                ),
            ))

    return issues
