#!/usr/bin/env python3

import argparse
import sys

GREETINGS = {
    "en": "Hello",
    "zh-cn": "你好",
    "es": "Hola",
    "fr": "Bonjour",
    "ja": "こんにちは",
    "de": "Hallo",
}


def main():
    parser = argparse.ArgumentParser(
        prog="greet", description="hello-belt greeting script"
    )
    parser.add_argument("--name", default="World", help="Name to greet")
    parser.add_argument(
        "--lang", default="en", choices=list(GREETINGS.keys()), help="Greeting language"
    )
    parser.add_argument(
        "--list-langs", action="store_true", help="List available languages"
    )
    args = parser.parse_args()

    if args.list_langs:
        print("Supported greeting languages:")
        for code, word in GREETINGS.items():
            print(f"  {code:8s}  {word}")
        return

    greeting = GREETINGS.get(args.lang, "Hello")
    print(f"{greeting}, {args.name}! 👋")
    print(f"(Powered by hello-belt — a Belt AI-native app)")


if __name__ == "__main__":
    main()
