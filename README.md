# 🔍 LookML Auditor

**LookML Auditor** is a powerful, privacy-first static analysis tool for Looker projects. It helps developers maintain high-quality code by detecting broken references, duplicate definitions, and join integrity issues—all in one beautiful dashboard.

---

## 🚀 How to Use

### 1. Cloud-Hosted (Streamlit Community Cloud)
The easiest way to use the auditor without any installation.
*   **Access**: [lookml-auditor.streamlit.app](https://lookml-auditor.streamlit.app)
*   **GitHub URL**: Paste any public LookML repository URL to audit it instantly.
*   **ZIP Upload**: Upload a folder of your LookML project in `.zip` format. Perfect for private repos.

### 2. Local Setup (Developer Mode)
Run the auditor locally on your machine for the best performance and "Local Folder" access.

**Prerequisites**:
*   Python 3.8+
*   Git (optional, for GitHub source)

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

## 🛠 Features & Capabilities

*   **⚡ Instant Health Score**: A proprietary 0–100 score based on repo size and issue density.
*   **🐙 GitHub Integration**: Audit any public repository by simply pasting its URL.
*   **🤐 ZIP Upload Support**: Securely audit local projects in the cloud via ZIP extraction.
*   **📂 Local Folder Audit**: Points directly to your local development directory (Desktop only).
*   **📊 Dynamic Visualizations**: Interactive graphs and charts powered by Plotly.
*   **📥 CSV Export**: Download a full list of issues and suggestions for easy tracking.
*   **🔒 Privacy-First**: 100% in-memory analysis. Your code never leaves the session.

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
*   ⭐ **85–100**: Healthy
*   ⚠️ **60–84**: Needs Attention
*   🔴 **0–59**: Critical Integrity Issues

---

## 📂 Project Structure

```bash
lookml-auditor/
├── dashboard.py         # Main Streamlit UI & logic
├── lookml_parser/       # Regex-based LookML engine
├── validators/          # The audit rules & scoring engine
├── reporting/           # CSV and JSON report generators
├── tests/               # Automated test suite
└── mock_project/        # Sample LookML for demo purposes
```

---

## 🤝 Contributing

Have a new audit rule in mind? 
1. Create a new validator in `validators/`.
2. Add it to the `ALL_CHECKS` list in `validators/__init__.py`.
3. Submit a Pull Request!
