param(
  [switch]$IncludeDevOps,
  [switch]$EmergencyDeleteResourceGroups = $true,
  [switch]$DeleteTfStateResourceGroup = $true,
  [switch]$DeleteNetworkWatcherRG,
  [string]$DevResourceGroup = "rg-energypredict-dev",
  [string]$ProdResourceGroup = "rg-energypredict-prod",
  [string]$TfStateResourceGroup = "rg-energypredict-tfstate",
  [string]$TfStateStorageAccount = "stenergypredicttfstate01",
  [string]$TfStateContainer = "tfstate",
  [string]$TfStateKeyDev = "dev.terraform.tfstate",
  [string]$TfStateKeyProd = "prod.terraform.tfstate",
  [string]$DevKeyVaultName = "kv-energypredict-dev-02",
  [string]$ProdKeyVaultName = "kv-energypredict-prod-01",
  [string[]]$ExtraKeyVaultNames = @("kv-energypredict-dev-01"),
  [string[]]$KeyVaultSecretNames = @(
    "DATABASE-URL",
    "JWT-SECRET-KEY",
    "FERNET-KEY",
    "SNOWFLAKE-ACCOUNT",
    "SNOWFLAKE-USER",
    "SNOWFLAKE-PASSWORD",
    "SNOWFLAKE-DATABASE",
    "SNOWFLAKE-SCHEMA",
    "SNOWFLAKE-WAREHOUSE",
    "SNOWFLAKE-ROLE",
    "DATABRICKS-WORKSPACE-URL",
    "DATABRICKS-TOKEN",
    "DATABRICKS-JOB-ID"
  )
)

$ErrorActionPreference = "Stop"

function Add-WindowsPathToCurrentSession {
  $machinePath = [Environment]::GetEnvironmentVariable("Path", "Machine")
  $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
  $env:Path = @($env:Path, $machinePath, $userPath) -join ";"
}

function Resolve-ToolPath {
  param(
    [Parameter(Mandatory = $true)][string]$CommandName,
    [string[]]$CandidatePaths = @()
  )

  $cmd = Get-Command $CommandName -ErrorAction SilentlyContinue
  if ($cmd) {
    return $cmd.Source
  }

  foreach ($candidate in $CandidatePaths) {
    if (Test-Path $candidate) {
      return $candidate
    }
  }

  return $null
}

function Add-ToolDirectoryToPath {
  param([string]$ToolPath)

  if ([string]::IsNullOrWhiteSpace($ToolPath)) {
    return
  }

  $toolDir = Split-Path -Parent $ToolPath
  if (-not [string]::IsNullOrWhiteSpace($toolDir)) {
    $env:Path = "$toolDir;$env:Path"
  }
}

function Remove-AzureResourceGroupIfExists {
  param(
    [Parameter(Mandatory = $true)][string]$Name,
    [Parameter(Mandatory = $true)][string]$AzureCli
  )

  if ([string]::IsNullOrWhiteSpace($Name)) {
    return
  }

  $exists = & $AzureCli group exists --name $Name
  if ($LASTEXITCODE -ne 0) {
    Write-Warning "Could not check Resource Group: $Name"
    return
  }

  if ($exists.Trim().ToLowerInvariant() -ne "true") {
    Write-Host "Resource Group already absent: $Name"
    return
  }

  Write-Host "Deleting Resource Group in background: $Name"
  & $AzureCli group delete --name $Name --yes --no-wait
  if ($LASTEXITCODE -ne 0) {
    Write-Warning "Failed to request deletion for Resource Group: $Name"
    return
  }

  Write-Host "Requested RG deletion: $Name"
}

function Remove-KeyVaultSecretsBestEffort {
  param(
    [Parameter(Mandatory = $true)][string]$VaultName,
    [Parameter(Mandatory = $true)][string]$AzureCli,
    [Parameter(Mandatory = $true)][string[]]$SecretNames
  )

  if ([string]::IsNullOrWhiteSpace($VaultName)) {
    return
  }

  $previousErrorActionPreference = $ErrorActionPreference
  $ErrorActionPreference = "Continue"
  & $AzureCli keyvault show --name $VaultName 1>$null 2>$null
  $showVaultExitCode = $LASTEXITCODE
  $ErrorActionPreference = $previousErrorActionPreference

  if ($showVaultExitCode -ne 0) {
    Write-Host "Key Vault already absent or inaccessible: $VaultName"
    return
  }

  Write-Host "Cleaning known Key Vault secrets in: $VaultName"
  foreach ($secretName in $SecretNames) {
    $ErrorActionPreference = "Continue"
    & $AzureCli keyvault secret show --vault-name $VaultName --name $secretName 1>$null 2>$null
    $showSecretExitCode = $LASTEXITCODE
    $ErrorActionPreference = $previousErrorActionPreference

    if ($showSecretExitCode -eq 0) {
      Write-Host "Deleting active secret: $VaultName/$secretName"
      $ErrorActionPreference = "Continue"
      & $AzureCli keyvault secret delete --vault-name $VaultName --name $secretName 1>$null 2>$null
      $ErrorActionPreference = $previousErrorActionPreference
    }

    $ErrorActionPreference = "Continue"
    & $AzureCli keyvault secret show-deleted --vault-name $VaultName --name $secretName 1>$null 2>$null
    $showDeletedSecretExitCode = $LASTEXITCODE
    $ErrorActionPreference = $previousErrorActionPreference

    if ($showDeletedSecretExitCode -eq 0) {
      Write-Host "Purging deleted secret: $VaultName/$secretName"
      $ErrorActionPreference = "Continue"
      & $AzureCli keyvault secret purge --vault-name $VaultName --name $secretName 1>$null 2>$null
      $purgeSecretExitCode = $LASTEXITCODE
      $ErrorActionPreference = $previousErrorActionPreference

      if ($purgeSecretExitCode -ne 0) {
        Write-Warning "Could not purge $VaultName/$secretName. Purge protection or permissions may prevent immediate deletion."
      }
    }
  }
}

