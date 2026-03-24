"""
Validator runner — executes all checks and returns consolidated results.

Scoring v2: ratio-based per-category scoring.
Instead of flat penalties per issue (which crushes large repos),
each category is scored as a % of objects that are clean.
Overall score = weighted average of category scores.

This means a repo with 1000 views and 5 broken refs scores ~99 on that
category (99.5% clean), whereas a repo with 10 views and 5 broken refs
scores ~50 (50% clean). Proportional and fair.
"""
from __future__ import annotations
from lookml_parser.models import LookMLProject
from .issue import Issue, IssueCategory, Severity
from .broken_references import check_broken_references
from .duplicates import check_duplicates
from .duplicate_tables import check_duplicate_table_refs
from .duplicate_sql import check_duplicate_sql
from .join_integrity import check_join_integrity
from .primary_keys import check_primary_keys
from .field_documentation import check_field_documentation
from .orphans import check_orphans


ALL_CHECKS = [
    check_broken_references,
    check_duplicates,
    check_duplicate_table_refs,
    check_duplicate_sql,
    check_join_integrity,
    check_primary_keys,
    check_field_documentation,
    check_orphans,
]


def run_all_checks(project: LookMLProject) -> list[Issue]:
    issues: list[Issue] = []
    for check_fn in ALL_CHECKS:
        issues.extend(check_fn(project))
    return issues


def compute_health_score(issues: list[Issue], project: LookMLProject | None = None) -> int:
    """
    Ratio-based health score (0–100).

    Each category is scored as: 100 × (1 − issue_rate)
    where issue_rate = issues_in_category / max_possible_objects

    Overall = weighted average across categories:
      Broken Reference  35% — structural correctness (most critical)
      Duplicate Def     25% — code hygiene
      Join Integrity    25% — model correctness
      Field Quality     15% — documentation / PK quality (advisory)

    Falls back to a simplified absolute penalty if no project is provided.
    """
    if project is None:
        # Fallback: simple absolute penalty (used in tests without project)
        errors   = sum(1 for i in issues if i.severity == Severity.ERROR)
        warnings = sum(1 for i in issues if i.severity == Severity.WARNING)
        infos    = sum(1 for i in issues if i.severity == Severity.INFO)
        ep = min(errors   * 8,   70)
        wp = min(warnings * 1,   10)
        ip = min(infos    * 0.1,  5)
        return max(0, int(100 - ep - wp - ip))

    # ── Denominators (max objects that could have issues) ──────────────────
    n_views    = max(len(project.views),    1)
    n_explores = max(len(project.explores), 1)
    n_fields   = max(sum(len(v.fields) for v in project.views), 1)
    # Joins: sum of all joins across all explores
    n_joins    = max(sum(len(e.joins) for e in project.explores), 1)

    # ── Category issue counts ──────────────────────────────────────────────
    by_cat: dict[IssueCategory, int] = {c: 0 for c in IssueCategory}
    for issue in issues:
        by_cat[issue.category] += 1

    broken_count  = by_cat[IssueCategory.BROKEN_REFERENCE]
    dup_count     = by_cat[IssueCategory.DUPLICATE]
    join_count    = by_cat[IssueCategory.JOIN_INTEGRITY]
    quality_count = by_cat[IssueCategory.FIELD_QUALITY]

    # ── Per-category scores ────────────────────────────────────────────────
    # Denominator choice: how many objects COULD be broken in each category
    def _cat_score(n_issues: int, denominator: int) -> float:
        rate = min(n_issues / denominator, 1.0)
        return 100.0 * (1.0 - rate)

    s_broken  = _cat_score(broken_count,  n_explores + n_joins)
    s_dup     = _cat_score(dup_count,     n_views + n_fields)
    s_join    = _cat_score(join_count,    n_joins * 2)   # ×2: sql_on + relationship checks
    s_quality = _cat_score(quality_count, n_fields + n_views)

    # ── Weighted average ───────────────────────────────────────────────────
    score = (
        s_broken  * 0.35 +
        s_dup     * 0.25 +
        s_join    * 0.25 +
        s_quality * 0.15
    )

    return max(0, min(100, int(score)))


def compute_category_scores(issues: list[Issue],
                            project: LookMLProject) -> dict[str, int]:
    """Return per-category scores for display in the dashboard."""
    n_views    = max(len(project.views),    1)
    n_explores = max(len(project.explores), 1)
    n_fields   = max(sum(len(v.fields) for v in project.views), 1)
    n_joins    = max(sum(len(e.joins) for e in project.explores), 1)

    by_cat: dict[IssueCategory, int] = {c: 0 for c in IssueCategory}
    for issue in issues:
        by_cat[issue.category] += 1

    def _s(n_issues, denom):
        return max(0, int(100 * (1 - min(n_issues / denom, 1.0))))

    return {
        "Broken Reference":  _s(by_cat[IssueCategory.BROKEN_REFERENCE],  n_explores + n_joins),
        "Duplicate Def":     _s(by_cat[IssueCategory.DUPLICATE],          n_views + n_fields),
        "Join Integrity":    _s(by_cat[IssueCategory.JOIN_INTEGRITY],      n_joins * 2),
        "Field Quality":     _s(by_cat[IssueCategory.FIELD_QUALITY],       n_fields + n_views),
    }


__all__ = [
    "run_all_checks", "compute_health_score", "compute_category_scores",
    "Issue", "IssueCategory", "Severity",
]
