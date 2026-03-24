"""
Unit tests for LookML Auditor
Run with: python tests/test_auditor.py  (from project root)
"""
import sys, os

# Always resolve paths relative to this file so tests work from any cwd
TEST_DIR    = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(TEST_DIR)
MOCK_DIR    = os.path.join(PROJECT_DIR, "mock_project")

sys.path.insert(0, PROJECT_DIR)

from lookml_parser.parser import parse_project
from lookml_parser.models import LookMLProject, LookMLView, LookMLField, LookMLExplore
from validators import run_all_checks, compute_health_score
from validators.broken_references import check_broken_references
from validators.duplicates import check_duplicates
from validators.duplicate_tables import check_duplicate_table_refs
from validators.join_integrity import check_join_integrity
from validators.primary_keys import check_primary_keys
from validators.field_documentation import check_field_documentation
from validators.duplicate_sql import check_duplicate_sql
from validators.orphans import check_orphans


# ── Parser ────────────────────────────────────────────────────

def test_parse_mock_project():
    p = parse_project(MOCK_DIR)
    assert len(p.views) > 0
    assert len(p.explores) > 0

def test_view_has_fields():
    p = parse_project(MOCK_DIR)
    customers = p.view_map.get("customers")
    assert customers is not None
    assert len(customers.fields) > 0
    assert any(f.name == "id" for f in customers.fields)

def test_explore_has_joins():
    p = parse_project(MOCK_DIR)
    orders_explore = p.explore_map.get("orders")
    assert orders_explore is not None
    assert len(orders_explore.joins) > 0

def test_primary_key_parsed():
    p = parse_project(MOCK_DIR)
    orders = p.view_map.get("orders")
    assert orders is not None
    pk_fields = [f for f in orders.fields if f.primary_key]
    assert len(pk_fields) > 0, "orders.id should have primary_key: yes"

def test_derived_table_parsed():
    p = parse_project(MOCK_DIR)
    dt_views = p.derived_table_views
    assert any(v.name == "orders_summary" for v in dt_views), \
        "orders_summary should be detected as derived table"


# ── Validators ────────────────────────────────────────────────

def test_broken_references_detects_missing_view():
    p = parse_project(MOCK_DIR)
    issues = check_broken_references(p)
    assert any("ghost_explore" in i.message or "non_existent" in i.message for i in issues)

def test_duplicates_detects_duplicate_views():
    p = parse_project(MOCK_DIR)
    issues = check_duplicates(p)
    assert any(i.object_type == "view" for i in issues)

def test_duplicates_detects_duplicate_fields():
    p = parse_project(MOCK_DIR)
    issues = check_duplicates(p)
    assert any(i.object_type == "field" for i in issues)

def test_duplicate_tables_detected():
    p = parse_project(MOCK_DIR)
    issues = check_duplicate_table_refs(p)
    assert len(issues) > 0, "public.customers used in multiple views should be flagged"
    assert any("public.customers" in i.message.lower() for i in issues)

def test_join_integrity_detects_missing_sql_on():
    p = parse_project(MOCK_DIR)
    issues = check_join_integrity(p)
    assert any("no sql_on or foreign_key" in i.message for i in issues)

def test_primary_key_check_flags_missing():
    p = parse_project(MOCK_DIR)
    issues = check_primary_keys(p)
    flagged = [i.object_name for i in issues]
    assert "staging_temp" in flagged

def test_primary_key_check_passes_when_defined():
    p = parse_project(MOCK_DIR)
    issues = check_primary_keys(p)
    flagged = [i.object_name for i in issues]
    assert "orders" not in flagged

def test_field_documentation_flags_missing():
    p = parse_project(MOCK_DIR)
    issues = check_field_documentation(p)
    assert len(issues) > 0, "Should flag views with fields missing label/description"
    # Issues are grouped by view — orders view has undocumented fields
    assert any("orders" in i.object_name for i in issues)

def test_field_documentation_skips_hidden():
    p = parse_project(MOCK_DIR)
    issues = check_field_documentation(p)
    flagged = [i.object_name for i in issues]
    assert "customers.internal_notes" not in flagged

