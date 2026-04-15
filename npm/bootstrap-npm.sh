#!/usr/bin/env bash
# bootstrap-npm.sh
#
# One-time script to create all 6 package names on npmjs.com so that
# Trusted Publishing can be configured per-package afterwards.
#
# Usage (two options):
#
# Option A — Granular token with "bypass 2FA" (recommended, no OTP needed):
#   NPM_TOKEN=npm_xxx bash npm/bootstrap-npm.sh
#
# Option B — Interactive login + OTP:
#   npm login
#   bash npm/bootstrap-npm.sh
#
# How to get a bypass-2FA token:
#   npmjs.com → Account Settings → Access Tokens
#   → Generate New Token → Granular Access Token
#   → Packages: Read and write
#   → Two-factor authentication: ✅ "Bypass two-factor authentication"
#   → Generate → copy the token
#
# After this bootstrap, configure Trusted Publishing for each package at:
#   https://www.npmjs.com/package/@projanvil/PACKAGE_NAME/access
# Set: Repo owner=ProjAnvil, Repo=Belt, Workflow=release.yml
# Then delete this token — CI will use OIDC forever after.

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

# Auth: prefer NPM_TOKEN env var (bypass-2FA token), fall back to OTP
if [[ -n "$NPM_TOKEN" ]]; then
  echo "    Using NPM_TOKEN for authentication (bypass 2FA)."
  # Write token to a temp .npmrc scoped to this script
  NPMRC_TMP="$(mktemp)"
  echo "//registry.npmjs.org/:_authToken=${NPM_TOKEN}" > "$NPMRC_TMP"
  NPM_EXTRA_ARGS=(--userconfig "$NPMRC_TMP")
  echo ""
else
  echo "    No NPM_TOKEN found — falling back to OTP."
  read -rp "    Enter your npm 2FA OTP code: " OTP
  NPM_EXTRA_ARGS=(--otp="$OTP")
  echo ""
fi

# Cleanup temp .npmrc on exit
cleanup() {
  [[ -n "$NPMRC_TMP" ]] && rm -f "$NPMRC_TMP"
  # Reset package.json versions back to 0.0.0
  for PKG in "${PACKAGES[@]}"; do
    DIR="$ROOT/$PKG"
    node -e "
      const fs = require('fs');
      const p = JSON.parse(fs.readFileSync('$DIR/package.json', 'utf8'));
      p.version = '0.0.0';
      if (p.optionalDependencies) {
        Object.keys(p.optionalDependencies).forEach(k => p.optionalDependencies[k] = '0.0.0');
      }
      fs.writeFileSync('$DIR/package.json', JSON.stringify(p, null, 2) + '\n');
    " 2>/dev/null || true
  done
}
trap cleanup EXIT

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
    if [[ ! -f "$TOUCH_FILE" ]] || grep -q "placeholder" "$TOUCH_FILE" 2>/dev/null; then
      printf '\x7fELF' > "$TOUCH_FILE"  # minimal non-empty placeholder
      [[ "$PKG" != *"win32"* ]] && chmod +x "$TOUCH_FILE"
    fi
  fi

  # If OTP expires mid-run, prompt again
  if ! (cd "$DIR" && npm publish --access public "${NPM_EXTRA_ARGS[@]}" 2>&1); then
    if [[ -z "$NPM_TOKEN" ]]; then
      echo "   OTP may have expired. Enter a fresh OTP:"
      read -rp "   New OTP: " OTP
      NPM_EXTRA_ARGS=(--otp="$OTP")
      (cd "$DIR" && npm publish --access public "${NPM_EXTRA_ARGS[@]}")
    else
      echo "   ✗ Failed. Check your NPM_TOKEN has 'bypass 2FA' and 'read+write' permissions."
      exit 1
    fi
  fi
  echo "   ✓ @projanvil/$PKG@0.0.1 published"
done

echo ""
echo "✓ All 6 packages created on npmjs.com."
echo ""
echo "Next steps:"
echo "  1. Open each package settings and add Trusted Publisher:"
for PKG in "${PACKAGES[@]}"; do
  echo "     https://www.npmjs.com/package/@projanvil/$PKG/access"
done
echo "  2. Set: Repo owner=ProjAnvil  Repo=Belt  Workflow=release.yml"
echo "  3. Delete the bypass-2FA token — CI will use OIDC from now on."
echo "  4. Push a version tag:  git tag v0.1.0 && git push origin v0.1.0"
