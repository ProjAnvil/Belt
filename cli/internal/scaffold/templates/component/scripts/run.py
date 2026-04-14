#!/usr/bin/env python3
import argparse
import sys


def main():
    parser = argparse.ArgumentParser(description="__COMPONENT_NAME__")
    sub = parser.add_subparsers(dest="command", required=True)

    args = parser.parse_args()
    print(f"Command: {args.command}")


if __name__ == "__main__":
    main()
