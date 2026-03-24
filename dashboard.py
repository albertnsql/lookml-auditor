"""
LookML Auditor — Dashboard
===========================
Based on user's preferred UI format with all fixes applied:

Case 1: Case-insensitive view/explore name comparison (already in validators)
Case 2: Duplicate explore across model files → WARNING not ERROR (in validators)
Case 3: Duplicate SQL → dimension/measure type labels, value_format hint (in validators)
Case 4: Primary key sharing SQL → INFO not WARNING (in validators)
Case 5: Derived Tables collapse to accordion — Add 'Jump to Explores' anchor button
Case 6: UI lag fixed — st.cache_data on heavy compute, lazy KPI detail, minimal rerender
"""
from __future__ import annotations
import sys, os, json
from collections import Counter
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
import plotly.graph_objects as go
import pandas as pd

from lookml_parser import parse_project
from validators import run_all_checks, compute_health_score, compute_category_scores, Severity, IssueCategory
from validators.suppression import load_suppression_rules, apply_suppressions, EXAMPLE_CONFIG
from reporting import build_json_report


# ─────────────────────────────────────────────────────────────
st.set_page_config(page_title="LookML Auditor", page_icon="🔍",
                   layout="wide", initial_sidebar_state="expanded")
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');
  html,body,[class*="css"]{font-family:'Inter',sans-serif;}
  .stApp{background:#141B2D;color:#E2E8F0;}
  section[data-testid="stSidebar"]{background:#0F1628!important;border-right:1px solid #1E2D4A;}
  div[data-testid="metric-container"]{background:#1A2438;border:1px solid #1E2D4A;border-radius:12px;padding:14px;cursor:default;box-shadow:0 2px 8px rgba(0,0,0,0.3);}
  div[data-testid="metric-container"] label{color:#7B8FAE!important;font-size:10px!important;letter-spacing:.1em;text-transform:uppercase;font-family:'Inter',sans-serif!important;}
  div[data-testid="metric-container"] div[data-testid="stMetricValue"]{font-family:'JetBrains Mono',monospace!important;font-size:22px!important;font-weight:700;color:#E2E8F0!important;}
  .section-header{font-family:'Inter',sans-serif;font-size:10px;font-weight:700;letter-spacing:.18em;text-transform:uppercase;color:#4A9EFF;border-bottom:1px solid #1E2D4A;padding-bottom:8px;margin:20px 0 14px 0;}
  .stTabs [data-baseweb="tab-list"]{background:#0F1628;border-bottom:1px solid #1E2D4A;}
  .stTabs [data-baseweb="tab"]{font-family:'Inter',sans-serif;font-size:12px;font-weight:500;color:#7B8FAE;padding:12px 20px;letter-spacing:.02em;}
  .stTabs [aria-selected="true"]{color:#4A9EFF!important;border-bottom:2px solid #4A9EFF;}
  .stTextInput input{background:#1A2438!important;border:1px solid #1E2D4A!important;color:#E2E8F0!important;font-family:'JetBrains Mono',monospace;border-radius:8px;}
  .stButton button{background:linear-gradient(135deg,#4A9EFF,#4A9EFF)!important;color:#1A2438!important;font-family:'Inter',sans-serif;font-weight:600;font-size:12px;border:none;border-radius:8px;letter-spacing:.02em;}
  .stButton button:hover{background:linear-gradient(135deg,#2563EB,#4A9EFF)!important;box-shadow:0 4px 14px rgba(74,158,255,0.35);}
  div[data-testid="stExpander"]{border:1px solid #1E2D4A;border-radius:10px;background:#1A2438;}
  .filter-bar{background:#1A2438;border:1px solid #1E2D4A;border-radius:12px;padding:14px 20px;margin-bottom:18px;box-shadow:0 2px 8px rgba(0,0,0,0.2);}
  .kpi-detail{background:#0F1628;border:1px solid #1E2D4A;border-radius:8px;padding:12px 16px;margin-top:6px;font-family:'JetBrains Mono',monospace;font-size:11px;color:#7B8FAE;max-height:200px;overflow-y:auto;line-height:1.8;}
  .jump-link a{font-family:'Inter',sans-serif;font-size:11px;color:#4A9EFF;text-decoration:none;}
  hr{border-color:#1E2D4A!important;}
  header[data-testid="stHeader"] {background: transparent !important;}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# Chart helpers
# ─────────────────────────────────────────────────────────────
def score_meta(s):
    if s >= 85: return "#22c55e", "Healthy"
    if s >= 60: return "#fbbf24", "Needs Attention"
    return "#ef4444", "Critical"

def _norm(p: str) -> str:
    return str(Path(p)).lower().replace("\\", "/")

def make_gauge(score):
    color, label = score_meta(score)
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=score,
        number={"font": {"size": 44, "color": color, "family": "JetBrains Mono"}},
        gauge={
            "axis": {"range": [0, 100], "tickfont": {"color": "#7B8FAE", "size": 10}},
            "bar": {"color": color, "thickness": 0.28},
            "bgcolor": "#1A2438", "bordercolor": "#1E2D4A", "borderwidth": 1,
            "steps": [{"range": [0, 60], "color": "#0F1628"},
                      {"range": [60, 85], "color": "#0F1628"},
                      {"range": [85, 100], "color": "#1A2D1A"}],
        },
        title={"text": f"<b>{label}</b>",
               "font": {"color": "#7B8FAE", "size": 12, "family": "Inter"}},
    ))
    fig.update_layout(height=250, margin=dict(l=20, r=20, t=36, b=8),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    return fig

def make_cat_bar(issues):
    c = Counter(i.category for i in issues)
    if not c: return go.Figure()
    labels = [x.value for x in c]; values = list(c.values())
    colors = ["#4A9EFF", "#F59E0B", "#F472B6", "#10B981", "#818CF8"]
    fig = go.Figure(go.Bar(x=values, y=labels, orientation="h",
                           marker_color=colors[:len(labels)], text=values,
                           textposition="outside",
                           textfont={"color": "#7B8FAE", "size": 11, "family": "JetBrains Mono"}))
    fig.update_layout(height=220, margin=dict(l=10, r=40, t=10, b=10),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      xaxis={"gridcolor": "#1E2D4A", "color": "#7B8FAE",
                             "tickfont": {"family": "JetBrains Mono", "size": 10}},
                      yaxis={"color": "#7B8FAE", "tickfont": {"family": "Inter", "size": 11}},
                      showlegend=False)
    return fig

def make_donut(issues):
    c = Counter(i.severity for i in issues)
    if not c: return go.Figure()
    lm = {"error": "Error", "warning": "Warning", "info": "Info"}
    cm = {"error": "#EF4444", "warning": "#F59E0B", "info": "#4A9EFF"}
    keys = list(c)
    fig = go.Figure(go.Pie(labels=[lm.get(k, k) for k in keys],
                           values=[c[k] for k in keys], hole=0.65,
                           marker_colors=[cm.get(k, "#888") for k in keys],
                           textfont={"family": "JetBrains Mono", "size": 11},
                           textinfo="label+value"))
    fig.update_layout(height=220, margin=dict(l=10, r=10, t=10, b=10),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      showlegend=False)
    return fig

def _badge(count, label, bg, fg, border):
    if not count: return ""
    return (f'<span style="background:{bg};color:{fg};border:1px solid {border};'
            f'border-radius:4px;padding:2px 8px;font-size:11px;'
            f'font-family:JetBrains Mono,monospace;font-weight:600;">{count} {label}</span>')

def _card(title, total, errors, warnings, infos):
    badges = (
        _badge(errors,   "err",  "#2D1A1A", "#DC2626", "#FECACA") +
        _badge(warnings, "warn", "#2D2A1A", "#D97706", "#FDE68A") +
        _badge(infos,    "info", "#102030", "#4A9EFF", "#1A3A5C")
    )
    clean = '<span style="color:#22C55E;font-size:11px;font-family:Inter,sans-serif;">✓ clean</span>'
    return (f'<div style="background:#1A2438;border:1px solid #1E2D4A;border-radius:10px;padding:16px;">'
            f'<div style="font-family:JetBrains Mono,monospace;font-size:10px;color:#7B8FAE;letter-spacing:.1em;'
            f'text-transform:uppercase;margin-bottom:10px;">{title}</div>'
            f'<div style="font-family:JetBrains Mono,monospace;font-size:26px;font-weight:700;color:#E2E8F0;">{total}</div>'
            f'<div style="margin-top:10px;display:flex;gap:6px;flex-wrap:wrap;">'
            f'{badges if (errors or warnings or infos) else clean}</div></div>')

def _kpi_with_detail(col, label, value, detail_items, color="#e2e8f0", help_text=""):
    """Metric tile only — no expander, detail available via help tooltip."""
    col.metric(label, f"{value:,}" if isinstance(value, int) else value,
               help=help_text or None)


# ─────────────────────────────────────────────────────────────
# Cached parse — defined early so sidebar Clear button can call it
# ─────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def _parse_only(path: str):
    """Cache only the parsing step. Validators always re-run fresh."""
    return parse_project(path)


# ─────────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        "<div style='padding:12px 0 20px;border-bottom:1px solid #1E2D4A;margin-bottom:16px;'>"
        "<div style='font-family:JetBrains Mono,monospace;font-size:11px;font-weight:600;letter-spacing:.2em;text-transform:uppercase;color:#4A9EFF;margin-bottom:4px;'>LookML</div>"
        "<div style='font-family:Inter,sans-serif;font-size:20px;font-weight:700;color:#E2E8F0;letter-spacing:-.3px;'>Auditor</div>"
        "</div>", unsafe_allow_html=True)
    st.markdown('<div class="section-header">Project Path</div>', unsafe_allow_html=True)
    default_path = str(Path(__file__).parent / "looker-repo")
    project_path = st.text_input("path", value=default_path,
                                  label_visibility="collapsed",
                                  placeholder="/path/to/lookml/project")
    run_btn = st.button("▶  Run Audit", use_container_width=True)
    st.markdown('<div class="section-header">Severity Filter</div>', unsafe_allow_html=True)
    show_e = st.checkbox("Errors",   value=True)
    show_w = st.checkbox("Warnings", value=True)
    show_i = st.checkbox("Info",     value=True)
    severity_filter = (
        (["error"]   if show_e else []) +
        (["warning"] if show_w else []) +
        (["info"]    if show_i else [])
    )
    st.markdown('<div class="section-header">Export</div>', unsafe_allow_html=True)
    export_json = st.button("⬇  Export JSON", use_container_width=True)
    st.markdown('<div class="section-header">Cache</div>', unsafe_allow_html=True)
    if st.button("🗑  Clear & Re-parse", use_container_width=True, help="Clears the parse cache and re-runs from scratch. Use after updating the repo."):
        st.cache_data.clear()   # clears all @st.cache_data caches safely
        st.session_state.audit_result = None
        st.rerun()
    _ar = st.session_state.get("audit_result")  # safe — works before initialisation
    if _ar:
        _sup = _ar.get("suppressed", 0)
        _man = _ar.get("manifest", {})
        if _sup:
            st.markdown(f"<div style='font-family:JetBrains Mono,monospace;font-size:11px;color:#fbbf24;"
                        f"margin-top:8px;'>⚡ {_sup} issues suppressed by rules</div>",
                        unsafe_allow_html=True)
        if _man:
            st.markdown(f"<div style='font-family:JetBrains Mono,monospace;font-size:11px;color:#34d399;"
                        f"margin-top:4px;'>✓ {len(_man)} manifest constants loaded</div>",
                        unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# Session state
# ─────────────────────────────────────────────────────────────
if "audit_result" not in st.session_state:
    st.session_state.audit_result = None

# Reset flag pattern (avoids Streamlit widget-state error on direct key assignment)
if st.session_state.pop("_do_reset", False):
    st.session_state["_reset_fold"] = True
    st.session_state["_reset_exp"]  = True

if run_btn:
    with st.spinner("Parsing & analysing — may take a moment for large repos..."):
        try:
            _p = _parse_only(project_path)
            _i = run_all_checks(_p)
            _rules = load_suppression_rules(_p.root_path)
            _i, _suppressed = apply_suppressions(_i, _rules, _p.root_path)
            _g = None  # graph removed — not used
            _r = build_json_report(_p, _i)
            st.session_state.audit_result = {"project": _p, "issues": _i,
                                              "graph": _g, "report": _r,
                                              "suppressed": _suppressed,
                                              "manifest": _p.manifest_constants}
            st.rerun()
        except Exception as e:
            st.error(f"❌ {e}")
            import traceback; st.code(traceback.format_exc())


# ─────────────────────────────────────────────────────────────
# Landing
# ─────────────────────────────────────────────────────────────
if st.session_state.audit_result is None:
    st.markdown(
        "<div style='text-align:center;padding:48px 0 32px;'>"
        "<div style='font-family:JetBrains Mono,monospace;font-size:52px;color:#4A9EFF;margin-bottom:8px;'>⬡</div>"
        "<h1 style='font-size:30px;margin-bottom:10px;color:#E2E8F0;'>LookML Auditor</h1>"
        "<p style='color:#7B8FAE;font-size:14px;max-width:460px;margin:0 auto;line-height:1.7;'>"
        "Static analysis for your LookML project.<br>"
        "Detect broken references, duplicates, join issues, and field quality problems."
        "</p></div>", unsafe_allow_html=True)
    _, cc, _ = st.columns([1, 2, 1])
    with cc:
        lp = st.text_input("p", value=default_path, label_visibility="collapsed",
                            placeholder="C:\\Users\\you\\your-looker-repo", key="landing_path")
        lr = st.button("▶  Run Audit", use_container_width=True, key="landing_run")
        st.markdown(
            "<div style='margin-top:12px;font-family:JetBrains Mono,monospace;font-size:11px;"
            "color:#94A3B8;text-align:center;'>Paste the full path to your local LookML repo folder above</div>",
            unsafe_allow_html=True)
    if lr:
        with st.spinner("Parsing & analysing — may take a moment for large repos..."):
            try:
                _p = _parse_only(lp)
                _i = run_all_checks(_p)
                _rules = load_suppression_rules(_p.root_path)
                _i, _suppressed = apply_suppressions(_i, _rules, _p.root_path)
                _g = None  # graph removed — not used
                _r = build_json_report(_p, _i)
                st.session_state.audit_result = {"project": _p, "issues": _i,
                                                  "graph": _g, "report": _r,
                                                  "suppressed": _suppressed,
                                                  "manifest": _p.manifest_constants}
                st.rerun()
            except Exception as e:
                st.error(f"❌ {e}")
                import traceback; st.code(traceback.format_exc())
    st.stop()


# ─────────────────────────────────────────────────────────────
# Unpack
# ─────────────────────────────────────────────────────────────
result     = st.session_state.audit_result
project    = result["project"]
issues     = result["issues"]
report     = result["report"]
suppressed = result.get("suppressed", 0)
manifest   = result.get("manifest", {})

# CSV export — always available once audit has run
import io as _io, csv as _csv
_csv_rows = [{"Severity": i.severity.upper(), "Category": i.category.value,
              "Object": i.object_name, "Type": i.object_type,
              "Message": i.message, "Suggestion": i.suggestion,
              "File": Path(i.source_file).name if i.source_file else "",
              "Line": i.line_number or ""}
             for i in sorted(issues, key=lambda x: (x.severity, x.category.value))]
_buf = _io.StringIO()
if _csv_rows:
    _w = _csv.DictWriter(_buf, fieldnames=list(_csv_rows[0].keys()))
    _w.writeheader(); _w.writerows(_csv_rows)

if export_json:
    st.sidebar.download_button("⬇  Download JSON",
        data=json.dumps(report, indent=2, default=str),
        file_name=f"lookml_audit_{project.name}.json",
        mime="application/json", use_container_width=True)

st.sidebar.download_button("⬇  Download CSV",
    data=_buf.getvalue(),
    file_name=f"lookml_audit_{project.name}.csv",
    mime="text/csv", use_container_width=True)


# ─────────────────────────────────────────────────────────────
# Global Filters
# ─────────────────────────────────────────────────────────────
all_folders       = sorted({Path(v.source_file).parent.name
                             for v in project.views if v.source_file})
all_explore_names = sorted({e.name for e in project.explores})

fold_default = (["All Folders"]  if st.session_state.pop("_reset_fold", False)
                else st.session_state.get("folder_filter",  ["All Folders"]))
exp_default  = (["All Explores"] if st.session_state.pop("_reset_exp",  False)
                else st.session_state.get("explore_filter", ["All Explores"]))

st.markdown('<div class="filter-bar">', unsafe_allow_html=True)
fc1, fc2, fc3 = st.columns([3, 3, 1])
with fc1:
    st.markdown('<span style="font-family:JetBrains Mono,monospace;font-size:11px;color:#7B8FAE;'
                'letter-spacing:.1em;text-transform:uppercase;">Filter by Folder</span>',
                unsafe_allow_html=True)
    sel_folders = st.multiselect("f", options=["All Folders"] + all_folders,
                                  default=fold_default,
                                  label_visibility="collapsed", key="folder_filter")
with fc2:
    st.markdown('<span style="font-family:JetBrains Mono,monospace;font-size:11px;color:#7B8FAE;'
                'letter-spacing:.1em;text-transform:uppercase;">Filter by Explore</span>',
                unsafe_allow_html=True)
    sel_explores = st.multiselect("e", options=["All Explores"] + all_explore_names,
                                   default=exp_default,
                                   label_visibility="collapsed", key="explore_filter")
with fc3:
    st.markdown('<span style="font-family:JetBrains Mono,monospace;font-size:11px;color:#7B8FAE;'
                'letter-spacing:.1em;text-transform:uppercase;">Reset</span>',
                unsafe_allow_html=True)
    if st.button("✕ Reset", use_container_width=True):
        st.session_state["_do_reset"] = True
        st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

folder_active  = "All Folders"  not in sel_folders  and len(sel_folders)  > 0
explore_active = "All Explores" not in sel_explores and len(sel_explores) > 0


# ─────────────────────────────────────────────────────────────
# Apply filters
# ─────────────────────────────────────────────────────────────
filtered_views = [
    v for v in project.views
    if not folder_active or Path(v.source_file).parent.name in sel_folders
]
filtered_explores = [
    e for e in project.explores
    if not explore_active or e.name in sel_explores
]

def _issue_matches(iss) -> bool:
    if folder_active:
        if not iss.source_file or Path(iss.source_file).parent.name not in sel_folders:
            return False
    if explore_active:
        if not any(exp in iss.object_name or exp in iss.message for exp in sel_explores):
            return False
    return True

filtered_issues_all = [i for i in issues if _issue_matches(i)]
filtered_issues     = [i for i in filtered_issues_all if i.severity in severity_filter]

# Health score from filtered issues only
filtered_score = compute_health_score(filtered_issues_all, project)
score_color, score_label = score_meta(filtered_score)


# ─────────────────────────────────────────────────────────────
# Header
# ─────────────────────────────────────────────────────────────
col_t, col_p = st.columns([3, 5])
with col_t:
    fb = ('<span style="margin-left:8px;font-family:JetBrains Mono,monospace;font-size:11px;color:#fbbf24;'
          'background:#2e251018;border:1px solid #4a3a1844;border-radius:4px;padding:3px 8px;">⚡ Filtered</span>'
          if (folder_active or explore_active) else "")
    st.markdown(
        f"<div style='padding:8px 0;'>"
        f"<span style='font-family:JetBrains Mono,monospace;font-size:22px;font-weight:700;color:#e2e8f0;'>"
        f"{project.name}</span>"
        f"<span style='margin-left:12px;font-family:JetBrains Mono,monospace;font-size:11px;"
        f"color:{score_color};background:{score_color}18;border:1px solid {score_color}44;"
        f"border-radius:4px;padding:3px 8px;'>{score_label}</span>{fb}</div>",
        unsafe_allow_html=True)
with col_p:
    st.markdown(
        f"<div style='font-family:JetBrains Mono,monospace;font-size:11px;color:#7B8FAE;margin-top:14px;"
        f"overflow:hidden;text-overflow:ellipsis;white-space:nowrap;'>📁 {project.root_path}</div>",
        unsafe_allow_html=True)
st.markdown("<hr style='border-color:#1E2D4A;margin:8px 0 18px 0;'>", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# KPI pre-compute — cached so it only reruns when inputs change
# ─────────────────────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def _compute_kpis(
    view_names:     tuple,   # tuple of view names (hashable)
    explore_names:  tuple,   # tuple of explore names
    issue_keys:     tuple,   # tuple of (severity, category, object_name) — hashable
    # raw data passed as tuples so Streamlit can hash them
    view_data:      tuple,   # tuple of (name, n_fields, n_dims, n_measures, has_pk, is_dt, source_file)
    explore_data:   tuple,   # tuple of (name, base_view)
    field_data:     tuple,   # tuple of (view_name, field_name, hidden, field_type, label, description)
    all_proj_views: tuple,   # full project view names (for orphan calc)
    all_proj_refs:  tuple,   # all referenced view names across all explores
    all_proj_explores: tuple,# full project explore (name, base_view)
):
    """
    All expensive KPI aggregations in one cached function.
    Only recomputes when the filtered view/explore/issue sets actually change.
    """
    from collections import Counter

    # ── Orphan / zombie (project-wide, not just filtered) ──────
    all_view_set     = set(all_proj_views)
    all_ref_set      = set(all_proj_refs)
    zombie_exp_set   = {name for name, base in all_proj_explores if base not in all_view_set}
    orphan_view_set  = {name for name in all_proj_views if name not in all_ref_set}

    # ── Filtered view aggregations (single pass) ───────────────
    derived_count  = 0
    total_fields   = 0
    dim_count      = 0
    meas_count     = 0
    no_pk_views    = []
    no_label_items = []
    no_desc_items  = []
    multi_files    = Counter()
    orphan_in_filter  = []
    zombie_in_filter  = []

    for name, n_fields, n_dims, n_meas, has_pk, is_dt, src in view_data:
        total_fields += n_fields
        dim_count    += n_dims
        meas_count   += n_meas
        if is_dt:   derived_count += 1
        if not has_pk: no_pk_views.append(name)
        if name in orphan_view_set: orphan_in_filter.append(name)
        fname = src.replace("\\", "/").split("/")[-1] if src else ""
        if fname: multi_files[fname] += 1

    for exp_name in explore_names:
        if exp_name in zombie_exp_set:
            zombie_in_filter.append(exp_name)

    multi_view_files = sum(1 for c in multi_files.values() if c > 1)
    total_view_files = len(multi_files)

    # ── Field doc (single pass over pre-extracted field tuples) ─
    for v_name, f_name, hidden, ftype, label, desc in field_data:
        if hidden or ftype not in ("dimension", "dimension_group", "measure"):
            continue
        if not label: no_label_items.append(f"{v_name}.{f_name}")
        if not desc:  no_desc_items.append(f"{v_name}.{f_name}")

    # ── Issue aggregations ─────────────────────────────────────
    error_issues_list   = [(sev, cat, obj) for sev, cat, obj in issue_keys if sev == "error"]
    warning_issues_list = [(sev, cat, obj) for sev, cat, obj in issue_keys if sev == "warning"]
    error_objects   = sorted({obj for _, _, obj in error_issues_list})
    warning_objects = sorted({obj for _, _, obj in warning_issues_list})
    all_issue_objs  = sorted({obj for _, _, obj in issue_keys})

    return {
        "orphan_view_set":   orphan_view_set,
        "zombie_exp_set":    zombie_exp_set,
        "orphan_in_filter":  sorted(orphan_in_filter),
        "zombie_in_filter":  sorted(zombie_in_filter),
        "derived_count":     derived_count,
        "total_fields":      total_fields,
        "dim_count":         dim_count,
        "meas_count":        meas_count,
        "no_pk_views":       no_pk_views,
        "no_label_items":    no_label_items,
        "no_desc_items":     no_desc_items,
        "multi_view_files":  multi_view_files,
        "total_view_files":  total_view_files,
        "error_objects":     error_objects,
        "warning_objects":   warning_objects,
        "all_issue_objs":    all_issue_objs,
        "n_errors":          len(error_issues_list),
        "n_warnings":        len(warning_issues_list),
    }


# Build hashable inputs from filtered data (cheap operations)
_view_data   = tuple(
    (v.name, len(v.fields), len(v.dimensions), len(v.measures),
     v.has_primary_key, v.is_derived_table, v.source_file or "")
    for v in filtered_views
)
_explore_data = tuple((e.name, e.base_view) for e in filtered_explores)
_field_data   = tuple(
    (v.name, f.name, f.hidden, f.field_type, f.label or "", f.description or "")
    for v in filtered_views for f in v.fields
)
_issue_keys   = tuple(
    (i.severity, i.category.value, i.object_name)
    for i in filtered_issues_all
)
# Project-wide refs (for orphan/zombie — always uses full project)
_all_proj_refs = tuple(
    vname
    for e in project.explores
    for vname in ([e.base_view] + [j.resolved_view for j in e.joins])
)

_kpis = _compute_kpis(
    view_names     = tuple(v.name for v in filtered_views),
    explore_names  = tuple(e.name for e in filtered_explores),
    issue_keys     = _issue_keys,
    view_data      = _view_data,
    explore_data   = _explore_data,
    field_data     = _field_data,
    all_proj_views = tuple(v.name for v in project.views),
    all_proj_refs  = _all_proj_refs,
    all_proj_explores = tuple((e.name, e.base_view) for e in project.explores),
)

# Unpack for use throughout the dashboard
orphan_view_names    = _kpis["orphan_view_set"]
zombie_explore_names = _kpis["zombie_exp_set"]
orphan_in_filter     = _kpis["orphan_in_filter"]
zombie_in_filter     = _kpis["zombie_in_filter"]
orphan_view_count    = len(orphan_in_filter)
zombie_exp_count     = len(zombie_in_filter)
derived_count        = _kpis["derived_count"]
total_fields         = _kpis["total_fields"]
dim_count            = _kpis["dim_count"]
meas_count           = _kpis["meas_count"]
no_pk_views          = _kpis["no_pk_views"]
no_label_items       = _kpis["no_label_items"]
no_desc_items        = _kpis["no_desc_items"]
multi_view_files     = _kpis["multi_view_files"]
total_view_files     = _kpis["total_view_files"]
error_objects        = _kpis["error_objects"]
warning_objects      = _kpis["warning_objects"]
all_issue_objs       = _kpis["all_issue_objs"]

# Rebuild issue lists for chart/score use (these are cheap — just filtering a list)
error_issues   = [i for i in filtered_issues_all if i.severity == "error"]
warning_issues = [i for i in filtered_issues_all if i.severity == "warning"]


# ─────────────────────────────────────────────────────────────
# KPI — 2 rows (7 metrics per row)
# ─────────────────────────────────────────────────────────────

# Row 1 — High-Level Health & Object Counts
ra1, ra2, ra3, ra4, ra5, ra6, ra7 = st.columns(7)

ra1.metric("Health Score", f"{filtered_score}/100", 
           help="Ratio-based score (0–100). Each category scored as % of objects that are clean. Weighted: Broken Ref 35%, Duplicates 25%, Join Integrity 25%, Field Quality 15%. Proportional to repo size — a large repo with few issues scores high.")
_kpi_with_detail(ra2, "Total Issues", len(filtered_issues_all), 
                 all_issue_objs, color="#7B8FAE")
ra3.metric("Views", f"{len(filtered_views):,}",  
           help="Number of LookML view blocks parsed. Multiple views can exist in one file — each block is counted separately.")
ra4.metric("Explores", f"{len(filtered_explores):,}", 
           help="Number of explores parsed from all .model.lkml files. Explores define what end users can query in Looker.")
ra5.metric("Derived Tables", f"{derived_count:,}",        
           help="Views using a derived_table: { sql: ... } block. These run as subqueries at query time and may be performance-intensive.")
ra6.metric("Dimensions", f"{dim_count:,}",    
           help="Dimensions define the attributes and groupable columns in your data model. Includes dimension, dimension_group, and filter field types.")
ra7.metric("Measures", f"{meas_count:,}",   
           help="Measures define aggregations (SUM, COUNT, AVG etc.) in your data model. A high measures-to-dimensions ratio may indicate over-aggregation.")

st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)

# Row 2 — Field Quality & Warnings
rb1, rb2, rb3, rb4, rb5, rb6, rb7 = st.columns(7)

_kpi_with_detail(rb1, "Errors", len(error_issues), 
                 error_objects, color="#ef4444")
_kpi_with_detail(rb2, "Warnings", len(warning_issues), 
                 warning_objects, color="#fbbf24")
_kpi_with_detail(rb3, "Orphan Views", orphan_view_count, 
                 orphan_in_filter, color="#fbbf24", 
                 help_text="Views that exist in the codebase but are not joined into any explore. They are invisible to Looker end users and may be safe to remove or archive.")
_kpi_with_detail(rb4, "Zombie Explores", zombie_exp_count, 
                 zombie_in_filter, color="#ef4444", 
                 help_text="Explores whose base view (from: or view_name:) does not exist in the project. These explores are completely broken and will fail at query time.")
_kpi_with_detail(rb5, "Missing PK", len(no_pk_views), 
                 no_pk_views, color="#fbbf24", 
                 help_text="Views with no dimension marked as primary_key: yes. Missing primary keys cause incorrect COUNT DISTINCT results, fanout bugs, and broken symmetric aggregates in Looker.")
_kpi_with_detail(rb6, "No Label", len(no_label_items), 
                 no_label_items, color="#7B8FAE", 
                 help_text="Visible dimensions and measures with no user-friendly label defined. Labels are what Looker end users see in the field picker — missing labels make the model hard to self-serve.")
_kpi_with_detail(rb7, "No Description", len(no_desc_items), 
                 no_desc_items, color="#7B8FAE", 
                 help_text="Visible dimensions and measures with no description: defined. Descriptions appear as tooltips in Looker. Without them, users cannot understand what a field means or how to use it correctly.")

st.markdown("<div style='margin-top:24px;'></div>", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# Tabs
# ─────────────────────────────────────────────────────────────
tab_ov, tab_iss, tab_viz, tab_inv, tab_fv, tab_cfg = st.tabs([
    "  Overview  ", "  Issues  ", "  Visualizations  ",
    "  Inventory  ", "  File Viewer  ", "  ⚙ Settings  ",
])


# ═══════════════════════════════════════════════════════════════
# TAB 1 — Overview
# ═══════════════════════════════════════════════════════════════
with tab_ov:
    cg, cb, cd = st.columns([2, 3, 2])
    with cg:
        st.markdown('<div class="section-header">Health Score</div>', unsafe_allow_html=True)
        st.plotly_chart(make_gauge(filtered_score), use_container_width=True,
                        config={"displayModeBar": False})
    with cb:
        st.markdown('<div class="section-header">Issues by Category</div>', unsafe_allow_html=True)
        if filtered_issues_all:
            st.plotly_chart(make_cat_bar(filtered_issues_all), use_container_width=True,
                            config={"displayModeBar": False})
        else:
            st.success("✓ No issues found")
    with cd:
        st.markdown('<div class="section-header">By Severity</div>', unsafe_allow_html=True)
        if filtered_issues_all:
            st.plotly_chart(make_donut(filtered_issues_all), use_container_width=True,
                            config={"displayModeBar": False})

    # Category scores
    cat_scores = compute_category_scores(filtered_issues_all, project)
    cs1, cs2, cs3, cs4 = st.columns(4)
    for col, (cat_name, cat_s) in zip([cs1, cs2, cs3, cs4], cat_scores.items()):
        sc_color = "#22c55e" if cat_s >= 85 else "#fbbf24" if cat_s >= 60 else "#ef4444"
        col.markdown(
            f"<div style='background:#1A2438;border:1px solid #1E2D4A;border-radius:10px;"
            f"padding:12px 14px;text-align:center;'>"
            f"<div style='font-family:JetBrains Mono,monospace;font-size:9px;color:#7B8FAE;"
            f"letter-spacing:.1em;text-transform:uppercase;margin-bottom:6px;'>{cat_name}</div>"
            f"<div style='font-family:JetBrains Mono,monospace;font-size:22px;font-weight:700;"
            f"color:{sc_color};'>{cat_s}/100</div>"
            f"</div>", unsafe_allow_html=True)

    st.markdown("<div style='margin-top:12px;'></div>", unsafe_allow_html=True)

    with st.expander("ℹ  How is the Health Score calculated?"):
        st.markdown(
            f"<div style='font-family:JetBrains Mono,monospace;font-size:12px;line-height:1.8;color:#7B8FAE;'>"
            f"<b style='color:#e2e8f0;'>Ratio-based scoring</b> — each category is scored as the "
            f"percentage of objects that are clean (no issues).<br><br>"
            f"<b style='color:#4A9EFF;'>Broken Reference (35%)</b>: issues / (explores + joins)<br>"
            f"<b style='color:#4A9EFF;'>Duplicate Def (25%)</b>: issues / (views + fields)<br>"
            f"<b style='color:#4A9EFF;'>Join Integrity (25%)</b>: issues / (joins × 2)<br>"
            f"<b style='color:#4A9EFF;'>Field Quality (15%)</b>: issues / (fields + views)<br><br>"
            f"Overall = weighted average of the four category scores.<br>"
            f"This is proportional to repo size — a large repo with few issues scores high.<br>"
            f"<b style='color:#4A9EFF;'>Current:</b> "
            f"{len(error_issues)} errors · {len(warning_issues)} warnings · "
            f"{len(filtered_issues_all) - len(error_issues) - len(warning_issues)} info"
            f"</div>", unsafe_allow_html=True)

    st.markdown('<div class="section-header">Issue Summary</div>', unsafe_allow_html=True)
    active_cats = list(IssueCategory)
    card_cols   = st.columns(len(active_cats))
    for col, cat in zip(card_cols, active_cats):
        ci  = [i for i in filtered_issues_all if i.category == cat]
        e   = sum(1 for i in ci if i.severity == Severity.ERROR)
        w   = sum(1 for i in ci if i.severity == Severity.WARNING)
        inf = sum(1 for i in ci if i.severity == Severity.INFO)
        with col:
            st.markdown(_card(cat.value, len(ci), e, w, inf), unsafe_allow_html=True)

    st.markdown(
        "<div style='font-family:JetBrains Mono,monospace;font-size:10px;color:#94A3B8;margin-top:12px;line-height:1.8;'>"
        "<b style='color:#60A5FA;'>Broken Reference</b> — Explores/joins pointing to missing views &nbsp;|&nbsp; "
        "<b style='color:#60A5FA;'>Duplicate Definition</b> — Same view in 2+ files · duplicate fields · same SQL · same table in 2+ views &nbsp;|&nbsp; "
        "<b style='color:#60A5FA;'>Join Integrity</b> — Missing sql_on · bad field refs · missing relationship &nbsp;|&nbsp; "
        "<b style='color:#60A5FA;'>Field Quality</b> — Missing PKs · orphaned views · missing labels/descriptions"
        "</div>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# TAB 2 — Issues
# ═══════════════════════════════════════════════════════════════
with tab_iss:
    st.markdown('<div class="section-header">All Issues</div>', unsafe_allow_html=True)
    if not filtered_issues:
        st.success("✓ No issues matching your current filters.")
    else:
        all_cats = sorted({i.category.value for i in filtered_issues})
        sel_cats = st.multiselect("Filter by category", options=all_cats, default=all_cats,
                                   label_visibility="collapsed")
        display_issues = [i for i in filtered_issues if i.category.value in sel_cats]
        rows = [{"Severity": i.severity.upper(), "Category": i.category.value,
                 "Object": i.object_name, "Type": i.object_type, "Message": i.message,
                 "File": Path(i.source_file).name if i.source_file else "",
                 "Line": i.line_number or ""} for i in display_issues]
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True, height=440)

        st.markdown('<div class="section-header">Details & Suggestions (first 50)</div>',
                    unsafe_allow_html=True)
        for issue in display_issues[:50]:
            sc = {"error": "#ef4444", "warning": "#fbbf24", "info": "#4a9eff"}.get(issue.severity, "#888")
            with st.expander(f"[{issue.severity.upper()}]  {issue.object_name}  —  {issue.category.value}"):
                st.markdown(
                    f"<div style='font-family:JetBrains Mono,monospace;font-size:13px;line-height:1.7;'>"
                    f"<div style='color:{sc};margin-bottom:8px;'>● {issue.message}</div>"
                    f"<div style='color:#7B8FAE;font-size:11px;'>"
                    f"Type: <b style='color:#e2e8f0'>{issue.object_type}</b> &nbsp;|&nbsp;"
                    f"File: <b style='color:#e2e8f0'>"
                    f"{Path(issue.source_file).name if issue.source_file else '—'}</b> &nbsp;|&nbsp;"
                    f"Line: <b style='color:#e2e8f0'>{issue.line_number or '—'}</b>"
                    f"</div>"
                    + (f"<div style='margin-top:12px;background:#0F1628;border-left:3px solid #4a9eff;"
                       f"padding:10px 14px;border-radius:0 6px 6px 0;color:#4A9EFF;font-size:12px;'>"
                       f"💡 {issue.suggestion}</div>" if issue.suggestion else "")
                    + "</div>", unsafe_allow_html=True)
        if len(display_issues) > 50:
            st.info(f"Showing 50 of {len(display_issues)} issues. Export JSON for the full list.")


# ═══════════════════════════════════════════════════════════════
# TAB 3 — Visualizations
# ═══════════════════════════════════════════════════════════════
with tab_viz:
    st.markdown(
        f"<div style='display:flex;gap:32px;font-family:JetBrains Mono,monospace;font-size:11px;"
        f"color:#7B8FAE;margin-bottom:16px;padding:12px 16px;"
        f"background:#0F1628;border:1px solid #1E2D4A;border-radius:8px;'>"
        f"<span><span style='color:#4A9EFF;font-weight:700;'>{len(filtered_explores)}</span> explores</span>"
        f"<span><span style='color:#4A9EFF;font-weight:700;'>{len(filtered_views)}</span> views</span>"
        f"<span><span style='color:#818CF8;font-weight:700;'>{total_fields}</span> fields</span>"
        f"<span><span style='color:#F59E0B;font-weight:700;'>{derived_count}</span> derived tables</span>"
        f"</div>", unsafe_allow_html=True)

    vt1, vt2 = st.tabs(["  Treemap — Field Distribution  ", "  Explore Coverage  "])

    with vt1:
        st.markdown('<div class="section-header">Field Distribution by View</div>',
                    unsafe_allow_html=True)
        st.caption("Each tile = one view. Size = total fields. Hover for details.")
        tm_f = st.radio("show", ["All Views", "Derived Tables Only", "Regular Tables Only"],
                         horizontal=True, label_visibility="collapsed")
        tm_v = filtered_views
        if tm_f == "Derived Tables Only":   tm_v = [v for v in filtered_views if v.is_derived_table]
        elif tm_f == "Regular Tables Only": tm_v = [v for v in filtered_views if not v.is_derived_table]
        if not tm_v:
            st.info("No views match this filter.")
        else:
            df_tm = pd.DataFrame([{
                "view": v.name, "fields": len(v.fields),
                "dimensions": len(v.dimensions), "measures": len(v.measures),
                "pk": v.primary_key_field.name if v.has_primary_key else "Missing",
                "vtype": "Derived" if v.is_derived_table else "Table",
                "source": Path(v.source_file).name if v.source_file else "—"
            } for v in tm_v])
            fig_tm = go.Figure(go.Treemap(
                labels=df_tm["view"], parents=[""] * len(df_tm), values=df_tm["fields"],
                customdata=df_tm[["dimensions","measures","pk","vtype","source"]].values,
                texttemplate="<b>%{label}</b><br>%{value} fields",
                hovertemplate=("<b>%{label}</b><br>Fields: %{value}<br>"
                               "Dimensions: %{customdata[0]}<br>Measures: %{customdata[1]}<br>"
                               "PK: %{customdata[2]}<br>Type: %{customdata[3]}<br>"
                               "File: %{customdata[4]}<extra></extra>"),
                marker=dict(
                    colors=df_tm["fields"],
                    colorscale=[[0,"#0d1929"],[0.3,"#0d3d6b"],[0.6,"#1565c0"],
                                [0.85,"#4a9eff"],[1,"#93c5fd"]],
                    showscale=True,
                    colorbar=dict(
                        title=dict(text="Fields",
                                   font=dict(family="IBM Plex Mono", size=11, color="#7B8FAE")),
                        tickfont=dict(family="IBM Plex Mono", size=10, color="#7B8FAE"),
                        bgcolor="rgba(0,0,0,0)", bordercolor="#1E2D4A"),
                ),
                textfont=dict(family="IBM Plex Mono", size=11, color="#e2e8f0"),
            ))
            fig_tm.update_layout(height=540, margin=dict(l=0,r=0,t=10,b=0),
                                  paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_tm, use_container_width=True, config={"displayModeBar": True})
            ta, tb, tc, td = st.columns(4)
            ta.metric("Views shown",     len(tm_v))
            tb.metric("Total Fields",    int(df_tm["fields"].sum()))
            tc.metric("Avg Fields/View", f'{df_tm["fields"].mean():.1f}')
            td.metric("Largest View",    df_tm.loc[df_tm["fields"].idxmax(), "view"])

    with vt2:
        st.markdown('<div class="section-header">Explore Coverage Analysis</div>',
                    unsafe_allow_html=True)
        if not filtered_explores:
            st.info("No explores in current filter.")
        else:
            view_map_live = project.view_map
            exp_data = []
            for exp in filtered_explores:
                ev = [exp.base_view] + [j.resolved_view for j in exp.joins]
                broken = sum(1 for v in ev if v not in view_map_live)
                exp_data.append({"explore": exp.name, "joins": len(exp.joins),
                                 "total_views": len(ev), "broken": broken})
            
            # 1. Sort explicitly by 'joins' ascending
            # 2. Grab the tail(20) to keep the highest values
            # (Plotly draws the bottom of the dataframe at the top of the chart)
            df_exp = (pd.DataFrame(exp_data)
                      .sort_values(by="joins", ascending=True)
                      .tail(20))

            st.markdown('<div class="section-header">Top 20 Explores by Join Count</div>',
                        unsafe_allow_html=True)
            fig_j = go.Figure()
            fig_j.add_trace(go.Bar(y=df_exp["explore"], x=df_exp["joins"], orientation="h",
                                    name="Joins", marker_color="#3B82F6", text=df_exp["joins"],
                                    textposition="outside",
                                    textfont=dict(family="IBM Plex Mono", size=10, color="#94A3B8")))
            fig_j.add_trace(go.Bar(y=df_exp["explore"], x=df_exp["broken"], orientation="h",
                                    name="Broken refs", marker_color="#EF4444",
                                    text=[str(b) if b > 0 else "" for b in df_exp["broken"]],
                                    textposition="outside",
                                    textfont=dict(family="IBM Plex Mono", size=10, color="#EF4444")))
            fig_j.update_layout(
                height=max(300, len(df_exp)*22+100), barmode="stack",
                margin=dict(l=10,r=60,t=10,b=10),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(gridcolor="#334155",
                           tickfont=dict(family="IBM Plex Mono",size=10,color="#94A3B8")),
                # EXPLICITLY lock the axis sorting to the dataframe's row order
                yaxis=dict(
                    categoryorder='array', 
                    categoryarray=df_exp["explore"],
                    tickfont=dict(family="IBM Plex Mono",size=10,color="#F8FAFC"),
                    showgrid=False
                ),
                legend=dict(font=dict(family="IBM Plex Mono",size=11,color="#94A3B8"),bgcolor="rgba(0,0,0,0)"))
            st.plotly_chart(fig_j, use_container_width=True, config={"displayModeBar": False})

            st.markdown('<div class="section-header">Top 20 View Usage Frequency</div>',
                        unsafe_allow_html=True)
            st.caption("How many explores reference each view. Red = never used.")
            vfreq: Counter = Counter()
            for exp in filtered_explores:
                vfreq[exp.base_view] += 1
                for j in exp.joins: vfreq[j.resolved_view] += 1
            for v in filtered_views:
                if v.name not in vfreq: vfreq[v.name] = 0
            df_vf = (pd.DataFrame({"view": list(vfreq), "count": list(vfreq.values())})
                     .sort_values("count", ascending=False).head(20))
            bar_colors = ["#ef4444" if c==0 else "#fbbf24" if c==1 else "#4a9eff"
                          for c in df_vf["count"]]
            fig_vf = go.Figure(go.Bar(
                x=df_vf["view"], y=df_vf["count"], marker_color=bar_colors,
                text=df_vf["count"], textposition="outside",
                textfont=dict(family="IBM Plex Mono", size=9, color="#7B8FAE"),
                hovertemplate="<b>%{x}</b><br>Used in %{y} explore(s)<extra></extra>"))
            fig_vf.update_layout(
                height=360, margin=dict(l=10,r=10,t=10,b=120),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(tickfont=dict(family="IBM Plex Mono",size=9,color="#7B8FAE"),
                           tickangle=-50,showgrid=False),
                yaxis=dict(gridcolor="#1E2D4A",
                           tickfont=dict(family="IBM Plex Mono",size=10,color="#7B8FAE")),
                showlegend=False)
            st.plotly_chart(fig_vf, use_container_width=True, config={"displayModeBar": False})
            st.markdown(
                "<div style='display:flex;gap:20px;font-family:JetBrains Mono,monospace;font-size:11px;color:#7B8FAE;'>"
                "<span><span style='color:#ef4444;'>■</span> Never used</span>"
                "<span><span style='color:#fbbf24;'>■</span> 1 explore</span>"
                "<span><span style='color:#4A9EFF;'>■</span> 2+ explores</span></div>",
                unsafe_allow_html=True)
            va, vb, vc, vd = st.columns(4)
            va.metric("Total Views",  len(vfreq))
            vb.metric("Never Used",   sum(1 for c in vfreq.values() if c==0))
            vc.metric("Used in 1",    sum(1 for c in vfreq.values() if c==1))
            vd.metric("Shared (2+)",  sum(1 for c in vfreq.values() if c>=2))


# ═══════════════════════════════════════════════════════════════
# TAB 4 — Inventory
# ═══════════════════════════════════════════════════════════════
with tab_inv:
    # Case 5: Add quick-jump anchor to skip past derived tables
    inv_subtab_views, inv_subtab_dt, inv_subtab_exp, inv_subtab_joins, inv_subtab_fields = st.tabs([
        "  Views  ", "  Derived Tables  ", "  Explores  ", "  Join Relationships  ", "  All Fields  "
    ])

    with inv_subtab_views:
        st.markdown('<div class="section-header">Views</div>', unsafe_allow_html=True)
        view_rows = [{
            "View":        v.name,
            "Dimensions":  len(v.dimensions),
            "Measures":    len(v.measures),
            "Fields":      len(v.fields),
            "Primary Key": v.primary_key_field.name if v.has_primary_key else "⚠ Missing",
            "Derived":     "Yes" if v.is_derived_table else "No",
            "SQL Table":   v.sql_table_name or "—",
            "Orphan":      "⚠ Yes" if v.name in orphan_view_names else "",
            "Source":      Path(v.source_file).name if v.source_file else "",
        } for v in filtered_views]
        st.dataframe(pd.DataFrame(view_rows), use_container_width=True, hide_index=True)

    with inv_subtab_dt:
        # Case 5: Derived tables now in own tab — no scrolling past them
        dv = [v for v in filtered_views if v.is_derived_table]
        if not dv:
            st.info("No derived tables in current filter.")
        else:
            st.markdown('<div class="section-header">Derived Tables — SQL Preview</div>',
                        unsafe_allow_html=True)
            st.caption(f"{len(dv)} derived table(s) — click any row to expand full SQL.")
            for v in dv:
                raw_sql = v.derived_table_sql or ""
                pk_val  = v.primary_key_field.name if v.has_primary_key else "⚠ Missing"
                with st.expander(f"▶  {v.name}   ({len(v.fields)} fields · PK: {pk_val})"):
                    st.code(raw_sql, language="sql")

    with inv_subtab_exp:
        st.markdown('<div class="section-header">Explores</div>', unsafe_allow_html=True)
        exp_rows = []
        for e in filtered_explores:
            # Tally relationships for this explore
            rels = [j.relationship or "undefined" for j in e.joins]
            rel_summary = ", ".join(
                f"{v}×{k}" for k, v in
                sorted(Counter(rels).items(), key=lambda x: -x[1])
            ) if rels else "—"
            join_types_list = sorted({(j.type or "left_outer").replace("_", " ") for j in e.joins})
            exp_rows.append({
                "Explore":        e.name,
                "Label":          e.label or "—",
                "Base View":      e.base_view,
                "Joins":          len(e.joins),
                "Relationships":  rel_summary,
                "Join Types":     ", ".join(join_types_list) if join_types_list else "—",
                "Zombie":         "🔴 Yes" if e.name in zombie_explore_names else "",
                "Source":         Path(e.source_file).name if e.source_file else "",
            })
        st.dataframe(pd.DataFrame(exp_rows), use_container_width=True, hide_index=True)

    with inv_subtab_joins:
        st.markdown('<div class="section-header">Join Relationship Summary</div>', unsafe_allow_html=True)
        st.caption("All joins across all explores with their relationship type, join type, and sql_on condition.")

        # Pre-compute join stats
        from collections import Counter as _JCounter
        _all_joins = []
        for _exp in filtered_explores:
            for _j in _exp.joins:
                _all_joins.append({
                    "Explore":      _exp.name,
                    "Join":         _j.name,
                    "Resolved View":_j.resolved_view,
                    "Type":         (_j.type or "left_outer").replace("_", " ").title(),
                    "Relationship": (_j.relationship or "⚠ Missing").replace("_", " ").title(),
                    "Has sql_on":   "✓" if _j.sql_on else ("✓ (sql:)" if False else "⚠ Missing"),
                    "File":         Path(_j.source_file).name if _j.source_file else "",
                })

        if not _all_joins:
            st.info("No joins found in current filter.")
        else:
            _df_joins = pd.DataFrame(_all_joins)

            # Summary stats row
            _rel_counts = _JCounter(_df_joins["Relationship"])
            _type_counts = _JCounter(_df_joins["Type"])
            _missing_rel = sum(1 for j in _all_joins if "Missing" in j["Relationship"])

            _ja, _jb, _jc, _jd = st.columns(4)
            _ja.metric("Total Joins",       f"{len(_all_joins):,}")
            _jb.metric("Missing Relationship", f"{_missing_rel:,}",
                       help="Joins without a relationship: type defined. Causes fanout risk.")
            _jc.metric("Unique Join Types",  len(_type_counts))
            _jd.metric("Unique Rel Types",   len(_rel_counts))

            # Relationship breakdown chart
            if _rel_counts:
                st.markdown('<div class="section-header">Relationship Type Breakdown</div>',
                            unsafe_allow_html=True)
                _rel_df = pd.DataFrame({"Relationship": list(_rel_counts.keys()),
                                        "Count": list(_rel_counts.values())
                                        }).sort_values("Count", ascending=False)
                _rel_colors = {
                    "Many To One":  "#4A9EFF",
                    "One To Many":  "#F472B6",
                    "One To One":   "#10B981",
                    "Many To Many": "#F59E0B",
                    "⚠ Missing":   "#EF4444",
                }
                _fig_rel = go.Figure(go.Bar(
                    x=_rel_df["Count"], y=_rel_df["Relationship"],
                    orientation="h",
                    marker_color=[_rel_colors.get(r, "#7B8FAE") for r in _rel_df["Relationship"]],
                    text=_rel_df["Count"], textposition="outside",
                    textfont=dict(family="IBM Plex Mono", size=11, color="#7B8FAE"),
                ))
                _fig_rel.update_layout(
                    height=max(200, len(_rel_df) * 44 + 60),
                    margin=dict(l=10, r=50, t=10, b=10),
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    xaxis=dict(gridcolor="#1E2D4A", tickfont=dict(family="IBM Plex Mono", size=10, color="#7B8FAE")),
                    yaxis=dict(tickfont=dict(family="IBM Plex Mono", size=12, color="#e2e8f0"), showgrid=False),
                    showlegend=False,
                )
                st.plotly_chart(_fig_rel, use_container_width=True, config={"displayModeBar": False})

            # Join type breakdown
            if _type_counts:
                st.markdown('<div class="section-header">Join Type Breakdown</div>',
                            unsafe_allow_html=True)
                _type_df = pd.DataFrame({"Join Type": list(_type_counts.keys()),
                                         "Count": list(_type_counts.values())
                                         }).sort_values("Count", ascending=False)
                _type_colors = {
                    "Left Outer":  "#4A9EFF",
                    "Inner":       "#10B981",
                    "Full Outer":  "#F59E0B",
                    "Cross":       "#818CF8",
                }
                _fig_type = go.Figure(go.Bar(
                    x=_type_df["Count"], y=_type_df["Join Type"],
                    orientation="h",
                    marker_color=[_type_colors.get(t, "#7B8FAE") for t in _type_df["Join Type"]],
                    text=_type_df["Count"], textposition="outside",
                    textfont=dict(family="IBM Plex Mono", size=11, color="#7B8FAE"),
                ))
                _fig_type.update_layout(
                    height=max(180, len(_type_df) * 44 + 60),
                    margin=dict(l=10, r=50, t=10, b=10),
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    xaxis=dict(gridcolor="#1E2D4A", tickfont=dict(family="IBM Plex Mono", size=10, color="#7B8FAE")),
                    yaxis=dict(tickfont=dict(family="IBM Plex Mono", size=12, color="#e2e8f0"), showgrid=False),
                    showlegend=False,
                )
                st.plotly_chart(_fig_type, use_container_width=True, config={"displayModeBar": False})

            # Full join table with filter
            st.markdown('<div class="section-header">All Joins</div>', unsafe_allow_html=True)
            _rel_filter = st.multiselect(
                "Filter by relationship",
                options=sorted(_df_joins["Relationship"].unique()),
                default=sorted(_df_joins["Relationship"].unique()),
                label_visibility="collapsed", key="join_rel_filter"
            )
            _df_joins_display = _df_joins[_df_joins["Relationship"].isin(_rel_filter)]
            st.dataframe(_df_joins_display, use_container_width=True, hide_index=True, height=420)

    with inv_subtab_fields:
        st.markdown('<div class="section-header">All Fields</div>', unsafe_allow_html=True)
        field_rows = [{
            "View":        v.name,
            "Field":       f.name,
            "Label":       f.label or "⚠ Missing",
            "Type":        f.field_type,
            "Data Type":   f.data_type or "—",
            "Description": f.description or "⚠ Missing",
            "Primary Key": "✓" if f.primary_key else "",
            "Hidden":      "yes" if f.hidden else "",
            "Source":      Path(f.source_file).name if f.source_file else "",
        } for v in filtered_views for f in v.fields]
        st.dataframe(pd.DataFrame(field_rows), use_container_width=True,
                     hide_index=True, height=480)


# ═══════════════════════════════════════════════════════════════
# TAB 5 — File Viewer
# ═══════════════════════════════════════════════════════════════
with tab_fv:
    st.markdown('<div class="section-header">File Viewer</div>', unsafe_allow_html=True)
    st.caption("Select a .lkml file to view its source with issue annotations inline.")

    all_files = sorted({
        obj.source_file
        for obj_list in [project.views, project.explores,
                         [j for e in project.explores for j in e.joins]]
        for obj in obj_list
        if getattr(obj, "source_file", "")
    })

    if not all_files:
        st.info("No source files found.")
    else:
        root = Path(project.root_path)
        def _rel(p: str) -> str:
            try:    return str(Path(p).relative_to(root))
            except: return Path(p).name

        file_opts = {_rel(f): f for f in all_files}
        fv1, fv2 = st.columns([4, 1])
        with fv1:
            sel_rel = st.selectbox("file", options=sorted(file_opts.keys()),
                                   label_visibility="collapsed", key="fv_sel")
        with fv2:
            issues_only = st.checkbox("Issues only", value=False, key="fv_only")
        # Search box
        fv_search = st.text_input(
            "🔍  Search in file", value="", placeholder="field name, view name, SQL keyword...",
            label_visibility="collapsed", key="fv_search"
        )

        sel_abs = file_opts[sel_rel]
        try:
            raw = Path(sel_abs).read_text(encoding="utf-8", errors="replace")
        except Exception as ex:
            st.error(f"Cannot read file: {ex}"); raw = ""

        if raw:
            sel_norm  = _norm(sel_abs)
            sel_fname = Path(sel_abs).name.lower()
            file_issues = [i for i in issues if i.source_file and _norm(i.source_file)==sel_norm]
            if not file_issues:
                file_issues = [i for i in issues
                               if i.source_file and Path(i.source_file).name.lower()==sel_fname]

            lmap: dict[int, list] = {}
            for iss in file_issues:
                lmap.setdefault(iss.line_number or 0, []).append(iss)

            fa, fb, fc, fd = st.columns(4)
            fa.metric("Lines",    len(raw.splitlines()))
            fb.metric("Errors",   sum(1 for i in file_issues if i.severity=="error"))
            fc.metric("Warnings", sum(1 for i in file_issues if i.severity=="warning"))
            fd.metric("Info",     sum(1 for i in file_issues if i.severity=="info"))

            if file_issues:
                st.markdown('<div class="section-header">Issues in this file</div>',
                            unsafe_allow_html=True)
                irows = [{"Line": i.line_number or "—", "Severity": i.severity.upper(),
                          "Category": i.category.value, "Object": i.object_name,
                          "Message": i.message}
                         for i in sorted(file_issues, key=lambda x: x.line_number or 0)]
                st.dataframe(pd.DataFrame(irows), use_container_width=True,
                             hide_index=True, height=180)
            else:
                st.success("✓ No issues found in this file.")

            st.markdown('<div class="section-header">Source</div>', unsafe_allow_html=True)
            ICONS = {"error": "🔴", "warning": "🟡", "info": "🔵"}
            lines = raw.splitlines()

            if issues_only and lmap:
                context = set()
                for il in lmap:
                    for off in range(-5, 6): context.add(il + off)
                context = {c for c in context if 1 <= c <= len(lines)}
                out, prev = [], None
                for ln, lt in enumerate(lines, 1):
                    if ln not in context: continue
                    if prev is not None and ln > prev + 1:
                        out.append(f"  # ··· ({ln-prev-1} lines skipped) ···")
                    out.append(f"{ln:4d}  {lt}")
                    for iss in lmap.get(ln, []):
                        out.append(f"       # {ICONS.get(iss.severity,'●')} "
                                   f"[{iss.severity.upper()}] {iss.message}")
                    prev = ln
                display_code = "\n".join(out)
            else:
                out = []
                for ln, lt in enumerate(lines, 1):
                    out.append(f"{ln:4d}  {lt}")
                    for iss in lmap.get(ln, []):
                        out.append(f"       # {ICONS.get(iss.severity,'●')} "
                                   f"[{iss.severity.upper()}] {iss.message}")
                display_code = "\n".join(out)

            # Apply search highlighting
            if fv_search.strip():
                term = fv_search.strip().lower()
                matched_lines = [ln for ln, lt in enumerate(lines, 1)
                                 if term in lt.lower()]
                if matched_lines:
                    st.markdown(
                        f"<div style='font-family:JetBrains Mono,monospace;font-size:11px;color:#34d399;"
                        f"margin-bottom:8px;'>🔍 Found {len(matched_lines)} match(es) on lines: "
                        f"{', '.join(str(l) for l in matched_lines[:20])}"
                        f"{'...' if len(matched_lines)>20 else ''}</div>",
                        unsafe_allow_html=True)
                    # Filter display_code to show only matching lines ±3 context
                    search_context = set()
                    for ml in matched_lines:
                        for off in range(-3, 4): search_context.add(ml + off)
                    search_context = {c for c in search_context if 1 <= c <= len(lines)}
                    s_out, s_prev = [], None
                    for ln, lt in enumerate(lines, 1):
                        if ln not in search_context: continue
                        if s_prev is not None and ln > s_prev + 1:
                            s_out.append(f"  # ··· ({ln-s_prev-1} lines) ···")
                        # Annotate matching lines
                        prefix = ">>> " if term in lt.lower() else "    "
                        s_out.append(f"{ln:4d}{prefix}{lt}")
                        for iss in lmap.get(ln, []):
                            s_out.append(f"       # {ICONS.get(iss.severity, chr(9679))} [{iss.severity.upper()}] {iss.message}")
                        s_prev = ln
                    st.code("\n".join(s_out), language="sql")
                else:
                    st.warning(f"No matches found for '{fv_search}'")
                    st.code(display_code, language="sql")
            else:
                st.code(display_code, language="sql")


# ═══════════════════════════════════════════════════════════════
# TAB 6 — Settings: Suppression Rules + Manifest Info
# ═══════════════════════════════════════════════════════════════
with tab_cfg:
    st.markdown('<div class="section-header">Suppression Rules</div>', unsafe_allow_html=True)
    st.caption(
        "Create a `lookml_auditor.yaml` file in your LookML project root to suppress "
        "known false positives without touching validator code."
    )

    # Show current suppression file status
    config_path = Path(project.root_path) / "lookml_auditor.yaml"
    if config_path.exists():
        st.success(f"✓ Suppression config found: {config_path.name}")
        try:
            cfg_text = config_path.read_text(encoding="utf-8")
            st.code(cfg_text, language="yaml")
        except Exception:
            st.warning("Could not read config file.")
        if suppressed:
            st.markdown(
                f"<div style='font-family:JetBrains Mono,monospace;font-size:13px;color:#fbbf24;"
                f"padding:10px 14px;background:#2e251018;border:1px solid #4a3a18;"
                f"border-radius:8px;margin-top:8px;'>⚡ {suppressed} issues suppressed "
                f"by rules in this run.</div>", unsafe_allow_html=True)
    else:
        st.info("No `lookml_auditor.yaml` found in project root. "
                "Create one to suppress known false positives.")
        with st.expander("📋 Show example config (copy to your project root)"):
            st.code(EXAMPLE_CONFIG, language="yaml")
        # Offer to generate the file
        if st.button("📝 Generate example lookml_auditor.yaml in project root"):
            try:
                config_path.write_text(EXAMPLE_CONFIG, encoding="utf-8")
                st.success(f"Created {config_path} — edit it to add your suppression rules, "
                           f"then re-run the audit.")
            except Exception as ex:
                st.error(f"Could not write file: {ex}")

    # Manifest constants
    st.markdown('<div class="section-header">Manifest Constants</div>', unsafe_allow_html=True)
    if manifest:
        st.caption(f"Loaded {len(manifest)} constants from manifest.lkml. "
                   f"These are resolved in sql_table_name fields (e.g. @{{SAS_Schema}} → value).")
        man_rows = [{"Constant": k, "Resolved Value": v} for k, v in sorted(manifest.items())]
        st.dataframe(pd.DataFrame(man_rows), use_container_width=True, hide_index=True)
    else:
        st.info("No manifest.lkml found in project root, or no constants defined. "
                "Constants are used to resolve @{ConstantName} in sql_table_name fields.")
        st.markdown(
            "<div style='font-family:JetBrains Mono,monospace;font-size:12px;color:#7B8FAE;"
            "padding:12px;background:#0F1628;border:1px solid #1E2D4A;border-radius:8px;"
            "margin-top:8px;'>Example manifest.lkml:<br><br>"
            "constant: SAS_Schema {<br>"
            "&nbsp;&nbsp;value: &quot;PROD_DB&quot;<br>"
            "&nbsp;&nbsp;export: override_optional<br>"
            "}</div>",
            unsafe_allow_html=True)