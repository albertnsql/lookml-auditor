"""
Validator: Join Integrity

Fixes applied:
  Case 4 & 5: sql_on view references are checked against the full set of
    valid aliases per explore. An explore with 'from: sales_analysis' creates
    alias 'np_mail_order' — ${np_mail_order.field} is valid. Similarly a join
    with 'from: np_date_dim' creates alias 'np_date_dim_booked' — valid too.
    All names are normalised to lowercase before lookup.

  Case 6: Joins with type: cross do not require sql_on or foreign_key.
    We skip the missing-condition check for cross joins.

  Case 7: All view/explore/join name lookups are case-insensitive.
    'NP_Flash' matches 'np_flash' in the view map.

  Dimension_group sub-field awareness (existing):
    ${view.field_date}, ${view.field_month} etc. are never flagged.
"""
from __future__ import annotations
import re
from lookml_parser.models import LookMLProject, LookMLJoin, LookMLExplore
from .issue import Issue, IssueCategory, Severity

_FIELD_REF_RE = re.compile(r'\$\{(\w+)\.(\w+)\}')

_DIM_GROUP_SUFFIXES = {
    "date", "week", "month", "quarter", "year", "raw",
    "time", "hour", "minute", "second", "day_of_week",
    "day_of_week_index", "day_of_month", "day_of_year",
    "week_of_year", "month_num", "month_name", "fiscal_month_num",
    "fiscal_quarter", "fiscal_quarter_of_year", "fiscal_year",
}

# Join types that never require a sql_on / foreign_key
_NO_CONDITION_TYPES = {"cross"}


def _is_dim_group_subfield(field_ref: str, view_name_ci: str, view_map_ci: dict) -> bool:
    target_view = view_map_ci.get(view_name_ci.lower())
    if not target_view:
        return False
    dim_group_names = {f.name.lower() for f in target_view.fields
                       if f.field_type == "dimension_group"}
    for dg_name in dim_group_names:
        if field_ref.lower().startswith(dg_name + "_"):
            suffix = field_ref.lower()[len(dg_name) + 1:]
            if suffix in _DIM_GROUP_SUFFIXES:
                return True
    if dim_group_names:
        for suffix in _DIM_GROUP_SUFFIXES:
            if field_ref.lower().endswith("_" + suffix):
                return True
    return False


def check_join_integrity(project: LookMLProject) -> list[Issue]:
    # Case 7: case-insensitive view map
    view_map_ci = {v.name.lower(): v for v in project.views}
    issues = []
    for explore in project.explores:
        issues.extend(_check_explore(explore, project, view_map_ci))
    return issues


def _check_explore(explore: LookMLExplore, project: LookMLProject,
                   view_map_ci: dict) -> list[Issue]:
    issues = []

    # Build valid alias set (case-insensitive) for this explore:
    #   - explore name itself (may differ from base view when from: is used)
    #   - base view name
    #   - each join's name (the alias Looker exposes in sql_on)
    #   - each join's from_view (the actual underlying view)
    valid_aliases_ci: set[str] = set()
    valid_aliases_ci.add(explore.name.lower())
    valid_aliases_ci.add(explore.base_view.lower())
    for join in explore.joins:
        valid_aliases_ci.add(join.name.lower())
        if join.from_view:
            valid_aliases_ci.add(join.from_view.lower())

    for join in explore.joins:
        issues.extend(_check_join(join, explore, valid_aliases_ci, view_map_ci))

    return issues


def _check_join(join: LookMLJoin, explore: LookMLExplore,
                valid_aliases_ci: set[str], view_map_ci: dict) -> list[Issue]:
    issues = []
    join_type_ci = (join.type or "").lower().strip()

    # Case 6: cross joins never need a condition
    # Case 5 (new): sql_where can act as a join condition — downgrade to warning
    if not join.sql_on and not join.foreign_key:
        if join.sql_where:
            # sql_where is present — functional but non-standard join condition
            issues.append(Issue(
                category=IssueCategory.JOIN_INTEGRITY,
                severity=Severity.WARNING,
                message=(
                    f"Join '{join.name}' in explore '{explore.name}' "
                    f"uses sql_where instead of sql_on for its join condition"
                ),
                object_type="join",
                object_name=join.name,
                source_file=join.source_file,
                line_number=join.line_number,
                suggestion=(
                    "Consider using 'sql_on:' for standard join conditions. "
                    "'sql_where:' works but is less explicit about the join relationship."
                ),
            ))
        elif join_type_ci not in _NO_CONDITION_TYPES:
            issues.append(Issue(
                category=IssueCategory.JOIN_INTEGRITY,
                severity=Severity.ERROR,
                message=(
                    f"Join '{join.name}' in explore '{explore.name}' "
                    f"has no sql_on or foreign_key defined"
                ),
                object_type="join",
                object_name=join.name,
                source_file=join.source_file,
                line_number=join.line_number,
                suggestion="Add a 'sql_on:' or 'foreign_key:' clause to define the join condition.",
            ))
        return issues

    # Validate field refs in sql_on
    if join.sql_on:
        for view_ref, field_ref in _FIELD_REF_RE.findall(join.sql_on):
            view_ref_ci = view_ref.lower()

            # Case 4, 5, 7: if view_ref is a known alias → valid, skip
            if view_ref_ci in valid_aliases_ci:
                continue

            target_view = view_map_ci.get(view_ref_ci)
            if target_view is None:
                issues.append(Issue(
                    category=IssueCategory.JOIN_INTEGRITY,
                    severity=Severity.ERROR,
                    message=(
                        f"sql_on in join '{join.name}' (explore '{explore.name}') "
                        f"references unknown view '{view_ref}'"
                    ),
                    object_type="join",
                    object_name=join.name,
                    source_file=join.source_file,
                    line_number=join.line_number,
                    suggestion=f"Ensure view '{view_ref}' is defined in the project.",
                ))
            elif field_ref not in {f.name for f in target_view.fields}:
                if _is_dim_group_subfield(field_ref, view_ref_ci, view_map_ci):
                    continue
                issues.append(Issue(
                    category=IssueCategory.JOIN_INTEGRITY,
                    severity=Severity.WARNING,
                    message=(
                        f"sql_on in join '{join.name}' (explore '{explore.name}') "
                        f"references field '{view_ref}.{field_ref}' which is not defined"
                    ),
                    object_type="join",
                    object_name=join.name,
                    source_file=join.source_file,
                    line_number=join.line_number,
                    suggestion=(
                        f"Add dimension '{field_ref}' to view '{view_ref}' "
                        "or fix the sql_on reference."
                    ),
                ))

    # Missing relationship
    if not join.relationship:
        issues.append(Issue(
            category=IssueCategory.JOIN_INTEGRITY,
            severity=Severity.WARNING,
            message=(
                f"Join '{join.name}' in explore '{explore.name}' "
                f"is missing a 'relationship:' definition"
            ),
            object_type="join",
            object_name=join.name,
            source_file=join.source_file,
            line_number=join.line_number,
            suggestion="Add 'relationship: many_to_one' (or appropriate type) to avoid fanout issues.",
        ))

    return issues
