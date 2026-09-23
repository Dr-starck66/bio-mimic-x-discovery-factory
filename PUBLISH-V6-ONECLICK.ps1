$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Owner = "Dr-starck66"
$RepoName = "bio-mimic-x-scientific-org"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path

function PASS($m) { Write-Host "[PASS] $m" -ForegroundColor Green }
function WARN($m) { Write-Host "[WARN] $m" -ForegroundColor Yellow }
function FAIL($m) { Write-Host "[FAIL] $m" -ForegroundColor Red; throw $m }

try {
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) { FAIL "git absent" }
    if (-not (Get-Command gh -ErrorAction SilentlyContinue)) { FAIL "gh absent" }
    if (-not (Get-Command python -ErrorAction SilentlyContinue)) { FAIL "python absent" }

    gh auth status 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) { FAIL "GitHub CLI non authentifié" }
    PASS "GitHub authentifié"

    Set-Location $Root

    python -m unittest discover -s tests -v
    if ($LASTEXITCODE -ne 0) { FAIL "tests unitaires échoués" }
    PASS "tests V6 réels"

    python -m py_compile organization/lab_worker.py organization/committee.py
    if ($LASTEXITCODE -ne 0) { FAIL "compilation Python échouée" }
    PASS "compilation Python"

    gh repo view "$Owner/$RepoName" --json name 2>$null | Out-Null
    if ($LASTEXITCODE -ne 0) {
        gh repo create "$Owner/$RepoName" --private --description "BIO-MIMIC X V6 autonomous scientific organization"
        if ($LASTEXITCODE -ne 0) { FAIL "création dépôt échouée" }
        PASS "dépôt privé créé"
    } else { PASS "dépôt existant" }

    if (-not (Test-Path ".git")) { git init }
    git branch -M main

    $Remote = git remote get-url origin 2>$null
    $Wanted = "https://github.com/$Owner/$RepoName.git"
    if ($LASTEXITCODE -ne 0) { git remote add origin $Wanted }
    elseif ($Remote -ne $Wanted) { git remote set-url origin $Wanted }
    PASS "remote vérifié"

    git add .
    git diff --cached --quiet
    if ($LASTEXITCODE -ne 0) {
        git commit -m "BIO-MIMIC X V6 autonomous scientific organization"
        if ($LASTEXITCODE -ne 0) { FAIL "commit échoué" }
        PASS "commit créé"
    } else { WARN "aucun changement local" }

    git push -u origin main
    if ($LASTEXITCODE -ne 0) { FAIL "push échoué" }
    PASS "push GitHub"

    $Wf = gh api "repos/$Owner/$RepoName/contents/.github/workflows/scientific-organization.yml" --jq '.path'
    if ($LASTEXITCODE -ne 0 -or $Wf -ne ".github/workflows/scientific-organization.yml") { FAIL "workflow V6 absent à distance" }
    PASS "workflow V6 présent"

    $Sha = gh api "repos/$Owner/$RepoName/commits/main" --jq '.sha'
    if (-not $Sha) { FAIL "SHA distant absent" }
    PASS "preuve commit distant: $Sha"

    Write-Host ""
    Write-Host "V6 publié: https://github.com/$Owner/$RepoName" -ForegroundColor Cyan
    Write-Host "Actions lancera l'organisation scientifique automatiquement selon le cron." -ForegroundColor Cyan
}
catch {
    Write-Host "[FAIL] $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