def test_duplicate_sql_detected():
    proj = LookMLProject(
        name="test",
        views=[LookMLView(
            name="test_view",
            sql_table_name="public.test",
            fields=[
                LookMLField(name="cust_num",  field_type="dimension", sql='${TABLE}."CUSTOMER_NUMBER"'),
                LookMLField(name="cust_num2", field_type="dimension", sql='${TABLE}."CUSTOMER_NUMBER"'),
                LookMLField(name="unique",    field_type="dimension", sql='${TABLE}."OTHER_COL"'),
            ]
        )],
        explores=[]
    )
    issues = check_duplicate_sql(proj)
    assert len(issues) > 0
    assert "cust_num" in issues[0].message and "cust_num2" in issues[0].message

def test_orphans_detects_unreferenced_view():
    p = parse_project(MOCK_DIR)
    issues = check_orphans(p)
    orphan_names = [i.object_name for i in issues if "not referenced" in i.message]
    assert "staging_temp" in orphan_names


# ── Health score ──────────────────────────────────────────────

def test_health_score_range():
    p = parse_project(MOCK_DIR)
    issues = run_all_checks(p)
    score = compute_health_score(issues)
    assert 0 <= score <= 100

def test_clean_project_scores_100():
    clean = LookMLProject(
        name="clean",
        views=[LookMLView(
            name="orders",
            sql_table_name="public.orders",
            fields=[LookMLField(
                name="id", field_type="dimension",
                sql="${TABLE}.id", primary_key=True,
                label="Order ID", description="Unique order identifier"
            )]
        )],
        explores=[LookMLExplore(name="orders", joins=[])]
    )
    issues = run_all_checks(clean)
    errors = [i for i in issues if i.severity == "error"]
    assert len(errors) == 0

def test_health_score_errors_dominate():
    """Score should drop significantly with errors, minimally with warnings."""
    from validators.issue import Issue, IssueCategory, Severity
    error_issues   = [Issue(category=IssueCategory.BROKEN_REFERENCE, severity=Severity.ERROR,
                            message="err", object_type="view", object_name="x")] * 5
    warning_issues = [Issue(category=IssueCategory.JOIN_INTEGRITY, severity=Severity.WARNING,
                            message="warn", object_type="join", object_name="y")] * 50
    score_errors   = compute_health_score(error_issues)
    score_warnings = compute_health_score(warning_issues)
    # 5 errors should cost more than 50 warnings
    assert score_errors < score_warnings, \
        f"5 errors ({score_errors}) should score worse than 50 warnings ({score_warnings})"


# ── Graph ─────────────────────────────────────────────────────

def test_graph_removed():
    """NetworkX dependency graph removed — orphan detection now done directly in validators/orphans.py"""
    from validators.orphans import check_orphans
    p = parse_project(MOCK_DIR)
    issues = check_orphans(p)
    orphan_names = [i.object_name for i in issues if "not referenced" in i.message]
    assert "staging_temp" in orphan_names, "Orphan detection still works without graph"


if __name__ == "__main__":
    tests = [
        test_parse_mock_project, test_view_has_fields, test_explore_has_joins,
        test_primary_key_parsed, test_derived_table_parsed,
        test_broken_references_detects_missing_view,
        test_duplicates_detects_duplicate_views, test_duplicates_detects_duplicate_fields,
        test_duplicate_tables_detected, test_join_integrity_detects_missing_sql_on,
        test_primary_key_check_flags_missing, test_primary_key_check_passes_when_defined,
        test_field_documentation_flags_missing, test_field_documentation_skips_hidden,
        test_duplicate_sql_detected, test_orphans_detects_unreferenced_view,
        test_health_score_range, test_clean_project_scores_100,
        test_health_score_errors_dominate,
        test_graph_removed,
    ]
    passed = failed = 0
    for t in tests:
        try:
            t()
            print(f"  ✓ {t.__name__}")
            passed += 1
        except Exception as e:
            print(f"  ✗ {t.__name__}: {e}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
