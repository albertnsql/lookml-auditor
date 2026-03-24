"""
Orphan Detector
---------------
Finds:
  1. Views not referenced by any explore (orphan views)
  2. Explores whose base view doesn't exist (ghost explores)

These are returned as structured data, not Issues, so they can be
displayed separately in the overview without polluting the issue score.
"""
from __future__ import annotations
from lookml_parser.models import LookMLProject


def find_orphan_views(project: LookMLProject) -> list[str]:
    """Views that are never used in any explore (base or join)."""
    referenced: set[str] = set()
    for explore in project.explores:
        referenced.add(explore.base_view)
        for join in explore.joins:
            referenced.add(join.resolved_view)
    return sorted(v.name for v in project.views if v.name not in referenced)


def find_ghost_explores(project: LookMLProject) -> list[str]:
    """Explores whose base_view doesn't exist in the project."""
    view_names = {v.name for v in project.views}
    return sorted(
        e.name for e in project.explores if e.base_view not in view_names
    )


def find_orphan_explores(project: LookMLProject) -> list[str]:
    """
    Explores that have ALL joins pointing to missing views
    (i.e. the explore itself is essentially broken).
    """
    view_names = {v.name for v in project.views}
    broken = []
    for exp in project.explores:
        base_missing = exp.base_view not in view_names
        all_joins_broken = all(
            j.resolved_view not in view_names for j in exp.joins
        ) if exp.joins else False
        if base_missing and (not exp.joins or all_joins_broken):
            broken.append(exp.name)
    return sorted(broken)
