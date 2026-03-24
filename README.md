# ⬡ LookML Auditor

Static analysis and health scoring for LookML projects.
Detects broken references, duplicate definitions, unused objects, and join integrity issues.

---

## Setup

```bash
cd lookml_auditor
pip install -r requirements.txt
```

---

## Usage

### Streamlit Dashboard (recommended)
```bash
streamlit run dashboard.py
```
Then set your LookML project path in the sidebar and click **▶ Run Audit**.

### CLI
```bash
# Audit with rich terminal output
python main.py audit /path/to/your/lookml/project

# Audit + export JSON report
python main.py audit /path/to/your/lookml/project --json-out report.json

# Run against mock data
python main.py audit ./mock_project
```

### Run tests
```bash
python tests/test_auditor.py
# or with pytest
pip install pytest && pytest tests/ -v
```

---

## Project Structure

```
lookml_auditor/
├── parser/
│   ├── models.py            # Pydantic data models (View, Explore, Field, Join)
│   └── parser.py            # Regex-based .lkml file parser
├── graph/
│   └── dependency_graph.py  # networkx graph builder & query helpers
├── validators/
│   ├── issue.py             # Issue model (severity, category)
│   ├── broken_references.py # Explores/joins pointing to missing views
│   ├── duplicates.py        # Duplicate views and fields
│   ├── unused_objects.py    # Orphan views and unreferenced fields
│   ├── join_integrity.py    # Missing sql_on, bad field refs, missing relationship
│   └── __init__.py          # Runner + health score formula
├── reporting/
│   └── json_reporter.py     # JSON report builder
├── mock_project/            # Sample LookML with intentional issues
│   ├── views/
│   └── explores/
├── tests/
│   └── test_auditor.py      # Unit tests
├── dashboard.py             # Streamlit UI
├── main.py                  # CLI entry point
└── requirements.txt
```

---

## Checks Implemented

| Check | Severity | Description |
|-------|----------|-------------|
| Missing base view | ERROR | Explore references a view that doesn't exist |
| Missing join view | ERROR | Join references a view that doesn't exist |
| Bad field ref in sql_on | ERROR/WARNING | sql_on references undefined view or field |
| Duplicate view name | ERROR | Same view name defined in multiple files |
| Duplicate explore name | ERROR | Same explore defined multiple times |
| Duplicate field in view | ERROR | Same field name appears twice in one view |
| Missing sql_on / foreign_key | ERROR | Join has no condition defined |
| Missing relationship | WARNING | Join missing relationship type |
| Unused view | WARNING | View not referenced by any explore |
| Unused field | INFO | Field not referenced in any SQL expression |

---

## Health Score Formula

```
score = 100
       - min(errors   × 10, 60)
       - min(warnings ×  3, 20)
       - min(info     ×  1, 10)
```

| Score | Status |
|-------|--------|
| 85–100 | ✅ Healthy |
| 60–84  | ⚠️ Needs Attention |
| 0–59   | 🔴 Critical |

---

## Adding Your LookML Project

Replace `mock_project/` path with your local folder:
```bash
python main.py audit /Users/you/your-looker-repo
```
or set it in the Streamlit sidebar.

---

## Extending with New Checks

1. Create `validators/my_check.py` with a function `check_my_rule(project) -> list[Issue]`
2. Import and add it to `ALL_CHECKS` in `validators/__init__.py`

That's it — it will automatically appear in the dashboard and CLI output.
