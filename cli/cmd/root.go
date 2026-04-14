package cmd

import (
	"fmt"
	"os"

	"github.com/spf13/cobra"
)

var rootCmd = &cobra.Command{
	Use:   "belt",
	Short: "Belt - Scaffold AI-native apps for Claude Code",
	Long: `Belt is a CLI tool for scaffolding AI-native apps for Claude Code.

It generates project structures with skills, agents, and installation scripts
that integrate seamlessly with Claude Code's skill and agent system.`,
	Version: "1.0.0",
}

func Execute() error {
	return rootCmd.Execute()
}

func init() {
	rootCmd.CompletionOptions.DisableDefaultCmd = true
}

func exitWithError(format string, args ...interface{}) {
	fmt.Fprintf(os.Stderr, "✗ "+format+"\n", args...)
	os.Exit(1)
}
