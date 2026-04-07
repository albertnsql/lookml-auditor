# 🔍 LookML Auditor

**LookML Auditor** is a static analysis tool built to catch LookML issues that are easy to miss in code review — missing descriptions, orphaned views, joins without a relationship defined, explores with broken references, and more. 

Originally built out of frustration with how much bad LookML slips through to production, this tool parses `.lkml` files using a **hyper-optimized custom parser** (C-level string operations). Because it's aware of LookML block scope and syntax, it correctly handles `;;`-terminated SQL, extends, nested derived tables, and dimension groups.

---

## 🛠 What's Included (Current State)

We recently overhauled the auditor for extreme performance and accuracy. Here is what is actively operating in the application today:

* **⚡ Ultra-Fast Custom Parsing Engine**: Migrated away from recursive Python loops in favor of native C-speed block evaluations (`str.find()`) to parse massive `*.view.lkml` files instantly.
* **🌳 Interactive Dependency Trees**: Automatically visualizes `Explore → View` joins in a comprehensive top-to-bottom layout mapping Many-to-One and One-to-Many nodes.
* **🧠 SQL Derived Table Analysis**: Employs cached AST-like heuristics to read raw `derived_table_sql`, catching `SELECT *`, missing `WHERE` clauses, and alerting developers when they can simplify native tables.
* **📊 Dashboard & Metrics**: Runs locally on a dynamic **Streamlit** dashboard. Includes a 0–100 Health Score calculation and breakdown of errors by Category and Severity.
* **📥 CSV Export**: Clean, one-click export of data issues to pipe into sprint planning.
* **🛡️ Robust Stability**: Fixed parsing crashes by heavily coercing mixed dataframe types, meaning large complex repos load flawlessly.

---

## 🚀 How to Use

### Local Setup (Developer Mode)
Run the auditor locally on your machine for the best performance.

**Prerequisites**:
* Python 3.8+
* Streamlit, Plotly, Rich, Pydantic

**Installation**:
```bash
# Clone the repository
git clone https://github.com/albertnsql/lookml-auditor
cd lookml-auditor

# Install dependencies
pip install -r requirements.txt

# Launch the dashboard
streamlit run dashboard.py
```

---

## 🏗 Understanding the Audit

The Auditor categorizes findings into four key pillars:

| Category | Description |
| :--- | :--- |
| **Broken Reference** | Explores or joins pointing to missing views or fields. |
| **Duplicate Definition** | The same view, explore, or field defined in multiple places. |
| **Join Integrity** | Missing `sql_on`, bad field references, or inconsistent relationships. |
| **Field Quality** | Missing primary keys, orphaned views, and unlabeled fields. |

### Health Score Status
* ⭐ **85–100**: Healthy
* ⚠️ **60–84**: Needs Attention
* 🔴 **0–59**: Critical Integrity Issues

---

## 📂 Project Structure

```bash
lookml-auditor/
├── dashboard.py         # Main Streamlit UI & logic (Cached and Optimized)
├── lookml_parser/       # Hyper-optimized LookML engine
├── validators/          # The audit rules & scoring validations
├── reporting/           # Export engines and formatting
├── tests/               # 20/20 Passing Automated test suite
└── mock_project/        # Sample LookML with seeded errors for testing
```

---

## 🤝 Contributing

Have a new audit rule in mind? 
1. Create a new validator in `validators/`.
2. Add it to the `ALL_CHECKS` list in `validators/__init__.py`.
3. Submit a Pull Request!
