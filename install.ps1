# Topoli — install the /property-audit skill for Claude Code on Windows (PowerShell).
#   irm https://raw.githubusercontent.com/suchipizza/Topoli/main/install.ps1 | iex
$ErrorActionPreference = "Stop"
$Src = if ($env:TOPOLI_HOME) { $env:TOPOLI_HOME } else { Join-Path $HOME ".topoli\src" }
$Skills = Join-Path $HOME ".claude\skills"
$Repo = "https://github.com/suchipizza/Topoli.git"

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
  Write-Host "→ installing uv …"
  irm https://astral.sh/uv/install.ps1 | iex
  $env:Path = "$HOME\.local\bin;$env:Path"
}
if (Test-Path (Join-Path $Src ".git")) {
  Write-Host "→ updating $Src …"; git -C $Src pull --ff-only -q
} else {
  Write-Host "→ cloning Topoli into $Src …"
  New-Item -ItemType Directory -Force -Path (Split-Path $Src) | Out-Null
  git clone -q --depth 1 $Repo $Src
}
Write-Host "→ installing the Python environment (uv sync) …"
Push-Location $Src; uv sync -q; Pop-Location
New-Item -ItemType Directory -Force -Path $Skills | Out-Null
$Link = Join-Path $Skills "property-audit"
if (Test-Path $Link) { Remove-Item $Link -Recurse -Force }
New-Item -ItemType Junction -Path $Link -Target (Join-Path $Src "skills\property-audit") | Out-Null
Push-Location $Src; uv run topoli doctor --skip-network | Out-Null; Pop-Location
Write-Host ""
Write-Host "✓ Installed. Open Claude Code and type:  /property-audit ""Badenerstrasse 171, 8003 Zürich"""
