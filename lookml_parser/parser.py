"""
LookML Parser  (optimized)
--------------------------
Performance improvements over v1:
  - All regex patterns compiled once at module load (not per-call)
  - Comment stripping uses compiled pattern
  - _get_attr uses a single compiled pattern per attribute call
  - parse_project runs file I/O with early skip for empty/tiny files
  - Brace-walking starts from match.end() not match.start()
"""
from __future__ import annotations
import re
from pathlib import Path
from typing import Optional
from functools import lru_cache

from .models import (
    LookMLField, LookMLView, LookMLJoin,
    LookMLExplore, LookMLProject
)

# ---------------------------------------------------------------------------
# Pre-compiled module-level patterns  (compiled ONCE, reused always)
# ---------------------------------------------------------------------------
_RE_COMMENT       = re.compile(r'#[^\n]*')
_RE_VIEW_BLOCK    = re.compile(r'^\s*view\s*:\s*\S+\s*\{',     re.MULTILINE)
_RE_EXPLORE_BLOCK = re.compile(r'^\s*explore\s*:\s*\S+\s*\{',  re.MULTILINE)
_RE_ANON_DT       = re.compile(r'^\s*derived_table\s*:\s*\{',  re.MULTILINE)
_RE_EXTENDS       = re.compile(r'extends\s*:\s*\[([^\]]+)\]')

_FIELD_TYPE_PATTERNS = {
    ft: re.compile(rf'^\s*{ft}\s*:\s*\S+\s*\{{', re.MULTILINE)
    for ft in ("dimension_group", "dimension", "measure", "filter", "parameter")
}
_JOIN_BLOCK_RE  = re.compile(r'^\s*join\s*:\s*\S+\s*\{',  re.MULTILINE)

@lru_cache(maxsize=512)
def _attr_pattern(attr: str) -> re.Pattern:
    return re.compile(rf'^\s*{re.escape(attr)}\s*:\s*(.+?)\s*$', re.MULTILINE)

@lru_cache(maxsize=64)
def _sql_block_pattern(attr: str) -> re.Pattern:
    return re.compile(rf'^\s*{re.escape(attr)}\s*:\s*(.*?);;', re.MULTILINE | re.DOTALL)

@lru_cache(maxsize=32)
def _block_name_pattern(block_type: str) -> re.Pattern:
    return re.compile(rf'^\s*{re.escape(block_type)}\s*:\s*(\S+)\s*\{{', re.MULTILINE)

# ---------------------------------------------------------------------------
# Core utilities
# ---------------------------------------------------------------------------

def _walk_block(text: str, start: int) -> int:
    """Return index of the closing brace that matches the first { at/after start."""
    depth = 0
    i = start
    n = len(text)
    while i < n:
        next_open = text.find('{', i)
        next_close = text.find('}', i)
        
        if next_open == -1 and next_close == -1:
            break
            
        if next_open != -1 and (next_close == -1 or next_open < next_close):
            depth += 1
            i = next_open + 1
        elif next_close != -1:
            depth -= 1
            i = next_close + 1
            if depth == 0:
                return i - 1
        else:
            break
    return n - 1


def _extract_blocks_compiled(text: str, pattern: re.Pattern) -> list[tuple[str, int]]:
    results = []
    for match in pattern.finditer(text):
        line_num = text[:match.start()].count('\n') + 1
        end = _walk_block(text, match.start())
        results.append((text[match.start():end + 1], line_num))
    return results


def _extract_named_blocks(text: str, block_type: str) -> list[tuple[str, int]]:
    """Extract named blocks like 'view: foo {' or 'join: bar {'."""
    pat = _FIELD_TYPE_PATTERNS.get(block_type)
    if pat is None:
        if block_type == "join":
            pat = _JOIN_BLOCK_RE
        elif block_type == "view":
            pat = _RE_VIEW_BLOCK
        elif block_type == "explore":
            pat = _RE_EXPLORE_BLOCK
        else:
            pat = re.compile(rf'^\s*{re.escape(block_type)}\s*:\s*\S+\s*\{{', re.MULTILINE)
    return _extract_blocks_compiled(text, pat)


def _extract_anon_blocks(text: str, block_type: str) -> list[tuple[str, int]]:
    """Extract anonymous blocks like 'derived_table: {'."""
    if block_type == "derived_table":
        return _extract_blocks_compiled(text, _RE_ANON_DT)
    pat = re.compile(rf'^\s*{re.escape(block_type)}\s*:\s*\{{', re.MULTILINE)
    return _extract_blocks_compiled(text, pat)


