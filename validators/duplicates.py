"""
Validator: Duplicate Definitions

Case 1/3 fix: Same view name in different files.
  - Same physical file path → ERROR
  - Different file paths with same filename (different folders) → WARNING
  - Key fix: use the full source_file string for comparison, not Path().parent
    (Path().parent breaks on Windows-style paths running on Linux)

Case 2 fix: dimension + dimension_group same base name → WARNING not ERROR.
  LookML generates runtime sub-fields (_raw, _date etc.) that shadow same-named
  plain dimensions. This is technically valid — downgraded to WARNING.
"""
from __future__ import annotations
from collections import defaultdict
from pathlib import Path
from lookml_parser.models import LookMLProject
from .issue import Issue, IssueCategory, Severity


def _folder_of(source_file: str) -> str:
    """
    Extract folder name from source_file in a cross-platform way.
    Handles both Unix ('/') and Windows ('\\') separators.
    Returns the immediate parent directory name, or '' if none.
    """
    # Normalise separators
    norm = source_file.replace("\\", "/")
    parts = norm.split("/")
    # parts[-1] = filename, parts[-2] = immediate parent folder (if any)
    if len(parts) >= 2:
        return parts[-2]
    return ""


def _full_path_norm(source_file: str) -> str:
    """Normalised full path for exact-file comparison."""
    return source_file.replace("\\", "/").lower().strip()


def check_duplicates(project: LookMLProject) -> list[Issue]:
    issues = []

    # ── Duplicate view names ──────────────────────────────────────────────
    view_occurrences: dict[str, list[str]] = defaultdict(list)
    for view in project.views:
        view_occurrences[view.name].append(view.source_file)

    for view_name, files in view_occurrences.items():
        if len(files) <= 1:
            continue

        # Deduplicate by normalised full path
        unique_paths = {_full_path_norm(f) for f in files}
        if len(unique_paths) <= 1:
            # All occurrences point to the exact same file — parser read it twice
            continue

        # Compare immediate parent folder names (cross-platform)
        unique_folders = {_folder_of(f) for f in files}
        same_folder    = len(unique_folders) == 1

        severity = Severity.ERROR if same_folder else Severity.WARNING
        unique_filenames = {f.replace("\\", "/").split("/")[-1] for f in files}

        issues.append(Issue(
            category=IssueCategory.DUPLICATE,
            severity=severity,
            message=(
                f"View '{view_name}' is defined {len(unique_paths)} times "
                f"across {'the same folder' if same_folder else 'different folders'}: "
                f"{', '.join(sorted(unique_filenames))}"
            ),
            object_type="view",
            object_name=view_name,
            source_file=files[0],
            suggestion=(
                "Remove or rename the duplicate — same-folder duplicates always conflict in Looker."
                if same_folder else
                "Views with the same name in different folders may be intentional per-environment "
                "overrides. Verify only one is active per model file."
            ),
        ))

    # ── Duplicate explore names ───────────────────────────────────────────
    explore_occurrences: dict[str, list[str]] = defaultdict(list)
    for explore in project.explores:
        explore_occurrences[explore.name].append(explore.source_file)

    for exp_name, files in explore_occurrences.items():
        if len(files) <= 1:
            continue
        unique_paths = {_full_path_norm(f) for f in files}
        if len(unique_paths) <= 1:
            continue
        unique_filenames = {f.replace("\\", "/").split("/")[-1] for f in files}
        same_file  = len(unique_paths) == 1
        severity   = Severity.ERROR if same_file else Severity.WARNING
        issues.append(Issue(
            category=IssueCategory.DUPLICATE,
            severity=severity,
            message=(
                f"Explore '{exp_name}' is defined {len(unique_paths)} times "
                f"across files: {', '.join(sorted(unique_filenames))}"
            ),
            object_type="explore",
            object_name=exp_name,
            source_file=files[0],
            suggestion=(
                "Remove duplicate explore from the same file."
                if same_file else
                "Duplicate explore across model files may be intentional. "
                "Verify only one definition is active in production."
            ),
        ))

    # ── Duplicate fields within a view ───────────────────────────────────
    # Case 2: dimension_group + dimension same base name → WARNING (valid LookML pattern)
    # Pure same-type duplicates → ERROR
    # Case 4: views using extends can legitimately re-define fields from the base view
    # Also: skip views whose source file contains multiple view blocks —
    #        fields may belong to different views within the same file
    _file_view_count: dict[str, int] = defaultdict(int)
    for view in project.views:
        if view.source_file:
            _file_view_count[_full_path_norm(view.source_file)] += 1

    for view in project.views:
        # If this view uses extends:, skip — field overrides are standard LookML
        if view.extends:
            continue

        # If this file has multiple view blocks, skip — fields may span views
        if view.source_file and _file_view_count.get(_full_path_norm(view.source_file), 0) > 1:
            continue

        field_map: dict[str, list[str]] = defaultdict(list)
        for field in view.fields:
            field_map[field.name].append(field.field_type)

        for field_name, types in field_map.items():
            if len(types) <= 1:
                continue
            type_set = set(types)
            if "dimension_group" in type_set:
                # dimension_group + plain dimension with same base name is a known
                # LookML pattern — the group generates sub-fields like _raw, _date etc.
                issues.append(Issue(
                    category=IssueCategory.DUPLICATE,
                    severity=Severity.WARNING,
                    message=(
                        f"Field '{field_name}' in view '{view.name}' has both a dimension "
                        f"and a dimension_group with the same base name. "
                        f"LookML will generate sub-fields (e.g. {field_name}_raw, "
                        f"{field_name}_date) which may overlap with the plain dimension."
                    ),
                    object_type="field",
                    object_name=f"{view.name}.{field_name}",
                    source_file=view.source_file,
                    suggestion=(
                        f"Rename the plain dimension or the dimension_group in view "
                        f"'{view.name}' to avoid ambiguity at query time."
                    ),
                ))
            else:
                # True duplicate — same name, same type
                issues.append(Issue(
                    category=IssueCategory.DUPLICATE,
                    severity=Severity.ERROR,
                    message=(
                        f"Field '{field_name}' is defined {len(types)} times "
                        f"in view '{view.name}' (type: {types[0]})"
                    ),
                    object_type="field",
                    object_name=f"{view.name}.{field_name}",
                    source_file=view.source_file,
                    suggestion=(
                        f"Remove the duplicate '{field_name}' definition "
                        f"in view '{view.name}'."
                    ),
                ))

    return issues
