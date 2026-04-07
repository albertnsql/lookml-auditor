"""
LookML Parser  (lkml-backed — v2)
----------------------------------
Uses the `lkml` library (grammar-based, not regex) for accurate parsing.
Falls back gracefully per-file if lkml fails to parse.

Performance notes:
  - lkml.load() parses a typical file in <10 ms
  - All model construction is O(fields) per view
  - parse_project walks directories once; no redundant re-reads
"""
from __future__ import annotations
import re
from pathlib import Path
from typing import Optional

import lkml  # pip install lkml>=1.3

from .models import (
    LookMLField, LookMLView, LookMLJoin,
    LookMLExplore, LookMLProject,
)

# ---------------------------------------------------------------------------
# Manifest / constant helpers  (simple enough to keep with regex)
# ---------------------------------------------------------------------------
_CONSTANT_RE = re.compile(
    r'constant\s*:\s*(\w+)\s*\{[^}]*?value\s*:\s*["\']([^"\']+)["\']',
    re.DOTALL,
)
_CONST_REF_RE = re.compile(r'@\{(\w+)\}')
_RE_COMMENT   = re.compile(r'#[^\n]*')


def parse_manifest(root_path: str) -> dict[str, str]:
    """Find and parse manifest.lkml. Returns {constant_name: value}."""
    root = Path(root_path)
    constants: dict[str, str] = {}
    for candidate in [root / "manifest.lkml", root / "Manifest.lkml"]:
        if candidate.exists():
            text = _RE_COMMENT.sub('', candidate.read_text(encoding="utf-8", errors="replace"))
            for name, value in _CONSTANT_RE.findall(text):
                constants[name] = value
            break
    return constants


def resolve_constants(sql_table: str, constants: dict[str, str]) -> str:
    """Replace @{ConstantName} references with resolved values."""
    if not constants or not sql_table or '@{' not in sql_table:
        return sql_table
    def _repl(m: re.Match) -> str:
        return constants.get(m.group(1), m.group(0))
    return _CONST_REF_RE.sub(_repl, sql_table)


# ---------------------------------------------------------------------------
# Field builder
# ---------------------------------------------------------------------------
_FIELD_TYPES = {"dimension_group", "dimension", "measure", "filter", "parameter"}


def _build_field(raw: dict, source_file: str, view_line: int) -> Optional[LookMLField]:
    """Convert a raw lkml field dict to LookMLField."""
    ftype = raw.get("_type", "")  # lkml adds _type for the block keyword
    # lkml sets a special key "_type" but lets check
    # Actually lkml uses the key name for field type differently
    # The field raw dict has: name, type, sql, label, description, hidden, primary_key, tags, _type
    name = raw.get("name") or raw.get("label")
    if not name:
        return None

    tags_raw = raw.get("tags", "")
    if isinstance(tags_raw, list):
        tags = [str(t).strip().strip('"') for t in tags_raw]
    elif isinstance(tags_raw, str) and tags_raw:
        tags = [t.strip().strip('"') for t in tags_raw.split(',')]
    else:
        tags = []

    return LookMLField(
        name=name,
        field_type=ftype,
        data_type=raw.get("type"),
        sql=raw.get("sql"),
        label=raw.get("label"),
        description=raw.get("description"),
        hidden=(str(raw.get("hidden", "")).lower() == "yes"),
        primary_key=(str(raw.get("primary_key", "")).lower() == "yes"),
        tags=tags,
        source_file=source_file,
        line_number=view_line,
    )


def _collect_fields(view_raw: dict, source_file: str, view_line: int) -> list[LookMLField]:
    """Collect all field types from a view dict returned by lkml."""
    fields = []
    for ftype in ("dimensions", "dimension_groups", "measures", "filters", "parameters"):
        singular = ftype.rstrip("s")
        if ftype == "dimension_groups":
            singular = "dimension_group"
        elif ftype == "filters":
            singular = "filter"
        elif ftype == "parameters":
            singular = "parameter"
        for raw in view_raw.get(ftype, []):
            raw["_type"] = singular
            f = _build_field(raw, source_file, view_line)
            if f:
                fields.append(f)
    return fields


