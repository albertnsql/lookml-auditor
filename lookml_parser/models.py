"""
Core data models representing parsed LookML entities.
All parsed objects are immutable Pydantic models for safety and serializability.
"""
from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field


class LookMLField(BaseModel):
    name: str
    field_type: str          # "dimension" | "measure" | "dimension_group" | "filter"
    data_type: Optional[str] = None
    sql: Optional[str] = None
    label: Optional[str] = None
    description: Optional[str] = None
    hidden: bool = False
    primary_key: bool = False          # NEW: tracks primary_key: yes
    tags: list[str] = Field(default_factory=list)
    source_file: str = ""
    line_number: int = 0


class LookMLView(BaseModel):
    name: str
    sql_table_name: Optional[str] = None
    derived_table_sql: Optional[str] = None
    extends: list[str] = Field(default_factory=list)
    fields: list[LookMLField] = Field(default_factory=list)
    source_file: str = ""
    line_number: int = 0

    @property
    def dimensions(self) -> list[LookMLField]:
        return [f for f in self.fields if f.field_type in ("dimension", "dimension_group")]

    @property
    def measures(self) -> list[LookMLField]:
        return [f for f in self.fields if f.field_type == "measure"]

    @property
    def field_names(self) -> set[str]:
        return {f.name for f in self.fields}

    @property
    def is_derived_table(self) -> bool:
        return self.derived_table_sql is not None

    @property
    def has_primary_key(self) -> bool:
        return any(f.primary_key for f in self.fields)

    @property
    def primary_key_field(self) -> Optional[LookMLField]:
        for f in self.fields:
            if f.primary_key:
                return f
        return None


class LookMLJoin(BaseModel):
    name: str
    from_view: Optional[str] = None
    type: Optional[str] = None
    relationship: Optional[str] = None
    sql_on: Optional[str] = None
    sql_where: Optional[str] = None
    foreign_key: Optional[str] = None
    source_file: str = ""
    line_number: int = 0

    @property
    def resolved_view(self) -> str:
        return self.from_view or self.name


class LookMLExplore(BaseModel):
    name: str
    from_view: Optional[str] = None
    view_name: Optional[str] = None
    label: Optional[str] = None
    description: Optional[str] = None
    joins: list[LookMLJoin] = Field(default_factory=list)
    source_file: str = ""
    line_number: int = 0

    @property
    def base_view(self) -> str:
        return self.from_view or self.view_name or self.name


class LookMLProject(BaseModel):
    """Top-level container for an entire parsed LookML project."""
    name: str = "unnamed_project"
    root_path: str = ""
    views: list[LookMLView] = Field(default_factory=list)
    explores: list[LookMLExplore] = Field(default_factory=list)
    manifest_constants: dict[str, str] = Field(default_factory=dict)

    @property
    def view_map(self) -> dict[str, LookMLView]:
        return {v.name: v for v in self.views}

    @property
    def explore_map(self) -> dict[str, LookMLExplore]:
        return {e.name: e for e in self.explores}

    @property
    def derived_table_views(self) -> list[LookMLView]:
        return [v for v in self.views if v.is_derived_table]

    @property
    def all_files(self) -> set[str]:
        files = {v.source_file for v in self.views}
        files.update(e.source_file for e in self.explores)
        return files
