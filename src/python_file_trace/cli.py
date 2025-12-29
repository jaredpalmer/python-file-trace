"""Command-line interface for python-file-trace."""

import argparse
import json
import sys
from pathlib import Path

from . import __version__, python_file_trace
from .types import TraceOptions


def main(argv: list[str] | None = None) -> int:
    """
    Main entry point for the CLI.

    Args:
        argv: Command line arguments (defaults to sys.argv[1:]).

    Returns:
        Exit code (0 for success, non-zero for failure).
    """
    parser = argparse.ArgumentParser(
        prog="python-file-trace",
        description="Trace Python file dependencies to determine which files are needed to run an application.",
    )

    parser.add_argument(
        "files",
        nargs="+",
        help="Entry point file(s) to trace",
    )

    parser.add_argument(
        "--base",
        type=Path,
        default=None,
        help="Base directory for resolving relative paths (default: current directory)",
    )

    parser.add_argument(
        "--ignore",
        action="append",
        default=[],
        help="Glob pattern(s) to ignore (can be specified multiple times)",
    )

    parser.add_argument(
        "--include-stdlib",
        action="store_true",
        default=False,
        help="Include standard library files in the output",
    )

    parser.add_argument(
        "--no-site-packages",
        action="store_true",
        default=False,
        help="Exclude site-packages from the output",
    )

    parser.add_argument(
        "--follow-dynamic",
        action="store_true",
        default=False,
        help="Attempt to follow dynamic imports (__import__, importlib)",
    )

    parser.add_argument(
        "--max-depth",
        type=int,
        default=None,
        help="Maximum depth to trace (default: unlimited)",
    )

    parser.add_argument(
        "--json",
        action="store_true",
        default=False,
        help="Output results as JSON",
    )

    parser.add_argument(
        "--relative",
        action="store_true",
        default=False,
        help="Output paths relative to base directory",
    )

    parser.add_argument(
        "--show-reasons",
        action="store_true",
        default=False,
        help="Show why each file was included",
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    args = parser.parse_args(argv)

    # Build options
    options = TraceOptions(
        base=args.base,
        ignore=args.ignore,
        include_stdlib=args.include_stdlib,
        include_site_packages=not args.no_site_packages,
        follow_dynamic_imports=args.follow_dynamic,
        max_depth=args.max_depth,
    )

    # Run trace
    try:
        result = python_file_trace(args.files, options)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    # Output results
    if args.json:
        output = _format_json(result, args.relative, args.show_reasons)
        print(output)
    else:
        _format_text(result, args.relative, args.show_reasons)

    # Print warnings to stderr
    for warning in result.warnings:
        print(f"Warning: {warning}", file=sys.stderr)

    return 0


def _format_json(result, relative: bool, show_reasons: bool) -> str:
    """Format the result as JSON."""
    if relative:
        files = sorted(result.relative_file_list())
    else:
        files = sorted(result.file_list)

    output: dict = {"files": files}

    if show_reasons:
        reasons = {}
        for file_path, reason in result.reasons.items():
            if relative:
                try:
                    file_path = str(Path(file_path).relative_to(result.base))
                except ValueError:
                    pass

            reasons[file_path] = {
                "type": reason.type.value,
                "parents": sorted(reason.parents),
                "ignored": reason.ignored,
            }
            if reason.module_name:
                reasons[file_path]["module"] = reason.module_name

        output["reasons"] = reasons

    if result.warnings:
        output["warnings"] = result.warnings

    return json.dumps(output, indent=2)


def _format_text(result, relative: bool, show_reasons: bool) -> None:
    """Format the result as text output."""
    if relative:
        files = sorted(result.relative_file_list())
    else:
        files = sorted(result.file_list)

    if show_reasons:
        for file_path in files:
            abs_path = file_path
            if relative:
                abs_path = str(result.base / file_path)

            reason = result.reasons.get(abs_path)
            if reason:
                reason_str = f"[{reason.type.value}]"
                if reason.parents:
                    parents = ", ".join(sorted(reason.parents)[:3])
                    if len(reason.parents) > 3:
                        parents += f" (+{len(reason.parents) - 3} more)"
                    reason_str += f" from: {parents}"
                print(f"{file_path}  {reason_str}")
            else:
                print(file_path)
    else:
        for file_path in files:
            print(file_path)


if __name__ == "__main__":
    sys.exit(main())
