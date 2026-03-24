"""
LookML Auditor — CLI Entry Point
Usage:
    python main.py audit /path/to/lookml/project
    python main.py audit /path/to/lookml/project --json-out report.json
"""
from __future__ import annotations
import sys
import os
import json
import argparse
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lookml_parser import parse_project
from validators import run_all_checks, compute_health_score, Severity
from reporting import build_json_report

try:
    from rich.console import Console
    from rich.table import Table
    from rich import box
    RICH = True
except ImportError:
    RICH = False


def cli_audit(project_path: str, json_out: str | None = None):
    if RICH:
        _rich_audit(project_path, json_out)
    else:
        _plain_audit(project_path, json_out)


def _rich_audit(project_path: str, json_out: str | None):
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich import box

    console = Console()

    console.print(f"\n[bold cyan]⬡ LookML Auditor[/] — parsing [dim]{project_path}[/]\n")

    try:
        project = parse_project(project_path)
    except FileNotFoundError as e:
        console.print(f"[bold red]Error:[/] {e}")
        sys.exit(1)

    issues = run_all_checks(project)
    score  = compute_health_score(issues)

    score_color = "green" if score >= 85 else "yellow" if score >= 60 else "red"

    console.print(Panel(
        f"[bold {score_color}]{score}/100[/]  ·  "
        f"[dim]{len(project.views)} views  |  {len(project.explores)} explores  |  "
        f"{sum(len(v.fields) for v in project.views)} fields[/]",
        title="[bold]Health Score[/]",
        border_style="dim",
    ))

    if not issues:
        console.print("[bold green]✓ No issues found![/]\n")
    else:
        table = Table(box=box.SIMPLE_HEAD, show_footer=False, highlight=True)
        table.add_column("Severity", style="dim", width=10)
        table.add_column("Category", width=22)
        table.add_column("Object",   width=30)
        table.add_column("Message",  width=60)

        for issue in issues:
            sev_fmt = {
                "error":   "[bold red]ERROR[/]",
                "warning": "[bold yellow]WARN[/]",
                "info":    "[bold blue]INFO[/]",
            }.get(issue.severity, issue.severity)

            table.add_row(sev_fmt, issue.category.value, issue.object_name, issue.message)

        console.print(table)

        errors   = sum(1 for i in issues if i.severity == Severity.ERROR)
        warnings = sum(1 for i in issues if i.severity == Severity.WARNING)
        infos    = sum(1 for i in issues if i.severity == Severity.INFO)
        console.print(
            f"[bold red]{errors} errors[/]  "
            f"[bold yellow]{warnings} warnings[/]  "
            f"[bold blue]{infos} info[/]\n"
        )

    if json_out:
        report = build_json_report(project, issues, output_path=json_out)
        console.print(f"[dim]JSON report written to:[/] [cyan]{json_out}[/]\n")


def _plain_audit(project_path: str, json_out: str | None):
    try:
        project = parse_project(project_path)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)

    issues = run_all_checks(project)
    score  = compute_health_score(issues)

    print(f"\nLookML Auditor — {project.name}")
    print(f"Health Score: {score}/100")
    print(f"Views: {len(project.views)}  Explores: {len(project.explores)}  Fields: {sum(len(v.fields) for v in project.views)}")
    print(f"Issues: {len(issues)}\n")

    for issue in issues:
        print(f"[{issue.severity.upper()}] {issue.category.value} | {issue.object_name} | {issue.message}")

    if json_out:
        build_json_report(project, issues, output_path=json_out)
        print(f"\nJSON report written to: {json_out}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="lookml-auditor", description="LookML static analysis tool")
    sub = parser.add_subparsers(dest="command")

    audit_cmd = sub.add_parser("audit", help="Audit a LookML project")
    audit_cmd.add_argument("path", help="Path to LookML project root")
    audit_cmd.add_argument("--json-out", "-o", help="Write JSON report to file", default=None)

    args = parser.parse_args()

    if args.command == "audit":
        cli_audit(args.path, args.json_out)
    else:
        parser.print_help()
