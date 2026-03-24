"""
Validator: Duplicate SQL Table References
------------------------------------------
Flags cases where the same sql_table_name is used in more than one view.
This is usually a copy-paste error and leads to confusion about which
view "owns" a table.
"""
from __future__ import annotations
from collections import defaultdict
from lookml_parser.models import LookMLProject
from .issue import Issue, IssueCategory, Severity


def check_duplicate_table_refs(project: LookMLProject) -> list[Issue]:
    issues = []

    # Group views by normalized sql_table_name (case-insensitive, strip whitespace)
    table_to_views: dict[str, list] = defaultdict(list)
    for view in project.views:
        if view.sql_table_name:
            normalized = view.sql_table_name.strip().lower()
            table_to_views[normalized].append(view)

    for table_name, views in table_to_views.items():
        if len(views) > 1:
            view_names = ", ".join(f"'{v.name}'" for v in views)
            issues.append(Issue(
                category=IssueCategory.DUPLICATE,
                severity=Severity.WARNING,
                message=(
                    f"SQL table '{table_name}' is referenced by {len(views)} views: {view_names}"
                ),
                object_type="view",
                object_name=table_name,
                source_file=views[0].source_file,
                line_number=views[0].line_number,
                suggestion=(
                    f"Check if {view_names} should really point to the same table. "
                    "If intentional, consider consolidating into one view or documenting the reason."
                ),
            ))

    return issues
