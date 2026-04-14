package cmd

import (
	"fmt"
	"os"
	"path/filepath"

	survey "github.com/AlecAivazis/survey/v2"
	"github.com/projanvil/belt/internal/scaffold"
	"github.com/spf13/cobra"
)

var (
	typeFlag      string
	installerFlag string
)

const (
	installerOptBoth = "both (sh + PowerShell)"
	installerOptSh   = "Linux / macOS (sh)"
	installerOptPs1  = "Windows (PowerShell)"

	templateOptEmpty = "empty     — blank templates with placeholders"
	templateOptHello = "hello-app — working example with greet skill"
)

var newCmd = &cobra.Command{
	Use:   "new [path]",
	Short: "Scaffold a new Belt app or component",
	Long: `Scaffold a new Belt app or component interactively.

App (default):
  belt new              Creates ./<app-name>/ in the current directory
  belt new ./projects   Creates ./projects/<app-name>/

Component:
  belt new --type=component <name>
  Creates ./components/<name>/ with scripts, reference docs, and tests.`,
	Args: cobra.MaximumNArgs(1),
	Run: func(cmd *cobra.Command, args []string) {

		// ── Component mode (non-interactive, name is a positional arg) ────────
		if typeFlag == "component" {
			if len(args) == 0 {
				exitWithError("Component name required: belt new --type=component <name>")
			}
			name := args[0]
			fmt.Printf("Creating Belt component: %s\n", name)
			if err := scaffold.GenerateComponent(name); err != nil {
				exitWithError("Failed to generate component: %v", err)
			}
			fmt.Printf("\n✓ Component generated: components/%s/\n", name)
			fmt.Printf("\nNext steps:\n")
			fmt.Printf("  1. Edit reference docs in components/%s/reference/\n", name)
			fmt.Printf("  2. Edit scripts       in components/%s/scripts/\n", name)
			fmt.Printf("  3. Run tests:            make -C components/%s test\n", name)
			fmt.Printf("  4. Install:              belt install %s\n", name)
			return
		}

		// ── App mode: determine parent directory ──────────────────────────────
		parentDir := "."
		if len(args) > 0 {
			parentDir = filepath.Clean(args[0])
		}

		// 2.1 App name
		appName, err := promptAppName()
		if err != nil {
			exitWithError("%v", err)
		}

		// 2.2 App description
		appDesc, err := promptAppDescription()
		if err != nil {
			exitWithError("%v", err)
		}

		// 2.3 Template
		tmpl, err := promptTemplate()
		if err != nil {
			exitWithError("%v", err)
		}

		// 2.3.1 Component selection — only for empty template
		var components []string
		if tmpl == "empty" {
			components, err = resolveComponents()
			if err != nil {
				exitWithError("%v", err)
			}
		}

		// 2.3.2 App data directory
		appDir, err := resolveAppDir(appName)
		if err != nil {
			exitWithError("%v", err)
		}

		// 2.4 Language
		lang, err := promptLang()
		if err != nil {
			exitWithError("%v", err)
		}

		// 2.5 Installer scripts
		installerType, err := resolveInstallerType(cmd, installerFlag)
		if err != nil {
			exitWithError("%v", err)
		}

		// 2.6 Create files
		outputDir := filepath.Join(parentDir, appName)
		fmt.Printf("\nCreating Belt app: %s\n", appName)
		if err := scaffold.GenerateApp(outputDir, appName, appDesc, lang, tmpl, installerType, appDir, components); err != nil {
			exitWithError("Failed to generate app: %v", err)
		}

		// 2.6 Done — next-step instructions
		fmt.Printf("\n✓ App generated: %s/\n", outputDir)
		fmt.Printf("\nNext steps:\n")
		fmt.Printf("  cd %s\n", outputDir)
		if installerType == scaffold.InstallerBoth || installerType == scaffold.InstallerSh {
			fmt.Printf("  bash install.sh        # install on Linux / macOS\n")
		}
		if installerType == scaffold.InstallerBoth || installerType == scaffold.InstallerPs1 {
			fmt.Printf("  pwsh install.ps1       # install on Windows\n")
		}
		fmt.Printf("\nOnce installed, Claude Code will recognise:\n")
		fmt.Printf("  /%s   (skill)\n", appName)
		fmt.Printf("  @%s   (agent)\n", appName)
	},
}

// ── Interactive prompts ────────────────────────────────────────────────────

func promptAppName() (string, error) {
	var name string
	if err := survey.AskOne(&survey.Input{
		Message: "App name:",
		Help:    "Used as the skill/agent identifier in Claude Code (e.g. my-tool)",
	}, &name, survey.WithValidator(survey.Required)); err != nil {
		return "", fmt.Errorf("cancelled")
	}
	return name, nil
}

