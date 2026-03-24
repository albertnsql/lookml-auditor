"""
Validator: Field Documentation Quality
----------------------------------------
Optimised single-pass: instead of generating one Issue per field (which creates
tens of thousands of Issue objects for large repos), we generate one summary
Issue per VIEW listing missing counts. This dramatically reduces object allocation.

Hidden fields are excluded. Only dimensions, dimension_groups, and measures checked.
"""
from __future__ import annotations
from lookml_parser.models import LookMLProject
from .issue import Issue, IssueCategory, Severity


def check_field_documentation(project: LookMLProject) -> list[Issue]:
    issues = []
    ELIGIBLE = {"dimension", "dimension_group", "measure"}

    for view in project.views:
        missing_label  = []
        missing_desc   = []

        for field in view.fields:
            if field.hidden or field.field_type not in ELIGIBLE:
                continue
            if not field.label:       missing_label.append(field.name)
            if not field.description: missing_desc.append(field.name)

        if missing_label or missing_desc:
            parts = []
            if missing_label:
                parts.append(f"{len(missing_label)} field(s) missing label")
            if missing_desc:
                parts.append(f"{len(missing_desc)} field(s) missing description")

            issues.append(Issue(
                category=IssueCategory.FIELD_QUALITY,
                severity=Severity.INFO,
                message=f"View '{view.name}': {'; '.join(parts)}",
                object_type="view",
                object_name=view.name,
                source_file=view.source_file,
                line_number=view.line_number,
                suggestion=(
                    f"Add label/description to fields in '{view.name}' "
                    "to improve Looker UI discoverability."
                ),
            ))

    return issues
