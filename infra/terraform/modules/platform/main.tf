locals {
  base_tags = merge(
    {
      project     = var.project_name
      environment = var.environment
      managed_by  = "terraform"
    },
    var.tags
  )

  generated_app_secrets = var.enable_postgresql ? {
    DATABASE_URL = format(
      "postgresql+psycopg2://%s:%s@%s:5432/%s",
      var.postgresql_admin_username,
      urlencode(var.postgresql_admin_password),
      azurerm_postgresql_flexible_server.this[0].fqdn,
      azurerm_postgresql_flexible_server_database.this[0].name
    )
  } : {}

  effective_app_secrets  = merge(var.key_vault_app_secrets, local.generated_app_secrets)
  effective_namespace    = coalesce(var.kubernetes_namespace, "${var.project_name}-${var.environment}")
  effective_sa_name      = coalesce(var.workload_identity_service_account_name, "${var.project_name}-api-${var.environment}")
  effective_aks_location = coalesce(var.aks_location, azurerm_resource_group.this.location)
}

data "azurerm_client_config" "current" {}

resource "azurerm_resource_group" "this" {
  name     = var.resource_group_name
  location = var.location
  tags     = local.base_tags
}

resource "azurerm_log_analytics_workspace" "this" {
  name                = var.log_analytics_name
  location            = azurerm_resource_group.this.location
  resource_group_name = azurerm_resource_group.this.name
  sku                 = "PerGB2018"
  retention_in_days   = 30
  tags                = local.base_tags
}

resource "azurerm_container_registry" "this" {
  name                = var.acr_name
  location            = azurerm_resource_group.this.location
  resource_group_name = azurerm_resource_group.this.name
  sku                 = "Basic"
  admin_enabled       = false
  tags                = local.base_tags
}

resource "azurerm_user_assigned_identity" "aks" {
  name                = "${var.aks_name}-uami"
  location            = local.effective_aks_location
  resource_group_name = azurerm_resource_group.this.name
  tags                = local.base_tags
}

resource "azurerm_key_vault" "this" {
  name                          = var.key_vault_name
  location                      = azurerm_resource_group.this.location
  resource_group_name           = azurerm_resource_group.this.name
  tenant_id                     = data.azurerm_client_config.current.tenant_id
  sku_name                      = "standard"
  purge_protection_enabled      = var.key_vault_purge_protection_enabled
  soft_delete_retention_days    = var.key_vault_soft_delete_retention_days
  public_network_access_enabled = true
  tags                          = local.base_tags
}

resource "azurerm_key_vault_access_policy" "terraform_operator" {
  key_vault_id = azurerm_key_vault.this.id
  tenant_id    = data.azurerm_client_config.current.tenant_id
  object_id    = data.azurerm_client_config.current.object_id

  secret_permissions = [
    "Get",
    "List",
    "Set",
    "Delete",
    "Purge",
    "Recover",
  ]
}

resource "azurerm_key_vault_secret" "app_secrets" {
  for_each = local.effective_app_secrets

  name         = replace(each.key, "_", "-")
  value        = each.value
  key_vault_id = azurerm_key_vault.this.id

  depends_on = [azurerm_key_vault_access_policy.terraform_operator]
}

resource "azurerm_postgresql_flexible_server" "this" {
  count = var.enable_postgresql ? 1 : 0

  name                   = coalesce(var.postgresql_server_name, "${var.project_name}-${var.environment}-pg")
  location               = coalesce(var.postgresql_location, azurerm_resource_group.this.location)
  resource_group_name    = azurerm_resource_group.this.name
  version                = var.postgresql_version
  delegated_subnet_id    = null
  private_dns_zone_id    = null
  administrator_login    = var.postgresql_admin_username
  administrator_password = var.postgresql_admin_password
  sku_name               = var.postgresql_sku_name
  storage_mb             = var.postgresql_storage_mb

  public_network_access_enabled = var.postgresql_public_access_enabled

  tags = local.base_tags

  lifecycle {
    ignore_changes = [zone]
  }
}

