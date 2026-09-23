$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$RepoName = "bio-mimic-x-autonomous-lab"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Owner = "Dr-starck66"

function PASS($m) { Write-Host "[PASS] $m" -ForegroundColor Green }
function WARN($m) { Write-Host "[WARN] $m" -ForegroundColor Yellow }
function FAIL($m) { Write-Host "[FAIL] $m" -ForegroundColor Red; throw $m }

try {
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) { FAIL "git absent" }
    if (-not (Get-Command gh -ErrorAction SilentlyContinue)) { FAIL "GitHub CLI gh absent" }

    git --version | Out-Null
    if ($LASTEXITCODE -ne 0) { FAIL "git ne répond pas correctement" }
    PASS "git opérationnel"

    gh auth status 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) { FAIL "gh n'est pas authentifié" }
    PASS "GitHub CLI authentifié"

    Set-Location $Root

    python -m unittest discover -s tests -v
    if ($LASTEXITCODE -ne 0) { FAIL "tests V5 échoués" }
    PASS "tests V5 réels"

    $Exists = $false
    gh repo view "$Owner/$RepoName" --json name 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) { $Exists = $true }

    if (-not $Exists) {
        gh repo create "$Owner/$RepoName" --private --description "BIO-MIMIC X autonomous comparative medicine research lab"
        if ($LASTEXITCODE -ne 0) { FAIL "création du dépôt échouée" }
        PASS "dépôt privé créé"
    } else {
        PASS "dépôt déjà existant"
    }

    if (-not (Test-Path ".git")) {
        git init
        if ($LASTEXITCODE -ne 0) { FAIL "git init échoué" }
    }

    git branch -M main

    $Remote = git remote get-url origin 2>$null
    if ($LASTEXITCODE -ne 0) {
        git remote add origin "https://github.com/$Owner/$RepoName.git"
    } elseif ($Remote -ne "https://github.com/$Owner/$RepoName.git") {
        git remote set-url origin "https://github.com/$Owner/$RepoName.git"
    }
    PASS "remote origin vérifié"

    git add .
    git diff --cached --quiet
    if ($LASTEXITCODE -ne 0) {
        git commit -m "BIO-MIMIC X V5 autonomous lab"
        if ($LASTEXITCODE -ne 0) { FAIL "commit échoué" }
        PASS "commit créé"
    } else {
        WARN "aucun changement à committer"
    }

    git push -u origin main
    if ($LASTEXITCODE -ne 0) { FAIL "push GitHub échoué" }
    PASS "push vérifié"

    $Workflow = gh api "repos/$Owner/$RepoName/contents/.github/workflows/daily-lab.yml" --jq '.path'
    if ($LASTEXITCODE -ne 0 -or $Workflow -ne ".github/workflows/daily-lab.yml") {
        FAIL "workflow daily-lab introuvable après push"
    }
    PASS "workflow daily-lab présent sur GitHub"

    $Head = gh api "repos/$Owner/$RepoName/commits/main" --jq '.sha'
    if (-not $Head) { FAIL "SHA distant non récupéré" }
    PASS "preuve commit distant: $Head"

    Write-Host ""
    Write-Host "BIO-MIMIC X V5 publié: https://github.com/$Owner/$RepoName" -ForegroundColor Cyan
    Write-Host "Le laboratoire se lancera automatiquement via le cron GitHub Actions." -ForegroundColor Cyan
}
catch {
    Write-Host "[FAIL] $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
