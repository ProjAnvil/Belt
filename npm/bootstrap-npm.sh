#!/usr/bin/env bash
# bootstrap-npm.sh
#
# One-time script to create all 6 package names on npmjs.com so that
# Trusted Publishing can be configured per-package afterwards.
#
# Run this ONCE from the repo root, after `npm login`:
#   npm login
#   bash npm/bootstrap-npm.sh
#
# After this, configure Trusted Publishing for each package at:
#   https://www.npmjs.com/package/@projanvil/belt/access
#   https://www.npmjs.com/package/@projanvil/belt-darwin-arm64/access
#   ... (all 6 packages)
# Then future publishes will use OIDC via GitHub Actions (no token needed).

set -e

PACKAGES=(
  "belt"
  "belt-darwin-arm64"
  "belt-darwin-x64"
  "belt-linux-x64"
  "belt-linux-arm64"
  "belt-win32-x64"
)

ROOT="$(cd "$(dirname "$0")" && pwd)"

echo "==> Bootstrapping npm packages for @projanvil/belt..."
echo "    This publishes version 0.0.1 (placeholder) to create each package name."
echo ""

for PKG in "${PACKAGES[@]}"; do
  DIR="$ROOT/$PKG"
  echo "--> Publishing @projanvil/$PKG..."

  # Stamp version 0.0.1 temporarily
  node -e "
    const fs = require('fs');
    const p = JSON.parse(fs.readFileSync('$DIR/package.json', 'utf8'));
    p.version = '0.0.1';
    if (p.optionalDependencies) {
      Object.keys(p.optionalDependencies).forEach(k => p.optionalDependencies[k] = '0.0.1');
    }
    fs.writeFileSync('$DIR/package.json', JSON.stringify(p, null, 2) + '\n');
  "

  # For platform packages that need a bin placeholder
  if [[ "$PKG" != "belt" ]]; then
    if [[ "$PKG" == *"win32"* ]]; then
      TOUCH_FILE="$DIR/bin/belt.exe"
    else
      TOUCH_FILE="$DIR/bin/belt"
    fi
    if [[ ! -f "$TOUCH_FILE" ]]; then
      echo "   (creating placeholder binary: $TOUCH_FILE)"
      echo "placeholder" > "$TOUCH_FILE"
      [[ "$PKG" != *"win32"* ]] && chmod +x "$TOUCH_FILE"
    fi
  fi

  (cd "$DIR" && npm publish --access public)
  echo "   ✓ @projanvil/$PKG@0.0.1 published"
done

echo ""
echo "✓ All 6 packages created on npmjs.com."
echo ""
echo "Next steps:"
echo "  1. Open each package on npmjs.com and configure Trusted Publishing:"
for PKG in "${PACKAGES[@]}"; do
  echo "     https://www.npmjs.com/package/@projanvil/$PKG/access"
done
echo "  2. Set: Repo owner=ProjAnvil, Repo=Belt, Workflow=release.yml"
echo "  3. Then push a version tag to trigger CI — no token needed."