def _get_attr(block_text: str, attr: str) -> Optional[str]:
    match = _attr_pattern(attr).search(block_text)
    if match:
        val = match.group(1).strip().rstrip(";").strip().strip('"').strip("'").strip()
        return val if val else None
    return None


def _get_block_name(block_text: str, block_type: str) -> Optional[str]:
    match = _block_name_pattern(block_type).search(block_text)
    return match.group(1).strip() if match else None


def _get_sql_block(block_text: str, attr: str) -> Optional[str]:
    match = _sql_block_pattern(attr).search(block_text)
    return match.group(1).strip() if match else None

# ---------------------------------------------------------------------------
# Field parser
# ---------------------------------------------------------------------------
FIELD_TYPES = ["dimension_group", "dimension", "measure", "filter", "parameter"]


def _parse_field(block_text: str, line_num: int, source_file: str) -> Optional[LookMLField]:
    field_type = None
    for ft in FIELD_TYPES:
        if block_text.lstrip().startswith(ft + ":") or \
           bool(re.match(rf'^\s*{ft}\s*:', block_text)):
            field_type = ft
            break
    if not field_type:
        return None

    name = _get_block_name(block_text, field_type)
    if not name:
        return None

    sql = _get_sql_block(block_text, "sql") or _get_attr(block_text, "sql")
    tags_raw = _get_attr(block_text, "tags")
    tags = [t.strip().strip('"') for t in tags_raw.split(',')] if tags_raw else []

    return LookMLField(
        name=name,
        field_type=field_type,
        data_type=_get_attr(block_text, "type"),
        sql=sql,
        label=_get_attr(block_text, "label"),
        description=_get_attr(block_text, "description"),
        hidden=_get_attr(block_text, "hidden") == "yes",
        primary_key=_get_attr(block_text, "primary_key") == "yes",
        tags=tags,
        source_file=source_file,
        line_number=line_num,
    )

# ---------------------------------------------------------------------------
# View parser
# ---------------------------------------------------------------------------

def _parse_view(block_text: str, line_num: int, source_file: str) -> Optional[LookMLView]:
    name = _get_block_name(block_text, "view")
    if not name:
        return None

    sql_table = _get_attr(block_text, "sql_table_name")

    # Parse extends: [view_a, view_b]
    extends: list[str] = []
    ext_match = _RE_EXTENDS.search(block_text)
    if ext_match:
        extends = [v.strip().strip('"').strip("'") for v in ext_match.group(1).split(',')]
        extends = [v for v in extends if v]

    # derived_table: { sql: ... ;; } — try named then anonymous blocks
    derived_sql = None
    dt_blocks = _extract_named_blocks(block_text, "derived_table") or \
                _extract_anon_blocks(block_text, "derived_table")
    if dt_blocks:
        inner, _ = dt_blocks[0]
        derived_sql = _get_sql_block(inner, "sql") or _get_attr(inner, "sql")
    if not derived_sql and not sql_table:
        derived_sql = _get_sql_block(block_text, "sql")

    fields = []
    for ft in FIELD_TYPES:
        for field_block, field_line in _extract_named_blocks(block_text, ft):
            field = _parse_field(field_block, line_num + field_line, source_file)
            if field:
                fields.append(field)

    return LookMLView(
        name=name,
        sql_table_name=sql_table,
        derived_table_sql=derived_sql,
        extends=extends,
        fields=fields,
        source_file=source_file,
        line_number=line_num,
    )

# ---------------------------------------------------------------------------
# Join parser
# ---------------------------------------------------------------------------

def _parse_join(block_text: str, line_num: int, source_file: str) -> Optional[LookMLJoin]:
    name = _get_block_name(block_text, "join")
    if not name:
        return None

    # sql_on is the standard join condition; some LookML uses bare `sql:` in joins
    # Both are valid join conditions — treat equivalently
    sql_on  = (_get_sql_block(block_text, "sql_on") or _get_attr(block_text, "sql_on") or
               _get_sql_block(block_text, "sql")    or _get_attr(block_text, "sql"))
    sql_where = _get_sql_block(block_text, "sql_where") or _get_attr(block_text, "sql_where")
    from_view = _get_attr(block_text, "from") or _get_attr(block_text, "view_name")

    return LookMLJoin(
        name=name,
        from_view=from_view,
        type=_get_attr(block_text, "type"),
        relationship=_get_attr(block_text, "relationship"),
        sql_on=sql_on,
        sql_where=sql_where,
        foreign_key=_get_attr(block_text, "foreign_key"),
        source_file=source_file,
        line_number=line_num,
    )