resource "azurerm_postgresql_flexible_server_database" "this" {
  count = var.enable_postgresql ? 1 : 0

  name      = var.postgresql_database_name
  server_id = azurerm_postgresql_flexible_server.this[0].id
  charset   = "UTF8"
  collation = "en_US.utf8"
}

resource "azurerm_postgresql_flexible_server_firewall_rule" "allow_azure_services" {
  count = var.enable_postgresql && var.postgresql_public_access_enabled ? 1 : 0

  name             = "AllowAzureServices"
  server_id        = azurerm_postgresql_flexible_server.this[0].id
  start_ip_address = "0.0.0.0"
  end_ip_address   = "0.0.0.0"
}

resource "azurerm_role_assignment" "kv_secrets_user" {
  scope                = azurerm_key_vault.this.id
  role_definition_name = "Key Vault Secrets User"
  principal_id         = azurerm_user_assigned_identity.aks.principal_id
}

# Access-policy fallback for workloads using UAMI when the Key Vault is operating
# in access-policy authorization mode (common in mixed/legacy setups).
resource "azurerm_key_vault_access_policy" "aks_workload_identity" {
  key_vault_id = azurerm_key_vault.this.id
  tenant_id    = data.azurerm_client_config.current.tenant_id
  object_id    = azurerm_user_assigned_identity.aks.principal_id

  secret_permissions = [
    "Get",
    "List",
  ]
}

resource "azurerm_databricks_workspace" "this" {
  count = var.enable_databricks ? 1 : 0

  name                = coalesce(var.databricks_workspace_name, "${var.project_name}-${var.environment}-dbw")
  location            = azurerm_resource_group.this.location
  resource_group_name = azurerm_resource_group.this.name
  sku                 = var.databricks_sku
  tags                = local.base_tags
}

resource "azurerm_static_web_app" "this" {
  count = var.enable_static_web_app ? 1 : 0

  name                = coalesce(var.static_web_app_name, "${var.project_name}-${var.environment}-portal")
  resource_group_name = azurerm_resource_group.this.name
  location            = azurerm_resource_group.this.location
  sku_tier            = var.static_web_app_sku_tier
  sku_size            = var.static_web_app_sku_size
  tags                = local.base_tags
}

resource "azurerm_kubernetes_cluster" "this" {
  name                      = var.aks_name
  location                  = local.effective_aks_location
  resource_group_name       = azurerm_resource_group.this.name
  dns_prefix                = "${var.project_name}-${var.environment}"
  kubernetes_version        = var.kubernetes_version
  oidc_issuer_enabled       = var.enable_workload_identity
  workload_identity_enabled = var.enable_workload_identity
  tags                      = local.base_tags

  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.aks.id]
  }

  default_node_pool {
    name       = "system"
    vm_size    = var.node_vm_size
    node_count = var.node_count
  }

  oms_agent {
    log_analytics_workspace_id = azurerm_log_analytics_workspace.this.id
  }

  dynamic "key_vault_secrets_provider" {
    for_each = var.enable_key_vault_csi ? [1] : []
    content {
      secret_rotation_enabled = true
    }
  }

  workload_autoscaler_profile {
    keda_enabled = true
  }
}

resource "azurerm_role_assignment" "aks_pull_acr" {
  scope                = azurerm_container_registry.this.id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_kubernetes_cluster.this.kubelet_identity[0].object_id
}

resource "azurerm_federated_identity_credential" "aks_workload" {
  count = var.enable_workload_identity ? 1 : 0

  name                      = "${var.project_name}-${var.environment}-workload-fic"
  user_assigned_identity_id = azurerm_user_assigned_identity.aks.id
  audience                  = ["api://AzureADTokenExchange"]
  issuer                    = azurerm_kubernetes_cluster.this.oidc_issuer_url
  subject                   = "system:serviceaccount:${local.effective_namespace}:${local.effective_sa_name}"
}

resource "azurerm_dns_zone" "this" {
  count               = var.create_dns_zone ? 1 : 0
  name                = var.dns_zone_name
  resource_group_name = coalesce(var.dns_resource_group_name, azurerm_resource_group.this.name)
  tags                = local.base_tags
}
