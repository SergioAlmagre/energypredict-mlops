param(
  [switch]$IncludeDevOps,
  [switch]$EmergencyDeleteResourceGroups,
  [string]$DevResourceGroup = "rg-energypredict-dev",
  [string]$ProdResourceGroup = "rg-energypredict-prod"
)

$ErrorActionPreference = "Stop"

function Invoke-TerraformDestroy {
  param(
    [Parameter(Mandatory = $true)][string]$StackPath,
    [Parameter(Mandatory = $true)][string]$StackName
  )

  if (-not (Test-Path $StackPath)) {
    Write-Warning "[$StackName] Path not found: $StackPath"
    return
  }

  Write-Host "[$StackName] Running terraform init..."
  Push-Location $StackPath
  try {
    terraform init -input=false
    Write-Host "[$StackName] Running terraform destroy..."
    terraform destroy -auto-approve -input=false
    Write-Host "[$StackName] Destroy completed."
  }
  finally {
    Pop-Location
  }
}

$repoRoot = Split-Path -Parent $PSScriptRoot
$prodPath = Join-Path $repoRoot "infra/terraform/envs/prod"
$devPath = Join-Path $repoRoot "infra/terraform/envs/dev"
$devopsPath = Join-Path $repoRoot "infra/terraform/devops"

Write-Host "Starting full destroy workflow..."
Write-Host "Repo root: $repoRoot"

# Order: prod -> dev to reduce dependency issues during teardown
Invoke-TerraformDestroy -StackPath $prodPath -StackName "prod"
Invoke-TerraformDestroy -StackPath $devPath -StackName "dev"

if ($IncludeDevOps) {
  Invoke-TerraformDestroy -StackPath $devopsPath -StackName "devops"
}

if ($EmergencyDeleteResourceGroups) {
  Write-Host "Emergency RG deletion enabled. Deleting RGs in background..."
  az group delete --name $ProdResourceGroup --yes --no-wait
  az group delete --name $DevResourceGroup --yes --no-wait
  Write-Host "Requested RG deletion: $ProdResourceGroup, $DevResourceGroup"
}

Write-Host "Destroy workflow finished."