func promptAppDescription() (string, error) {
	var desc string
	if err := survey.AskOne(&survey.Input{
		Message: "App description:",
		Help:    "One-line description of what your app does (used in SKILL.md and README)",
	}, &desc, survey.WithValidator(survey.Required)); err != nil {
		return "", fmt.Errorf("cancelled")
	}
	return desc, nil
}

func promptTemplate() (string, error) {
	var choice string
	if err := survey.AskOne(&survey.Select{
		Message: "Template:",
		Options: []string{templateOptEmpty, templateOptHello},
		Default: templateOptEmpty,
	}, &choice); err != nil {
		return "empty", nil
	}
	if choice == templateOptHello {
		return "hello-app", nil
	}
	return "empty", nil
}

func promptLang() (string, error) {
	var choice string
	if err := survey.AskOne(&survey.Select{
		Message: "Language:",
		Options: []string{"en  — English", "zh-cn  — 中文"},
		Default: "en  — English",
	}, &choice); err != nil {
		return "en", nil
	}
	if choice == "zh-cn  — 中文" {
		return "zh-cn", nil
	}
	return "en", nil
}

// resolveInstallerType returns the InstallerType from the --installer flag,
// or opens an interactive prompt when the flag was not explicitly set.
func resolveInstallerType(cmd *cobra.Command, flagVal string) (scaffold.InstallerType, error) {
	if cmd.Flags().Changed("installer") {
		switch flagVal {
		case "sh":
			return scaffold.InstallerSh, nil
		case "ps1":
			return scaffold.InstallerPs1, nil
		case "both":
			return scaffold.InstallerBoth, nil
		default:
			return "", fmt.Errorf("invalid --installer value %q (supported: both, sh, ps1)", flagVal)
		}
	}
	var choice string
	if err := survey.AskOne(&survey.Select{
		Message: "Install scripts to generate:",
		Options: []string{installerOptBoth, installerOptSh, installerOptPs1},
		Default: installerOptBoth,
	}, &choice); err != nil {
		return scaffold.InstallerBoth, nil
	}
	switch choice {
	case installerOptSh:
		return scaffold.InstallerSh, nil
	case installerOptPs1:
		return scaffold.InstallerPs1, nil
	default:
		return scaffold.InstallerBoth, nil
	}
}

// resolveAppDir prompts for the app's runtime data directory.
// This is NOT the skill install path (~/.claude/skills/<name>) — that is always fixed.
// The app_dir is stored in app.json and read by the skill at runtime.
func resolveAppDir(appName string) (string, error) {
	opt1 := fmt.Sprintf("~/.claude/.%s  (hidden, alongside Claude config)", appName)
	opt2 := fmt.Sprintf("~/.%s  (hidden, user home root)", appName)
	opt3 := fmt.Sprintf("~/.projanvil/%s  (projanvil ecosystem)", appName)
	opt4 := "Customize (enter a path)"

	var choice string
	if err := survey.AskOne(&survey.Select{
		Message: "App data directory (where the app stores runtime files):",
		Options: []string{opt1, opt2, opt3, opt4},
		Default: opt1,
	}, &choice); err != nil {
		return fmt.Sprintf("~/.claude/.%s", appName), nil
	}
	switch choice {
	case opt1:
		return fmt.Sprintf("~/.claude/.%s", appName), nil
	case opt2:
		return fmt.Sprintf("~/.%s", appName), nil
	case opt3:
		return fmt.Sprintf("~/.projanvil/%s", appName), nil
	default:
		var custom string
		if err := survey.AskOne(&survey.Input{
			Message: "Enter app data directory (e.g. ~/my-data or /var/data/my-app):",
		}, &custom, survey.WithValidator(survey.Required)); err != nil {
			return fmt.Sprintf("~/.claude/.%s", appName), nil
		}
		return custom, nil
	}
}

// resolveComponents shows an optional multi-select of available components whose
// reference docs will be injected into the generated SKILL.md.
func resolveComponents() ([]string, error) {
	entries, err := os.ReadDir("./components")
	if err != nil {
		if os.IsNotExist(err) {
			return nil, nil
		}
		return nil, fmt.Errorf("failed to list components: %w", err)
	}
	var available []string
	for _, e := range entries {
		if e.IsDir() {
			available = append(available, e.Name())
		}
	}
	if len(available) == 0 {
		return nil, nil
	}
	var selected []string
	if err := survey.AskOne(&survey.MultiSelect{
		Message: "Bundle components (reference injected into SKILL.md):",
		Options: available,
	}, &selected); err != nil {
		return nil, nil
	}
	return selected, nil
}

func init() {
	rootCmd.AddCommand(newCmd)
	newCmd.Flags().StringVar(&typeFlag, "type", "app", "Type to generate: app or component")
	newCmd.Flags().StringVar(&installerFlag, "installer", "both", "Installer scripts: both, sh, ps1 (skips interactive prompt)")
}
