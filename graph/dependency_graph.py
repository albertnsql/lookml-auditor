"""
Dependency Graph Builder
------------------------
Builds a directed graph of relationships between LookML entities:
  - Explore → base view
  - Explore → joined views
  - View → fields (dimensions/measures)

Node types are stored as node attributes for filtering.
"""
from __future__ import annotations
from typing import Any
import networkx as nx

from lookml_parser.models import LookMLProject, LookMLView, LookMLExplore


NODE_TYPE = "node_type"   # attribute key


def build_graph(project: LookMLProject) -> nx.DiGraph:
    """
    Build and return a directed dependency graph for the project.

    Node naming convention:
        view:<view_name>
        explore:<explore_name>
        field:<view_name>.<field_name>

    Edge attributes:
        relationship: "base_view" | "join" | "has_field"
    """
    G = nx.DiGraph()

    # ── Add view nodes ────────────────────────────────────────────────────
    for view in project.views:
        node_id = f"view:{view.name}"
        G.add_node(node_id, **{
            NODE_TYPE: "view",
            "name": view.name,
            "source_file": view.source_file,
            "field_count": len(view.fields),
            "dimension_count": len(view.dimensions),
            "measure_count": len(view.measures),
        })

        # Add field nodes and edges view → field
        for field in view.fields:
            field_id = f"field:{view.name}.{field.name}"
            G.add_node(field_id, **{
                NODE_TYPE: "field",
                "name": field.name,
                "view": view.name,
                "field_type": field.field_type,
                "data_type": field.data_type,
                "sql": field.sql,
                "source_file": field.source_file,
                "hidden": field.hidden,
            })
            G.add_edge(node_id, field_id, relationship="has_field")

    # ── Add explore nodes ─────────────────────────────────────────────────
    for explore in project.explores:
        exp_id = f"explore:{explore.name}"
        G.add_node(exp_id, **{
            NODE_TYPE: "explore",
            "name": explore.name,
            "base_view": explore.base_view,
            "source_file": explore.source_file,
            "join_count": len(explore.joins),
        })

        # Edge: explore → base view
        base_view_id = f"view:{explore.base_view}"
        G.add_edge(exp_id, base_view_id, relationship="base_view")

        # Edge: explore → joined views
        for join in explore.joins:
            joined_view_id = f"view:{join.resolved_view}"
            G.add_edge(exp_id, joined_view_id, relationship="join", join_name=join.name)

    return G


# ---------------------------------------------------------------------------
# Graph query helpers
# ---------------------------------------------------------------------------

def get_nodes_by_type(G: nx.DiGraph, node_type: str) -> list[str]:
    return [n for n, d in G.nodes(data=True) if d.get(NODE_TYPE) == node_type]


def get_views_used_in_explores(G: nx.DiGraph) -> set[str]:
    """Return set of view node IDs that are referenced by at least one explore."""
    used = set()
    for u, v, data in G.edges(data=True):
        if data.get("relationship") in ("base_view", "join"):
            used.add(v)
    return used


def get_unused_views(G: nx.DiGraph) -> list[str]:
    all_views = set(get_nodes_by_type(G, "view"))
    used = get_views_used_in_explores(G)
    return sorted(all_views - used)


def get_broken_explore_refs(G: nx.DiGraph) -> list[dict[str, Any]]:
    """Explores pointing to view nodes that don't exist in the graph."""
    broken = []
    for u, v, data in G.edges(data=True):
        if data.get("relationship") in ("base_view", "join"):
            if v not in G.nodes:
                broken.append({
                    "explore": u,
                    "missing_view": v,
                    "relationship": data.get("relationship"),
                })
    return broken


def get_explore_view_map(G: nx.DiGraph) -> dict[str, list[str]]:
    """Return mapping of explore → list of view node IDs it touches."""
    result: dict[str, list[str]] = {}
    for n, d in G.nodes(data=True):
        if d.get(NODE_TYPE) == "explore":
            neighbors = [
                v for _, v, ed in G.out_edges(n, data=True)
                if ed.get("relationship") in ("base_view", "join")
            ]
            result[n] = neighbors
    return result


def graph_summary(G: nx.DiGraph) -> dict[str, int]:
    return {
        "total_nodes": G.number_of_nodes(),
        "total_edges": G.number_of_edges(),
        "views": len(get_nodes_by_type(G, "view")),
        "explores": len(get_nodes_by_type(G, "explore")),
        "fields": len(get_nodes_by_type(G, "field")),
    }
