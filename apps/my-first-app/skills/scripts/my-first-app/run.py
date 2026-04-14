#!/usr/bin/env python3
"""Entry point script for the my-first-app Belt app."""

import sys
import argparse


def main():
    parser = argparse.ArgumentParser(
        prog="my-first-app",
        description="my-first-app - replace this with your app description",
    )
    parser.add_argument("command", nargs="?", default="help", help="Subcommand to run")
    parser.add_argument("args", nargs="*", help="Additional arguments")
    args = parser.parse_args()

    if args.command == "help" or args.command is None:
        parser.print_help()
        return

    if args.command == "run":
        run(args.args)
    else:
        print(f"Unknown command: {args.command}", file=sys.stderr)
        parser.print_help()
        sys.exit(1)


def run(args):
    print(f"my-first-app run: {' '.join(args) if args else '(no args)'}")


if __name__ == "__main__":
    main()
