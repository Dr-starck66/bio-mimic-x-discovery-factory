$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
$Owner="Dr-starck66"
$RepoName="bio-mimic-x-discovery-factory"
$Root=Split-Path -Parent $MyInvocation.MyCommand.Path
function PASS($m){Write-Host "[PASS] $m" -ForegroundColor Green}
function WARN($m){Write-Host "[WARN] $m" -ForegroundColor Yellow}
function FAIL($m){Write-Host "[FAIL] $m" -ForegroundColor Red; throw $m}
try {
  foreach($cmd in @("git","gh","python")) {
    if(-not (Get-Command $cmd -ErrorAction SilentlyContinue)){FAIL "$cmd absent"}
  }
  gh auth status 2>&1 | Out-Null
  if($LASTEXITCODE -ne 0){FAIL "gh non authentifié"}
  PASS "GitHub authentifié"

  Set-Location $Root
  python -m unittest discover -s tests -v
  if($LASTEXITCODE -ne 0){FAIL "tests échoués"}
  PASS "tests réels"

  python factory/brick_audit.py
  if($LASTEXITCODE -ne 0){FAIL "brick audit échoué"}
  PASS "aucune brique active décorative"

  python -m py_compile factory/control_plane.py factory/program_director.py factory/policy_foundry.py
  if($LASTEXITCODE -ne 0){FAIL "compilation Python échouée"}
  PASS "compilation Python"

  gh repo view "$Owner/$RepoName" --json name 2>$null | Out-Null
  if($LASTEXITCODE -ne 0){
    gh repo create "$Owner/$RepoName" --private --description "BIO-MIMIC X V7 Scientific Discovery Factory"
    if($LASTEXITCODE -ne 0){FAIL "création dépôt échouée"}
    PASS "dépôt privé créé"
  } else {PASS "dépôt existant"}

  if(-not (Test-Path ".git")){git init}
  git branch -M main
  $Wanted="https://github.com/$Owner/$RepoName.git"
  $Remote=git remote get-url origin 2>$null
  if($LASTEXITCODE -ne 0){git remote add origin $Wanted}
  elseif($Remote -ne $Wanted){git remote set-url origin $Wanted}
  PASS "remote vérifié"

  git add .
  git diff --cached --quiet
  if($LASTEXITCODE -ne 0){
    git commit -m "BIO-MIMIC X V7 scientific discovery factory"
    if($LASTEXITCODE -ne 0){FAIL "commit échoué"}
    PASS "commit créé"
  } else {WARN "aucun changement à committer"}

  git push -u origin main
  if($LASTEXITCODE -ne 0){FAIL "push échoué"}
  PASS "push distant"

  $Wf=gh api "repos/$Owner/$RepoName/contents/.github/workflows/scientific-discovery-factory.yml" --jq '.path'
  if($LASTEXITCODE -ne 0 -or $Wf -ne ".github/workflows/scientific-discovery-factory.yml"){FAIL "workflow V7 absent"}
  PASS "workflow V7 présent"

  $Sha=gh api "repos/$Owner/$RepoName/commits/main" --jq '.sha'
  if(-not $Sha){FAIL "preuve SHA distante absente"}
  PASS "commit distant $Sha"
  Write-Host "V7 publié: https://github.com/$Owner/$RepoName" -ForegroundColor Cyan
} catch {
  Write-Host "[FAIL] $($_.Exception.Message)" -ForegroundColor Red
  exit 1
}
