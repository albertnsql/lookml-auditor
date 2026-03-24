"""
Reporting: JSON export
"""
from __future__ import annotations
import json
from datetime import datetime
from lookml_parser.models import LookMLProject
from validators import Issue, compute_health_score


def build_json_report(
    project: LookMLProject,
    issues: list[Issue],
    output_path: str | None = None,
) -> dict:
    score = compute_health_score(issues)

    report = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "project_name": project.name,
        "project_path": project.root_path,
        "health_score": score,
        "summary": {
            "total_issues": len(issues),
            "errors":   sum(1 for i in issues if i.severity == "error"),
            "warnings": sum(1 for i in issues if i.severity == "warning"),
            "info":     sum(1 for i in issues if i.severity == "info"),
            "views":    len(project.views),
            "explores": len(project.explores),
            "total_fields": sum(len(v.fields) for v in project.views),
        },
        "issues": [i.model_dump() for i in issues],
    }

    if output_path:
        with open(output_path, "w") as f:
            json.dump(report, f, indent=2, default=str)

    return report
