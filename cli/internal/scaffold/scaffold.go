package scaffold

import (
	"embed"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"
)

//go:embed all:templates
var templatesFS embed.FS

// InstallerType controls which install scripts are generated.
type InstallerType string

const (
	InstallerBoth InstallerType = "both"
	InstallerSh   InstallerType = "sh"
	InstallerPs1  InstallerType = "ps1"
)

type fileSpec struct {
	templatePath string
	outputPath   string
	executable   bool
}

// GenerateApp creates a new Belt app at the given outputDir.
// tmpl selects the template set: "empty" (blank placeholders) or "hello-app" (working example).
func GenerateApp(outputDir, appName, appDesc, lang, tmpl string, installer InstallerType, appDir string, components []string) error {
	if _, err := os.Stat(outputDir); err == nil {
		return fmt.Errorf("directory already exists: %s", outputDir)
	}

	// Choose template paths based on selected template.
	var skillEnTpl, skillZhTpl, scriptTpl, agentEnTpl, agentZhTpl string
	switch tmpl {
	case "hello-app":
		skillEnTpl = "templates/apps/hello-app/skills/en/SKILL.md"
		skillZhTpl = "templates/apps/hello-app/skills/zh-cn/SKILL.md"
		scriptTpl = "templates/apps/hello-app/skills/scripts/run.py"
		agentEnTpl = "templates/apps/hello-app/agents/en/agent.md"
		agentZhTpl = "templates/apps/hello-app/agents/zh-cn/agent.md"
	default: // "empty"
		skillEnTpl = "templates/skills/en/_skill-name/SKILL.md"
		skillZhTpl = "templates/skills/zh-cn/_skill-name/SKILL.md"
		scriptTpl = "templates/skills/scripts/_skill-name/run.py"
		agentEnTpl = "templates/agents/en/_agent-name.md"
		agentZhTpl = "templates/agents/zh-cn/_agent-name.md"
	}

	files := []fileSpec{
		{templatePath: skillEnTpl, outputPath: filepath.Join(outputDir, "skills/en", appName, "SKILL.md")},
		{templatePath: skillZhTpl, outputPath: filepath.Join(outputDir, "skills/zh-cn", appName, "SKILL.md")},
		{templatePath: scriptTpl, outputPath: filepath.Join(outputDir, "skills/scripts", appName, "run.py"), executable: true},
		{templatePath: agentEnTpl, outputPath: filepath.Join(outputDir, "agents/en", appName+".md")},
		{templatePath: agentZhTpl, outputPath: filepath.Join(outputDir, "agents/zh-cn", appName+".md")},
	}

	if installer == InstallerBoth || installer == InstallerSh {
		files = append(files, fileSpec{
			templatePath: "templates/install.sh",
			outputPath:   filepath.Join(outputDir, "install.sh"),
			executable:   true,
		})
	}
	if installer == InstallerBoth || installer == InstallerPs1 {
		files = append(files, fileSpec{
			templatePath: "templates/install.ps1",
			outputPath:   filepath.Join(outputDir, "install.ps1"),
		})
	}

	files = append(files, fileSpec{
		templatePath: "templates/README.md",
		outputPath:   filepath.Join(outputDir, "README.md"),
	})
	files = append(files, fileSpec{
		templatePath: "templates/app.json",
		outputPath:   filepath.Join(outputDir, "app.json"),
	})

	replacements := map[string]string{
		"__APP_NAME__":        appName,
		"__APP_DESCRIPTION__": appDesc,
		"__APP_DIR__":         appDir,
		"__COMPONENTS__":      buildComponentsBlock(lang, components),
	}
	for _, file := range files {
		if err := generateFile(file, replacements); err != nil {
			return fmt.Errorf("failed to generate %s: %w", file.outputPath, err)
		}
		relPath, _ := filepath.Rel(".", file.outputPath)
		fmt.Printf("+ %s\n", relPath)
	}

	for _, compName := range components {
		if err := copyComponentReference(appName, lang, compName, outputDir); err != nil {
			fmt.Printf("  ! skipping component %s: %v\n", compName, err)
		}
	}

	return nil
}

// buildComponentsBlock reads each component's description from component.json and returns
// a short Markdown section for injection into SKILL.md via __COMPONENTS__.
// Full reference content is copied as separate files; this block only provides brief descriptions + links.
func buildComponentsBlock(lang string, components []string) string {
	if len(components) == 0 {
		return ""
	}

	var sb strings.Builder
	sb.WriteString("---\n\n## Bundled Components\n\n")
	sb.WriteString("The following components are bundled with this app. Full documentation is in `reference/`.\n\n")

	for _, compName := range components {
		desc := readComponentDescription(compName)
		sb.WriteString("### " + compName + "\n\n")
		if desc != "" {
			sb.WriteString(desc + "\n\n")
		}
		sb.WriteString("→ Full reference: [`reference/" + compName + "/" + compName + ".md`](reference/" + compName + "/" + compName + ".md)\n\n")
	}

	return strings.TrimRight(sb.String(), "\n")
}