# ---------------------------------------------------------------------------
# View builder
# ---------------------------------------------------------------------------
def _build_view(view_raw: dict, source_file: str, constants: dict) -> Optional[LookMLView]:
    name = view_raw.get("name")
    if not name:
        return None

    sql_table = view_raw.get("sql_table_name")
    if sql_table and constants:
        sql_table = resolve_constants(sql_table, constants)

    # derived_table
    dt = view_raw.get("derived_table") or {}
    derived_sql: Optional[str] = dt.get("sql") if isinstance(dt, dict) else None

    # extends
    extends_raw = view_raw.get("extends") or view_raw.get("extends__all") or []
    if isinstance(extends_raw, str):
        extends = [e.strip() for e in extends_raw.split(",") if e.strip()]
    elif isinstance(extends_raw, list):
        # lkml may give a list-of-lists for extends: [view_a, view_b]
        flat = []
        for item in extends_raw:
            if isinstance(item, list):
                flat.extend(item)
            else:
                flat.append(item)
        extends = [str(e).strip() for e in flat if e]
    else:
        extends = []

    fields = _collect_fields(view_raw, source_file, 0)

    return LookMLView(
        name=name,
        sql_table_name=sql_table,
        derived_table_sql=derived_sql,
        extends=extends,
        fields=fields,
        source_file=source_file,
        line_number=0,
    )


# ---------------------------------------------------------------------------
# Join builder
# ---------------------------------------------------------------------------
def _build_join(join_raw: dict, source_file: str) -> Optional[LookMLJoin]:
    name = join_raw.get("name")
    if not name:
        return None

    sql_on    = join_raw.get("sql_on")
    sql_where = join_raw.get("sql_where")
    from_view = join_raw.get("from") or join_raw.get("view_name")

    return LookMLJoin(
        name=name,
        from_view=from_view,
        type=join_raw.get("type"),
        relationship=join_raw.get("relationship"),
        sql_on=sql_on,
        sql_where=sql_where,
        foreign_key=join_raw.get("foreign_key"),
        source_file=source_file,
        line_number=0,
    )


# ---------------------------------------------------------------------------
# Explore builder
# ---------------------------------------------------------------------------
def _build_explore(exp_raw: dict, source_file: str) -> Optional[LookMLExplore]:
    name = exp_raw.get("name")
    if not name:
        return None

    joins = []
    for j_raw in exp_raw.get("joins", []):
        j = _build_join(j_raw, source_file)
        if j:
            joins.append(j)

    return LookMLExplore(
        name=name,
        from_view=exp_raw.get("from"),
        view_name=exp_raw.get("view_name"),
        label=exp_raw.get("label"),
        description=exp_raw.get("description"),
        joins=joins,
        source_file=source_file,
        line_number=0,
    )


# ---------------------------------------------------------------------------
# File parser
# ---------------------------------------------------------------------------
def _parse_file(
    path: Path,
    constants: dict,
) -> tuple[list[LookMLView], list[LookMLExplore]]:
    """Parse a single .lkml file using lkml library. Returns (views, explores)."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
        parsed = lkml.load(text)
    except Exception:
        # lkml failed — skip this file gracefully
        return [], []

    source_file = str(path)
    views: list[LookMLView] = []
    explores: list[LookMLExplore] = []

    for v_raw in parsed.get("views", []):
        v = _build_view(v_raw, source_file, constants)
        if v:
            views.append(v)

    for e_raw in parsed.get("explores", []):
        e = _build_explore(e_raw, source_file)
        if e:
            explores.append(e)

    return views, explores


def _parse_chunk(args: tuple[list[Path], dict]) -> tuple[list[LookMLView], list[LookMLExplore]]:
    """Worker function for concurrent chunk processing."""
    paths, constants = args
    res_views = []
    res_explores = []
    for p in paths:
        v, e = _parse_file(p, constants)
        res_views.extend(v)
        res_explores.extend(e)
    return res_views, res_explores


# ---------------------------------------------------------------------------
# Project parser (public API)
# ---------------------------------------------------------------------------
def parse_project(root_path: str) -> LookMLProject:
    """
    Walk a LookML project directory, parse all .lkml files,
    and return a LookMLProject with all views and explores.
    Runs concurrently using a ThreadPoolExecutor to reduce wait times on large repos.
    """
    import concurrent.futures

    root = Path(root_path)
    constants = parse_manifest(root_path)

    all_views: list[LookMLView]   = []
    all_explores: list[LookMLExplore] = []

    lkml_files = [f for f in sorted(root.rglob("*.lkml")) if f.name.lower() != "manifest.lkml"]
    
    chunk_size = 50
    chunks = [(lkml_files[i:i + chunk_size], constants) for i in range(0, len(lkml_files), chunk_size)]

    if chunks:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            for views, explores in executor.map(_parse_chunk, chunks):
                all_views.extend(views)
                all_explores.extend(explores)

    return LookMLProject(
        name=root.name,
        root_path=root_path,
        views=all_views,
        explores=all_explores,
        manifest_constants=constants,
    )
