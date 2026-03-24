"""
Validator: Unused Objects
--------------------------
Detects views not referenced by any explore, and fields
that appear unused (no SQL references to them anywhere in the project).
"""
from __future__ import annotations
import re
from lookml_parser.models import LookMLProject
from .issue import Issue, IssueCategory, Severity


def _all_sql_text(project: LookMLProject) -> str:
    """Collect all SQL expressions in the project for cross-referencing."""
    parts = []
    for view in project.views:
        for field in view.fields:
            if field.sql:
                parts.append(field.sql)
    for explore in project.explores:
        for join in explore.joins:
            if join.sql_on:
                parts.append(join.sql_on)
    return "\n".join(parts)


def check_unused_objects(project: LookMLProject) -> list[Issue]:
    issues = []

    # ── Unused views ──────────────────────────────────────────────────────
    referenced_views: set[str] = set()
    for explore in project.explores:
        referenced_views.add(explore.base_view)
        for join in explore.joins:
            referenced_views.add(join.resolved_view)

    for view in project.views:
        if view.name not in referenced_views:
            issues.append(Issue(
                category=IssueCategory.UNUSED,
                severity=Severity.WARNING,
                message=f"View '{view.name}' is not referenced by any explore",
                object_type="view",
                object_name=view.name,
                source_file=view.source_file,
                line_number=view.line_number,
                suggestion="Consider adding this view to an explore or removing it if obsolete.",
            ))

    # ── Unused fields ─────────────────────────────────────────────────────
    # A field is "potentially unused" if its qualified name (view_name.field_name)
    # does not appear anywhere in SQL expressions or sql_on clauses.
    all_sql = _all_sql_text(project)

    for view in project.views:
        for field in view.fields:
            qualified = f"{view.name}.{field.name}"
            # Also check short-form reference ${field_name} and ${TABLE}.field_name
            short_ref = f"${{{field.name}}}"
            if qualified not in all_sql and short_ref not in all_sql:
                issues.append(Issue(
                    category=IssueCategory.UNUSED,
                    severity=Severity.INFO,
                    message=f"Field '{qualified}' appears to be unused (no SQL references found)",
                    object_type="field",
                    object_name=qualified,
                    source_file=field.source_file,
                    line_number=field.line_number,
                    suggestion="Verify this field is actually needed; consider hiding or removing it.",
                ))

    return issues
