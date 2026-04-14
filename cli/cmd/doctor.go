package cmd

import (
	"bufio"
	"fmt"
	"os"
	"os/exec"
	"runtime"
	"strings"

	"github.com/spf13/cobra"
)

var doctorCmd = &cobra.Command{
	Use:   "doctor",
	Short: "Check system readiness for Belt",
	Long: `Examine the current system and report which Belt features are available.

Checks:
  - Operating system (Windows / Linux / macOS / WSL)
  - Shell availability: sh / bash
  - PowerShell availability: pwsh / powershell
  - Python availability: python3 / python
  - uv availability (optional package manager)

Exits with code 1 if any required tool is missing.`,
	Run: func(cmd *cobra.Command, args []string) {
		os.Exit(runDoctor())
	},
}

// checkResult holds the outcome of a single system check.
type checkResult struct {
	label    string
	found    bool
	detail   string
	optional bool
}

func runDoctor() int {
	fmt.Println("Belt Doctor — system check")
	fmt.Println(strings.Repeat("─", 44))

	// ── OS ──────────────────────────────────────────────────────────────────
	fmt.Println("\nSystem")
	goos := runtime.GOOS
	osLabel := map[string]string{
		"windows": "Windows",
		"darwin":  "macOS",
		"linux":   "Linux",
	}[goos]
	if osLabel == "" {
		osLabel = goos
	}

	isWSL := false
	if goos == "linux" {
		isWSL = detectWSL()
		if isWSL {
			osLabel += " (WSL)"
		}
	}
	fmt.Printf("  %-12s %s\n", "OS:", osLabel)

	// ── Shell checks ────────────────────────────────────────────────────────
	fmt.Println("\nShell")
	shChecks := []checkResult{
		lookupTool("sh", false),
		lookupTool("bash", false),
	}
	printChecks(shChecks)

	// ── PowerShell checks ───────────────────────────────────────────────────
	fmt.Println("\nPowerShell")
	psChecks := []checkResult{
		lookupTool("pwsh", false),
		lookupTool("powershell", false),
	}
	printChecks(psChecks)

	// ── Python checks ───────────────────────────────────────────────────────
	fmt.Println("\nPython")
	pythonCheck := firstFound([]string{"python3", "python"})
	pyChecks := []checkResult{pythonCheck}
	uvCheck := lookupTool("uv", true)
	pyChecks = append(pyChecks, uvCheck)
	printChecks(pyChecks)

	// ── Recommendation ──────────────────────────────────────────────────────
	fmt.Println("\n" + strings.Repeat("─", 44))
	fmt.Println("Recommendation")

	hasSh := shChecks[0].found || shChecks[1].found
	hasPs := psChecks[0].found || psChecks[1].found

	switch {
	case hasSh && hasPs:
		fmt.Println("  ✓ Both sh and PowerShell are available.")
		fmt.Println("    Use: belt new <app>  →  choose \"both\"")
	case hasSh:
		fmt.Println("  ✓ sh/bash is available.")
		fmt.Println("    Use: belt new <app>  →  choose \"Linux / WSL (sh only)\"")
	case hasPs:
		fmt.Println("  ✓ PowerShell is available.")
		fmt.Println("    Use: belt new <app>  →  choose \"Windows (PowerShell only)\"")
	default:
		fmt.Println("  ✗ Neither sh nor PowerShell found — install one first.")
	}

	if !pythonCheck.found {
		fmt.Println("  ✗ Python not found — required for Belt scripts.")
		fmt.Println("    Install: https://www.python.org/downloads/")
	}
	if !uvCheck.found {
		fmt.Println("  ⚠ uv not found (optional, faster package management).")
		fmt.Println("    Install: https://github.com/astral-sh/uv")
	}

	// Return exit code.
	requiredMissing := false
	if !hasSh && !hasPs {
		requiredMissing = true
	}
	if !pythonCheck.found {
		requiredMissing = true
	}
	if requiredMissing {
		return 1
	}
	fmt.Println("\n✓ All required tools found.")
	return 0
}

// lookupTool checks whether a binary exists in PATH.
func lookupTool(name string, optional bool) checkResult {
	path, err := exec.LookPath(name)
	if err != nil {
		return checkResult{label: name, found: false, optional: optional}
	}
	// Attempt to get version string (best-effort).
	ver := binaryVersion(name)
	detail := path
	if ver != "" {
		detail = fmt.Sprintf("%s (%s)", path, ver)
	}
	return checkResult{label: name, found: true, detail: detail, optional: optional}
}

// firstFound returns the first available tool from candidates.
// The label of the result is the name that was found (or the first candidate).
func firstFound(candidates []string) checkResult {
	for _, name := range candidates {
		r := lookupTool(name, false)
		if r.found {
			return r
		}
	}
	return checkResult{label: candidates[0], found: false}
}

// printChecks renders a slice of check results to stdout.
func printChecks(results []checkResult) {
	for _, r := range results {
		switch {
		case r.found:
			fmt.Printf("  ✓ %-12s %s\n", r.label+":", r.detail)
		case r.optional:
			fmt.Printf("  ⚠ %-12s not installed (optional)\n", r.label+":")
		default:
			fmt.Printf("  ✗ %-12s not found\n", r.label+":")
		}
	}
}

// detectWSL returns true when running inside Windows Subsystem for Linux.
func detectWSL() bool {
	f, err := os.Open("/proc/version")
	if err != nil {
		return false
	}
	defer f.Close()
	scanner := bufio.NewScanner(f)
	if scanner.Scan() {
		line := strings.ToLower(scanner.Text())
		return strings.Contains(line, "microsoft") || strings.Contains(line, "wsl")
	}
	return false
}

// binaryVersion attempts a best-effort version string for common tools.
func binaryVersion(name string) string {
	var args []string
	switch name {
	case "python3", "python":
		args = []string{"--version"}
	case "pwsh", "powershell":
		args = []string{"--version"}
	case "bash", "sh":
		args = []string{"--version"}
	case "uv":
		args = []string{"--version"}
	default:
		return ""
	}

	out, err := exec.Command(name, args...).CombinedOutput()
	if err != nil {
		return ""
	}
	line := strings.TrimSpace(strings.SplitN(string(out), "\n", 2)[0])
	// Trim common prefixes so output stays tidy.
	for _, prefix := range []string{"Python ", "PowerShell ", "GNU bash, version ", "uv "} {
		line = strings.TrimPrefix(line, prefix)
	}
	if len(line) > 40 {
		line = line[:40]
	}
	return line
}

func init() {
	rootCmd.AddCommand(doctorCmd)
}
