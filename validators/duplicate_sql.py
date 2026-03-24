"""
Validator: Duplicate SQL Expressions within a View
----------------------------------------------------
Cases 3 & 4:
  - Case 3: Two measures with same SQL but different value_format/filters
    → WARNING, clearly named as dimension/measure, shows value_format diff hint
  - Case 4: If one of the duplicate fields is a primary key → INFO (often intentional alias)
"""
from __future__ import annotations
from collections import defaultdict
from lookml_parser.models import LookMLProject, LookMLField, LookMLView
from .issue import Issue, IssueCategory, Severity


def _normalise_sql(sql: str) -> str:
    return sql.strip().lower().replace('"', '').replace("'", '').replace(' ', '')


def _field_kind(field: LookMLField) -> str:
    """Return human-readable type label."""
    if field.field_type == "measure":         return "measure"
    if field.field_type == "dimension_group": return "dimension group"
    return "dimension"


def check_duplicate_sql(project: LookMLProject) -> list[Issue]:
    issues = []
    SKIP = {"${table}", "1", "true", "false", "null", ""}

    for view in project.views:
        # Map: normalised SQL → list of LookMLField objects
        sql_to_fields: dict[str, list[LookMLField]] = defaultdict(list)
        for field in view.fields:
            if not field.sql or field.field_type not in ("dimension", "dimension_group", "measure"):
                continue
            norm = _normalise_sql(field.sql)
            if len(norm) < 5 or norm in SKIP:
                continue
            sql_to_fields[norm].append(field)

        for norm_sql, fields in sql_to_fields.items():
            if len(fields) < 2:
                continue

            names = [f.name for f in fields]
            has_pk = any(f.primary_key for f in fields)

            # Case 4: one field is a primary key — INFO, not WARNING
            if has_pk:
                pk_field    = next(f for f in fields if f.primary_key)
                other_fields= [f for f in fields if not f.primary_key]
                other_names = ", ".join(f"'{f.name}'" for f in other_fields)
                kinds       = ", ".join(f"({_field_kind(f)})" for f in other_fields)
                issues.append(Issue(
                    category=IssueCategory.DUPLICATE,
                    severity=Severity.INFO,
                    message=(
                        f"Duplicate SQL in view '{view.name}': "
                        f"'{pk_field.name}' (primary key) shares SQL with {other_names} {kinds}"
                    ),
                    object_type="field",
                    object_name=f"{view.name}.{pk_field.name}",
                    source_file=view.source_file,
                    line_number=view.line_number,
                    suggestion=(
                        f"'{pk_field.name}' is a primary key — sharing SQL with {other_names} "
                        "is often intentional. No action needed unless the duplication is unintended."
                    ),
                ))
                continue

            # Case 3: regular duplicate SQL — WARNING
            # Build per-field detail for the message
            field_details = []
            for f in fields:
                vf = getattr(f, 'value_format', None) or ""
                detail = f"'{f.name}' ({_field_kind(f)})"
                if vf:
                    detail += f" [format: {vf}]"
                field_details.append(detail)
            detail_str = ", ".join(field_details)

            issues.append(Issue(
                category=IssueCategory.DUPLICATE,
                severity=Severity.WARNING,
                message=(
                    f"Duplicate SQL in view '{view.name}': {detail_str} share identical SQL"
                ),
                object_type="field",
                object_name=f"{view.name}.*",
                source_file=view.source_file,
                line_number=view.line_number,
                suggestion=(
                    f"Fields {', '.join(repr(n) for n in names)} in view '{view.name}' "
                    "share the same SQL expression. If intentional (e.g. different value formats), "
                    "add a comment to document the intent. Otherwise remove the redundant definition."
                ),
            ))

    return issues
