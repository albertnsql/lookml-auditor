"""
Validator: Orphaned Objects
----------------------------
Detects:
  1. Views not referenced by ANY explore (orphaned views)
  2. Explores whose base view does not exist (zombie explores)
     — already caught by broken_references, but we surface the explore-level orphan

These are separate from broken references — an orphaned view is structurally
valid but potentially dead code. We flag as INFO (advisory).
"""
from __future__ import annotations
from lookml_parser.models import LookMLProject
from .issue import Issue, IssueCategory, Severity


def check_orphans(project: LookMLProject) -> list[Issue]:
    issues = []
    view_names = {v.name for v in project.views}

    # Build set of all views referenced by at least one explore
    referenced_views: set[str] = set()
    for exp in project.explores:
        referenced_views.add(exp.base_view)
        for join in exp.joins:
            referenced_views.add(join.resolved_view)

    # Case 3: Views used via extends: are referenced (not orphans)
    extended_views: set[str] = set()
    for view in project.views:
        for ext_name in view.extends:
            extended_views.add(ext_name)
    referenced_views.update(extended_views)

    # Orphaned views — exist in project but never referenced by any explore or extends
    for view in project.views:
        if view.name not in referenced_views:
            issues.append(Issue(
                category=IssueCategory.FIELD_QUALITY,
                severity=Severity.INFO,
                message=f"View '{view.name}' is not referenced by any explore (orphaned view)",
                object_type="view",
                object_name=view.name,
                source_file=view.source_file,
                line_number=view.line_number,
                suggestion=(
                    f"Add '{view.name}' to an explore or remove it if it is no longer needed."
                ),
            ))
        elif view.name in extended_views and view.name not in {
            ref for exp in project.explores
            for ref in ([exp.base_view] + [j.resolved_view for j in exp.joins])
        }:
            # View is used via extends but not directly joined — flag as info
            issues.append(Issue(
                category=IssueCategory.FIELD_QUALITY,
                severity=Severity.INFO,
                message=(
                    f"View '{view.name}' is used via extends (not directly joined into an explore)"
                ),
                object_type="view",
                object_name=view.name,
                source_file=view.source_file,
                line_number=view.line_number,
                suggestion=(
                    f"This view is extended by another view — this is expected LookML behavior."
                ),
            ))

    # Zombie explores — explores whose base view no longer exists
    for exp in project.explores:
        if exp.base_view not in view_names:
            issues.append(Issue(
                category=IssueCategory.BROKEN_REFERENCE,
                severity=Severity.ERROR,
                message=(
                    f"Explore '{exp.name}' is based on view '{exp.base_view}' "
                    f"which does not exist — this explore is effectively broken"
                ),
                object_type="explore",
                object_name=exp.name,
                source_file=exp.source_file,
                line_number=exp.line_number,
                suggestion=(
                    f"Define view '{exp.base_view}' or update the explore's "
                    f"'from:' / 'view_name:' field."
                ),
            ))

    return issues
