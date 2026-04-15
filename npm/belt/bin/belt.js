#!/usr/bin/env node
"use strict";

const { execFileSync } = require("child_process");
const os = require("os");

const PLATFORM_MAP = {
  "darwin-arm64": "@projanvil/belt-darwin-arm64",
  "darwin-x64":   "@projanvil/belt-darwin-x64",
  "linux-x64":    "@projanvil/belt-linux-x64",
  "linux-arm64":  "@projanvil/belt-linux-arm64",
  "win32-x64":    "@projanvil/belt-win32-x64",
};

const key = `${os.platform()}-${os.arch()}`;
const pkg = PLATFORM_MAP[key];

if (!pkg) {
  console.error(`belt: unsupported platform: ${key}`);
  console.error(`  Supported: ${Object.keys(PLATFORM_MAP).join(", ")}`);
  process.exit(1);
}

const binName = os.platform() === "win32" ? "belt.exe" : "belt";

let binPath;
try {
  binPath = require.resolve(`${pkg}/bin/${binName}`);
} catch (_) {
  console.error(`belt: platform package ${pkg} is not installed.`);
  console.error(`  Try reinstalling: npm install -g @projanvil/belt`);
  process.exit(1);
}

try {
  execFileSync(binPath, process.argv.slice(2), { stdio: "inherit" });
} catch (e) {
  process.exit(e.status ?? 1);
}
