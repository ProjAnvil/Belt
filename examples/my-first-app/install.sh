#!/bin/bash

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

detect_os() {
    if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
        echo "windows"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    else
        echo "linux"
    fi
}

OS_TYPE=$(detect_os)
LANG_CODE="en"

while [[ $# -gt 0 ]]; do
    case $1 in
        --lang=*) LANG_CODE="${1#*=}"; shift ;;
        --lang) LANG_CODE="$2"; shift 2 ;;
        -h|--help)
            echo "Usage: $0 [--lang=en|zh-cn]"
            exit 0 ;;
        *) echo -e "${RED}Unknown option: $1${NC}"; exit 1 ;;
    esac
done

if [[ "$LANG_CODE" != "en" && "$LANG_CODE" != "zh-cn" ]]; then
    echo -e "${RED}Error: Unsupported language '$LANG_CODE'${NC}"
    echo "Supported: en, zh-cn"
    exit 1
fi

APP_NAME="my-first-app"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

SKILL_SRC="$SCRIPT_DIR/skills/$LANG_CODE/$APP_NAME"
SCRIPTS_SRC="$SCRIPT_DIR/skills/scripts/$APP_NAME"
AGENT_SRC="$SCRIPT_DIR/agents/$LANG_CODE/$APP_NAME.md"

CLAUDE_DIR="$HOME/.claude"
CLAUDE_SKILLS_DIR="$CLAUDE_DIR/skills"
CLAUDE_AGENTS_DIR="$CLAUDE_DIR/agents"

echo -e "${BLUE}Installing: $APP_NAME (lang: $LANG_CODE)${NC}"

mkdir -p "$CLAUDE_SKILLS_DIR/$APP_NAME" "$CLAUDE_AGENTS_DIR"

link_or_copy() {
    local src="$1"
    local dst="$2"
    local label="$3"

    if [ "$OS_TYPE" = "windows" ]; then
        rm -rf "$dst"
        cp -r "$src" "$dst"
        echo -e "${GREEN}  copied${NC} $label"
    else
        if [ -L "$dst" ] && [ "$(readlink "$dst")" = "$src" ]; then
            echo -e "${GREEN}  ok${NC} $label (already linked)"
        else
            [ -L "$dst" ] && rm "$dst"
            ln -s "$src" "$dst"
            echo -e "${GREEN}  linked${NC} $label"
        fi
    fi
}

if [ -d "$SKILL_SRC" ]; then
    for f in "$SKILL_SRC"/*; do
        fname=$(basename "$f")
        link_or_copy "$f" "$CLAUDE_SKILLS_DIR/$APP_NAME/$fname" "$APP_NAME/$fname"
    done
else
    echo -e "${RED}Skill source not found: $SKILL_SRC${NC}"; exit 1
fi

if [ -d "$SCRIPTS_SRC" ]; then
    link_or_copy "$SCRIPTS_SRC" "$CLAUDE_SKILLS_DIR/$APP_NAME/scripts" "$APP_NAME/scripts"
fi

if [ -f "$AGENT_SRC" ]; then
    link_or_copy "$AGENT_SRC" "$CLAUDE_AGENTS_DIR/$APP_NAME.md" "$APP_NAME.md"
else
    echo -e "${YELLOW}  (no agent found at $AGENT_SRC — skipping)${NC}"
fi

echo ""
echo -e "${GREEN}Done! $APP_NAME installed.${NC}"
echo ""
echo "Claude Code will now recognize:"
echo "  Skill:  $APP_NAME  (invoke via /$APP_NAME)"
echo "  Agent:  @$APP_NAME"
echo ""
echo "To uninstall:"
echo "  rm -rf $CLAUDE_SKILLS_DIR/$APP_NAME"
echo "  rm -f  $CLAUDE_AGENTS_DIR/$APP_NAME.md"
