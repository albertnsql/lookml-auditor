"""
Suppression Rules — lookml_auditor.yaml
========================================
Allows teams to silence known false positives without touching validator code.

Example lookml_auditor.yaml (place in project root):

  suppress:
    # Suppress all join_integrity checks for legacy explores
    - check: join_integrity
      pattern: "np_legacy_*"

    # Suppress duplicate warnings on a specific view
    - check: duplicate
      pattern: "orderlines"

    # Suppress all checks for a specific file
    - file: "NP_Business_Analysis.model.lkml"
      check: "*"

    # Suppress a specific object by exact name
    - object: "np_sas_pnlsummary.custom_dimesnion_sos"
      check: join_integrity

  # Also works: suppress entire check categories globally
  suppress_checks:
    - field_documentation   # too noisy for now
"""
from __future__ import annotations
import re
from pathlib import Path
from validators.issue import Issue, IssueCategory


# Map friendly names → IssueCategory values
_CATEGORY_ALIASES = {
    "broken_reference":   IssueCategory.BROKEN_REFERENCE,
    "broken":             IssueCategory.BROKEN_REFERENCE,
    "duplicate":          IssueCategory.DUPLICATE,
    "duplicate_definition": IssueCategory.DUPLICATE,
    "join_integrity":     IssueCategory.JOIN_INTEGRITY,
    "join":               IssueCategory.JOIN_INTEGRITY,
    "field_quality":      IssueCategory.FIELD_QUALITY,
    "field_documentation": IssueCategory.FIELD_QUALITY,
    "quality":            IssueCategory.FIELD_QUALITY,
}


def _glob_match(pattern: str, text: str) -> bool:
    """Simple glob: supports * and ? wildcards, case-insensitive."""
    if pattern == "*":
        return True
    regex = re.escape(pattern).replace(r"\*", ".*").replace(r"\?", ".")
    return bool(re.fullmatch(regex, text, re.IGNORECASE))


def load_suppression_rules(project_root: str) -> dict:
    """
    Load lookml_auditor.yaml from project_root.
    Returns parsed rules dict, or empty dict if file not found.
    """
    config_path = Path(project_root) / "lookml_auditor.yaml"
    if not config_path.exists():
        return {}
    try:
        import yaml  # type: ignore
        with open(config_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        # yaml.safe_load returns None for empty files — guard against it
        return data if isinstance(data, dict) else {}
    except ImportError:
        # yaml not installed — try minimal parser
        return _minimal_yaml_parse(config_path)
    except Exception:
        return {}


def _minimal_yaml_parse(path: Path) -> dict:
    """Very basic YAML parser for simple suppress_checks lists (no PyYAML needed)."""
    rules: dict = {"suppress_checks": [], "suppress": []}
    try:
        text = path.read_text(encoding="utf-8")
        for line in text.splitlines():
            line = line.strip()
            if line.startswith("- ") and ":" not in line:
                # bare list item under suppress_checks
                rules["suppress_checks"].append(line[2:].strip())
    except Exception:
        pass
    return rules


def apply_suppressions(issues: list[Issue], rules: dict,
                       project_root: str = "") -> list[Issue]:
    """
    Filter out issues that match any suppression rule.
    Returns the surviving issues.
    """
    if not rules or not isinstance(rules, dict):
        return issues, 0

    # Global category suppressions
    suppressed_cats: set[IssueCategory] = set()
    for name in (rules.get("suppress_checks") or []):
        cat = _CATEGORY_ALIASES.get(name.lower().strip())
        if cat:
            suppressed_cats.add(cat)

    # Per-object/file/pattern rules
    per_rules = rules.get("suppress") or []

    def _is_suppressed(issue: Issue) -> bool:
        # Global check suppression
        if issue.category in suppressed_cats:
            return True

        # Per-rule matching
        for rule in per_rules:
            check_name = rule.get("check", "*").lower()
            # Resolve check to category
            if check_name != "*":
                rule_cat = _CATEGORY_ALIASES.get(check_name)
                if rule_cat and rule_cat != issue.category:
                    continue  # This rule targets a different category

            # Match by object name pattern
            if "pattern" in rule:
                if _glob_match(rule["pattern"], issue.object_name):
                    return True

            # Match by exact object name
            if "object" in rule:
                if rule["object"].lower() == issue.object_name.lower():
                    return True

            # Match by filename
            if "file" in rule:
                issue_filename = Path(issue.source_file).name if issue.source_file else ""
                if _glob_match(rule["file"], issue_filename):
                    return True

        return False

    kept      = [i for i in issues if not _is_suppressed(i)]
    suppressed = len(issues) - len(kept)
    return kept, suppressed


# Example config template — written to project root if not present
EXAMPLE_CONFIG = """\
# LookML Auditor — Suppression Rules
# Place this file in your LookML project root.
# Docs: https://github.com/your-org/lookml-auditor

suppress:
  # Suppress join_integrity for a specific explore or join
  # - check: join_integrity
  #   object: "np_sas_pnlsummary.custom_dimesnion_sos"

  # Suppress all checks for legacy files
  # - file: "legacy_*.model.lkml"
  #   check: "*"

  # Suppress duplicate warnings for views that intentionally share names
  # - check: duplicate
  #   pattern: "orderlines"

# Suppress entire check categories globally
suppress_checks:
  # - field_documentation   # uncomment to ignore all label/description issues
  # - join_integrity        # uncomment to ignore all join issues
"""