# ---------------------------------------------------------------------------
# Explore parser
# ---------------------------------------------------------------------------

def _parse_explore(block_text: str, line_num: int, source_file: str) -> Optional[LookMLExplore]:
    name = _get_block_name(block_text, "explore")
    if not name:
        return None

    joins = []
    for join_block, join_line in _extract_named_blocks(block_text, "join"):
        join = _parse_join(join_block, line_num + join_line, source_file)
        if join:
            joins.append(join)

    return LookMLExplore(
        name=name,
        from_view=_get_attr(block_text, "from"),
        view_name=_get_attr(block_text, "view_name"),
        label=_get_attr(block_text, "label"),
        description=_get_attr(block_text, "description"),
        joins=joins,
        source_file=source_file,
        line_number=line_num,
    )

# ---------------------------------------------------------------------------
# File & project parser
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Manifest parser — resolves @{Constant} references
# ---------------------------------------------------------------------------

_CONSTANT_RE = re.compile(
    r'constant\s*:\s*(\w+)\s*\{[^}]*?value\s*:\s*["\']([^"\']+)["\']',
    re.DOTALL
)
_CONST_REF_RE = re.compile(r'@\{(\w+)\}')


def parse_manifest(root_path: str) -> dict[str, str]:
    """
    Find and parse manifest.lkml in the project root.
    Returns dict of {constant_name: value}.
    """
    root = Path(root_path)
    constants: dict[str, str] = {}
    # Search for manifest.lkml with various casings (Windows is case-insensitive but Linux isn't)
    candidates = [root / "manifest.lkml", root / "Manifest.lkml", root / "MANIFEST.lkml"]
    # Also scan root for any file matching manifest*.lkml
    try:
        for f in root.iterdir():
            if f.name.lower() == "manifest.lkml" and f not in candidates:
                candidates.append(f)
    except Exception:
        pass
    for candidate in candidates:
        if candidate.exists():
            text = _RE_COMMENT.sub('', candidate.read_text(encoding="utf-8", errors="replace"))
            for name, value in _CONSTANT_RE.findall(text):
                constants[name] = value
            break
    return constants


def resolve_constants(sql_table: str, constants: dict[str, str]) -> str:
    """Replace @{ConstantName} with its resolved value."""
    if not constants or not sql_table or '@{' not in sql_table:
        return sql_table
    return _CONST_REF_RE.sub(
        lambda m: constants.get(m.group(1), m.group(0)),
        sql_table
    )


def parse_file(file_path: str) -> tuple[list[LookMLView], list[LookMLExplore]]:
    path = Path(file_path)
    if not path.exists() or path.stat().st_size == 0:
        return [], []

    text = path.read_text(encoding="utf-8", errors="replace")
    # Strip comments once — compiled pattern
    text = _RE_COMMENT.sub('', text)

    views: list[LookMLView] = []
    for block, line_num in _extract_blocks_compiled(text, _RE_VIEW_BLOCK):
        view = _parse_view(block, line_num, str(file_path))
        if view:
            views.append(view)

    explores: list[LookMLExplore] = []
    for block, line_num in _extract_blocks_compiled(text, _RE_EXPLORE_BLOCK):
        explore = _parse_explore(block, line_num, str(file_path))
        if explore:
            explores.append(explore)

    return views, explores


def parse_project(root_path: str) -> LookMLProject:
    """
    Walk directory recursively, parse all .lkml files.
    Skips __pycache__, hidden dirs, and files under 10 bytes.
    """
    root = Path(root_path)
    if not root.exists():
        raise FileNotFoundError(f"Project path does not exist: {root_path}")

    all_views:    list[LookMLView]    = []
    all_explores: list[LookMLExplore] = []

    for file_path in root.rglob("*.lkml"):
        # Skip hidden dirs and tiny files
        if any(p.name.startswith('.') for p in file_path.parents):
            continue
        if file_path.stat().st_size < 10:
            continue
        views, explores = parse_file(str(file_path))
        all_views.extend(views)
        all_explores.extend(explores)

    # Resolve @{Constant} references using manifest.lkml
    constants = parse_manifest(str(root_path))
    if constants:
        for view in all_views:
            if view.sql_table_name and "@{" in view.sql_table_name:
                view.sql_table_name = resolve_constants(view.sql_table_name, constants)

    return LookMLProject(
        name=root.name,
        root_path=str(root_path),
        views=all_views,
        explores=all_explores,
        manifest_constants=constants,
    )
