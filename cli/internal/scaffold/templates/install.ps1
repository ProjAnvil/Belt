param(
    [ValidateSet("en", "zh-cn")]
    [string]$Lang = "en"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$AppName = "__APP_NAME__"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

$SkillSrc = Join-Path $ScriptDir "skills/$Lang/$AppName"
$ScriptsSrc = Join-Path $ScriptDir "skills/scripts/$AppName"
$AgentSrc = Join-Path $ScriptDir "agents/$Lang/$AppName.md"

$ClaudeDir = Join-Path $HOME ".claude"
$ClaudeSkillsDir = Join-Path $ClaudeDir "skills"
$ClaudeAgentsDir = Join-Path $ClaudeDir "agents"

Write-Host "Installing: $AppName (lang: $Lang)"

New-Item -ItemType Directory -Force -Path (Join-Path $ClaudeSkillsDir $AppName) | Out-Null
New-Item -ItemType Directory -Force -Path $ClaudeAgentsDir | Out-Null

function Link-Or-Copy {
    param(
        [Parameter(Mandatory = $true)] [string]$Src,
        [Parameter(Mandatory = $true)] [string]$Dst,
        [Parameter(Mandatory = $true)] [string]$Label
    )

    if (Test-Path -LiteralPath $Dst) {
        Remove-Item -LiteralPath $Dst -Recurse -Force
    }

    if ($IsWindows) {
        Copy-Item -Path $Src -Destination $Dst -Recurse -Force
        Write-Host "  copied $Label"
        return
    }

    New-Item -ItemType SymbolicLink -Path $Dst -Target $Src | Out-Null
    Write-Host "  linked $Label"
}

if (-not (Test-Path -LiteralPath $SkillSrc -PathType Container)) {
    throw "Skill source not found: $SkillSrc"
}

Get-ChildItem -Path $SkillSrc -Force | Where-Object { $_.Name -ne 'reference' } | ForEach-Object {
    $dst = Join-Path (Join-Path $ClaudeSkillsDir $AppName) $_.Name
    Link-Or-Copy -Src $_.FullName -Dst $dst -Label "$AppName/$($_.Name)"
}

# -- reference/ directory -----------------------------------------------
# Created as a real directory so app.json can live alongside component
# reference files without writing back into the project tree.
$ReferenceDst = Join-Path (Join-Path $ClaudeSkillsDir $AppName) 'reference'
New-Item -ItemType Directory -Force -Path $ReferenceDst | Out-Null

$AppJsonSrc = Join-Path $ScriptDir 'app.json'
if (Test-Path -LiteralPath $AppJsonSrc -PathType Leaf) {
    Copy-Item -Path $AppJsonSrc -Destination (Join-Path $ReferenceDst 'app.json') -Force
    Write-Host "  copied reference/app.json"

    # Create the app data directory declared in app.json
    try {
        $appJsonContent = Get-Content $AppJsonSrc -Raw | ConvertFrom-Json
        $appDir = $appJsonContent.app_dir -replace '^~', $HOME
        if ($appDir) {
            New-Item -ItemType Directory -Force -Path $appDir | Out-Null
            Write-Host "  created app dir: $appDir"
        }
    } catch {
        Write-Host "  (could not read app_dir from app.json)"
    }
} else {
    Write-Host "  (no app.json found - skipping)"
}

$ReferenceSrc = Join-Path $SkillSrc 'reference'
if (Test-Path -LiteralPath $ReferenceSrc -PathType Container) {
    # Each component lives in its own subdirectory; link files and dirs alike
    Get-ChildItem -Path $ReferenceSrc | ForEach-Object {
        $dst = Join-Path $ReferenceDst $_.Name
        Link-Or-Copy -Src $_.FullName -Dst $dst -Label "reference/$($_.Name)"
    }
}

if (Test-Path -LiteralPath $ScriptsSrc -PathType Container) {
    Link-Or-Copy -Src $ScriptsSrc -Dst (Join-Path (Join-Path $ClaudeSkillsDir $AppName) "scripts") -Label "$AppName/scripts"
}

if (Test-Path -LiteralPath $AgentSrc -PathType Leaf) {
    Link-Or-Copy -Src $AgentSrc -Dst (Join-Path $ClaudeAgentsDir "$AppName.md") -Label "$AppName.md"
} else {
    Write-Host "  (no agent found at $AgentSrc - skipping)"
}

Write-Host ""
Write-Host "Done! $AppName installed."
Write-Host ""
Write-Host "Claude Code will now recognize:"
Write-Host "  Skill:  $AppName  (invoke via /$AppName)"
Write-Host "  Agent:  @$AppName"
Write-Host ""
Write-Host "To uninstall:"
Write-Host "  Remove-Item -Recurse -Force $(Join-Path $ClaudeSkillsDir $AppName)"
Write-Host "  Remove-Item -Force $(Join-Path $ClaudeAgentsDir \"$AppName.md\")"