function Invoke-TerraformDestroy {
  param(
    [Parameter(Mandatory = $true)][string]$StackPath,
    [Parameter(Mandatory = $true)][string]$StackName,
    [Parameter(Mandatory = $true)][string]$TfStateKey,
    [Parameter(Mandatory = $true)][string]$TerraformCli
  )

  if (-not (Test-Path $StackPath)) {
    Write-Warning "[$StackName] Path not found: $StackPath"
    return
  }

  Write-Host "[$StackName] Running terraform init..."
  Push-Location $StackPath
  try {
    & $TerraformCli init -input=false -reconfigure `
      -backend-config="resource_group_name=$TfStateResourceGroup" `
      -backend-config="storage_account_name=$TfStateStorageAccount" `
      -backend-config="container_name=$TfStateContainer" `
      -backend-config="key=$TfStateKey"
    if ($LASTEXITCODE -ne 0) {
      throw "[$StackName] terraform init failed."
    }

    Write-Host "[$StackName] Running terraform destroy..."
    & $TerraformCli destroy -auto-approve -input=false
    if ($LASTEXITCODE -ne 0) {
      throw "[$StackName] terraform destroy failed."
    }
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

Add-WindowsPathToCurrentSession

$azCli = Resolve-ToolPath -CommandName "az" -CandidatePaths @(
  "C:\Program Files (x86)\Microsoft SDKs\Azure\CLI2\wbin\az.cmd",
  "C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd",
  "C:\ProgramData\chocolatey\bin\az.cmd"
)

$terraformCli = Resolve-ToolPath -CommandName "terraform" -CandidatePaths @(
  "C:\ProgramData\chocolatey\bin\terraform.exe",
  "C:\Program Files\Terraform\terraform.exe"
)

Add-ToolDirectoryToPath -ToolPath $azCli
Add-ToolDirectoryToPath -ToolPath $terraformCli

if (-not $azCli) {
  Write-Error "Azure CLI was not found. Install it with 'choco install azure-cli -y' as Administrator, then open a new PowerShell."
  exit 1
}

if (-not $terraformCli) {
  Write-Warning "Terraform was not found. Skipping Terraform destroy and using Resource Group deletion only."
}

Write-Host "Starting full destroy workflow..."
Write-Host "Repo root: $repoRoot"
Write-Host "Azure CLI: $azCli"
if ($terraformCli) {
  Write-Host "Terraform: $terraformCli"
}

# Order: prod -> dev to reduce dependency issues during teardown
$prodDestroyOk = $false
$devDestroyOk = $false

try {
  if ($terraformCli) {
    Invoke-TerraformDestroy -StackPath $prodPath -StackName "prod" -TfStateKey $TfStateKeyProd -TerraformCli $terraformCli
  }
  $prodDestroyOk = $true
}
catch {
  Write-Warning $_
}

try {
  if ($terraformCli) {
    Invoke-TerraformDestroy -StackPath $devPath -StackName "dev" -TfStateKey $TfStateKeyDev -TerraformCli $terraformCli
  }
  $devDestroyOk = $true
}
catch {
  Write-Warning $_
}

if ($IncludeDevOps) {
  try {
    if ($terraformCli) {
      Invoke-TerraformDestroy -StackPath $devopsPath -StackName "devops" -TfStateKey "devops.terraform.tfstate" -TerraformCli $terraformCli
    }
  }
  catch {
    Write-Warning $_
  }
}

Remove-KeyVaultSecretsBestEffort -VaultName $ProdKeyVaultName -AzureCli $azCli -SecretNames $KeyVaultSecretNames
Remove-KeyVaultSecretsBestEffort -VaultName $DevKeyVaultName -AzureCli $azCli -SecretNames $KeyVaultSecretNames
foreach ($extraKeyVaultName in $ExtraKeyVaultNames) {
  Remove-KeyVaultSecretsBestEffort -VaultName $extraKeyVaultName -AzureCli $azCli -SecretNames $KeyVaultSecretNames
}

if ($EmergencyDeleteResourceGroups -or -not $prodDestroyOk -or -not $devDestroyOk) {
  Write-Host "Project RG deletion enabled. Only explicit EnergyPredict resource groups will be targeted."
  Remove-AzureResourceGroupIfExists -Name $ProdResourceGroup -AzureCli $azCli
  Remove-AzureResourceGroupIfExists -Name $DevResourceGroup -AzureCli $azCli
}

if ($DeleteTfStateResourceGroup) {
  Remove-AzureResourceGroupIfExists -Name $TfStateResourceGroup -AzureCli $azCli
}

if ($DeleteNetworkWatcherRG) {
  Remove-AzureResourceGroupIfExists -Name "NetworkWatcherRG" -AzureCli $azCli
}

Write-Host "Destroy workflow finished."