// readComponentDescription returns the description field from a component's component.json.
// Returns an empty string on any error.
func readComponentDescription(compName string) string {
	data, err := os.ReadFile(filepath.Join(".", "components", compName, "component.json"))
	if err != nil {
		return ""
	}
	var meta struct {
		Description string `json:"description"`
	}
	if err := json.Unmarshal(data, &meta); err != nil {
		return ""
	}
	return meta.Description
}

// copyComponentReference copies a component's reference doc (named {compName}.md) for the given
// language into the app's skill reference directory: skills/{lang}/{appName}/reference/{compName}.md
func copyComponentReference(appName, lang, compName, outputDir string) error {
	refPath := filepath.Join(".", "components", compName, "reference", lang, compName+".md")
	data, err := os.ReadFile(refPath)
	if err != nil && lang != "en" {
		refPath = filepath.Join(".", "components", compName, "reference", "en", compName+".md")
		data, err = os.ReadFile(refPath)
	}
	if err != nil {
		return fmt.Errorf("reference not found: %w", err)
	}

	destPath := filepath.Join(outputDir, "skills", lang, appName, "reference", compName, compName+".md")
	if err := os.MkdirAll(filepath.Dir(destPath), 0755); err != nil {
		return err
	}
	if err := os.WriteFile(destPath, data, 0644); err != nil {
		return err
	}

	relPath, _ := filepath.Rel(".", destPath)
	fmt.Printf("+ %s  (component: %s)\n", relPath, compName)
	return nil
}

// GenerateComponent creates a new Belt component scaffold with the given name
func GenerateComponent(name string) error {
	componentsDir := "./components"
	compDir := filepath.Join(componentsDir, name)

	if _, err := os.Stat(compDir); err == nil {
		return fmt.Errorf("component already exists: %s", compDir)
	}

	files := []fileSpec{
		{
			templatePath: "templates/component/component.json",
			outputPath:   filepath.Join(compDir, "component.json"),
		},
		{
			templatePath: "templates/component/Makefile",
			outputPath:   filepath.Join(compDir, "Makefile"),
		},
		{
			templatePath: "templates/component/requirements.txt",
			outputPath:   filepath.Join(compDir, "requirements.txt"),
		},
		{
			templatePath: "templates/component/scripts/run.py",
			outputPath:   filepath.Join(compDir, "scripts", name+".py"),
			executable:   true,
		},
		{
			templatePath: "templates/component/reference/en/reference.md",
			outputPath:   filepath.Join(compDir, "reference/en", name+".md"),
		},
		{
			templatePath: "templates/component/reference/zh-cn/reference.md",
			outputPath:   filepath.Join(compDir, "reference/zh-cn", name+".md"),
		},
		{
			templatePath: "templates/component/tests/test_component.py",
			outputPath:   filepath.Join(compDir, "tests", "test_"+name+".py"),
		},
		{
			templatePath: "templates/component/tests/__init__.py",
			outputPath:   filepath.Join(compDir, "tests/__init__.py"),
		},
	}

	replacements := map[string]string{"__COMPONENT_NAME__": name}
	for _, file := range files {
		if err := generateFile(file, replacements); err != nil {
			return fmt.Errorf("failed to generate %s: %w", file.outputPath, err)
		}
		relPath, _ := filepath.Rel(".", file.outputPath)
		fmt.Printf("+ %s\n", relPath)
	}

	return nil
}

func generateFile(spec fileSpec, replacements map[string]string) error {
	content, err := templatesFS.ReadFile(spec.templatePath)
	if err != nil {
		return fmt.Errorf("failed to read template: %w", err)
	}

	output := string(content)
	for placeholder, value := range replacements {
		output = strings.ReplaceAll(output, placeholder, value)
	}

	dir := filepath.Dir(spec.outputPath)
	if err := os.MkdirAll(dir, 0755); err != nil {
		return fmt.Errorf("failed to create directory: %w", err)
	}

	mode := os.FileMode(0644)
	if spec.executable {
		mode = 0755
	}
	if err := os.WriteFile(spec.outputPath, []byte(output), mode); err != nil {
		return fmt.Errorf("failed to write file: %w", err)
	}

	return nil
}
