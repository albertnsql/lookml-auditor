"""
Validator: Broken References

Handles LookML aliasing patterns correctly:
  - explore: alias { from: actual_view }   → alias is valid in sql_on
  - join: alias { from: actual_view }      → join alias is valid in sql_on
  - All lookups are case-insensitive

valid_aliases_ci contains ALL names that are valid as view references in sql_on
for a given explore:
  1. explore.name (the alias Looker exposes)
  2. explore.base_view (the underlying view, resolved through from:/view_name:)
  3. each join.name (join aliases)
  4. each join.from_view (underlying view of each join)
"""
from __future__ import annotations
import re
from lookml_parser.models import LookMLProject
from .issue import Issue, IssueCategory, Severity

_FIELD_REF_RE = re.compile(r'\$\{(\w+)\.(\w+)\}')


def check_broken_references(project: LookMLProject) -> list[Issue]:
    issues = []
    # Case-insensitive view name lookup
    view_names_ci = {v.name.lower() for v in project.views}

    def _view_exists(name: str) -> bool:
        return name.lower() in view_names_ci

    for explore in project.explores:
        # Build full set of valid aliases for this explore (all case-insensitive):
        # - explore name itself (always an alias, even when from: differs)
        # - underlying base view
        # - each join's alias name
        # - each join's from_view (the underlying view of a join alias)
        valid_aliases_ci: set[str] = {
            explore.name.lower(),
            explore.base_view.lower(),
        }
        for join in explore.joins:
            valid_aliases_ci.add(join.name.lower())
            if join.from_view:
                valid_aliases_ci.add(join.from_view.lower())

        # Check base view exists
        if not _view_exists(explore.base_view):
            issues.append(Issue(
                category=IssueCategory.BROKEN_REFERENCE,
                severity=Severity.ERROR,
                message=(
                    f"Explore '{explore.name}' references missing base view "
                    f"'{explore.base_view}'"
                ),
                object_type="explore",
                object_name=explore.name,
                source_file=explore.source_file,
                line_number=explore.line_number,
                suggestion=(
                    f"Create a view named '{explore.base_view}' or update "
                    f"the explore's 'from:' / 'view_name:' field."
                ),
            ))

        # Check each join's resolved view exists
        for join in explore.joins:
            resolved = join.resolved_view
            if not _view_exists(resolved):
                issues.append(Issue(
                    category=IssueCategory.BROKEN_REFERENCE,
                    severity=Severity.ERROR,
                    message=(
                        f"Join '{join.name}' in explore '{explore.name}' "
                        f"references missing view '{resolved}'"
                    ),
                    object_type="join",
                    object_name=join.name,
                    source_file=join.source_file,
                    line_number=join.line_number,
                    suggestion=(
                        f"Define a view named '{resolved}' or correct the join 'from:' value."
                    ),
                ))

            # Validate field refs in sql_on
            if join.sql_on:
                for view_ref, field_ref in _FIELD_REF_RE.findall(join.sql_on):
                    # Any known alias is valid — skip it
                    if view_ref.lower() in valid_aliases_ci:
                        continue
                    if not _view_exists(view_ref):
                        issues.append(Issue(
                            category=IssueCategory.BROKEN_REFERENCE,
                            severity=Severity.ERROR,
                            message=(
                                f"sql_on in join '{join.name}' (explore '{explore.name}') "
                                f"references unknown view '{view_ref}'"
                            ),
                            object_type="join",
                            object_name=join.name,
                            source_file=join.source_file,
                            line_number=join.line_number,
                            suggestion=(
                                f"Ensure view '{view_ref}' is defined in the project."
                            ),
                        ))

    return issues
