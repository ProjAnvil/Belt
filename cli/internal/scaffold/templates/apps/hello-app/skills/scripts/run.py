#!/usr/bin/env python3
"""
__APP_NAME__ - Sample Belt app that demonstrates skill + script structure.

Usage:
    python3 run.py greet [name]
    python3 run.py help

This script is invoked by the __APP_NAME__ skill (SKILL.md).
It is language-agnostic and shared across all locale variants.
"""

import sys
import argparse
import json
from pathlib import Path


# ---------------------------------------------------------------------------
# App configuration
# ---------------------------------------------------------------------------


def load_app_config() -> dict:
    """
    Read app.json from the skill's reference directory to obtain runtime configuration.
    app.json is copied there by install.sh / install.ps1 at install time:
        ~/.claude/skills/__APP_NAME__/reference/app.json
    """
    config_path = Path(__file__).parent.parent / "reference" / "app.json"
    if config_path.exists():
        return json.loads(config_path.read_text())
    return {}


def get_app_dir(config: dict) -> Path:
    """Return the resolved app data directory, creating it if needed."""
    raw = config.get("app_dir", "~/.claude/__APP_NAME__")
    app_dir = Path(raw).expanduser()
    app_dir.mkdir(parents=True, exist_ok=True)
    return app_dir


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


def cmd_greet(name: str, app_dir: Path) -> None:
    """Print a personalised greeting and record it in the app directory."""
    greeting = f"👋 Hello, {name}! Greetings from __APP_NAME__."
    print(greeting)

    # Example: persist a log of greetings to the app data directory.
    log_path = app_dir / "greetings.log"
    with log_path.open("a") as f:
        f.write(greeting + "\n")


def cmd_help() -> None:
    print(
        "Usage:\n"
        "  run.py greet [name]   Greet a person (default: World)\n"
        "  run.py help           Show this message\n"
    )


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        prog="run.py",
        description="__APP_NAME__ — sample Belt skill script",
        add_help=False,
    )
    parser.add_argument("subcommand", nargs="?", default="greet")
    parser.add_argument("args", nargs="*")
    parsed = parser.parse_args()

    config = load_app_config()
    app_dir = get_app_dir(config)

    if parsed.subcommand == "greet":
        name = parsed.args[0] if parsed.args else "World"
        cmd_greet(name, app_dir)
    elif parsed.subcommand == "help":
        cmd_help()
    else:
        print(f"Unknown subcommand: {parsed.subcommand}", file=sys.stderr)
        cmd_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
