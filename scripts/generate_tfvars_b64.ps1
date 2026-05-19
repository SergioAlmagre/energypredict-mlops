param(
  [string]$DevTfvarsPath = "infra/terraform/envs/dev/terraform.tfvars",
  [string]$ProdTfvarsPath = "infra/terraform/envs/prod/terraform.tfvars",
  [switch]$OutputEnvFile
)

$ErrorActionPreference = "Stop"

function Convert-FileToBase64 {
  param([Parameter(Mandatory = $true)][string]$Path)
  if (-not (Test-Path $Path)) {
    throw "File not found: $Path"
  }
  $content = Get-Content $Path -Raw -Encoding UTF8
  return [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($content))
}

$devB64 = Convert-FileToBase64 -Path $DevTfvarsPath
$prodB64 = Convert-FileToBase64 -Path $ProdTfvarsPath

Write-Host "Create/update these SECRET variables in Azure DevOps Variable Group: energypredict-shared"
Write-Host ""
Write-Host "TFVARS_DEV_B64 ="
Write-Output $devB64
Write-Host ""
Write-Host "TFVARS_PROD_B64 ="
Write-Output $prodB64

if ($OutputEnvFile) {
  $outPath = "tfvars_b64.env"
  @(
    "TFVARS_DEV_B64=$devB64"
    "TFVARS_PROD_B64=$prodB64"
  ) | Set-Content -Path $outPath -Encoding UTF8
  Write-Host ""
  Write-Host "Saved: $outPath"
}
