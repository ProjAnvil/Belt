#!/usr/bin/env python3
"""
test-gen-app - [Brief description of what this script does]

Usage:
    python3 run.py run [args...]
    python3 run.py help

This script is invoked by the test-gen-app skill (SKILL.md).
It is language-agnostic and shared across all locale variants.
"""

import sys
import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        prog="test-gen-app",
        description="test-gen-app - replace this with your app description",
    )
    subparsers = parser.add_subparsers(dest="command", help="Subcommand")

    # run subcommand
    run_parser = subparsers.add_parser("run", help="[Describe what run does]")
    run_parser.add_argument(
        "target",
        nargs="?",
        default=".",
        help="[Describe the argument, e.g. path to analyze]",
    )
    run_parser.add_argument(
        "--output",
        default=None,
        help="Output file path (default: stdout)",
    )

    args = parser.parse_args()

    if args.command is None or args.command == "help":
        parser.print_help()
        return

    if args.command == "run":
        run(args)
    else:
        print(f"Unknown command: {args.command}", file=sys.stderr)
        parser.print_help()
        sys.exit(1)


def run(args):
    """
    Primary logic for the 'run' subcommand.
    Replace this with your actual implementation.
    """
    target = Path(args.target)

    # Validate input
    if not target.exists():
        print(f"Error: '{target}' does not exist.", file=sys.stderr)
        sys.exit(1)

    # ----- Your logic here -----
    result = {
        "status": "success",
        "target": str(target),
        "summary": f"Processed {target}",
        # Add your result fields here
    }
    # ---------------------------

    # Output
    output = format_result(result)
    if args.output:
        Path(args.output).write_text(output)
        print(f"Output written to {args.output}")
    else:
        print(output)


def format_result(result: dict) -> str:
    """Format the result dict as readable output."""
    lines = [
        "## Result",
        "",
        f"**Status**: {result['status']}",
        f"**Summary**: {result['summary']}",
        "",
        "### Details",
        json.dumps(result, indent=2, ensure_ascii=False),
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    main()
