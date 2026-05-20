output "resource_group_name" {
  value = azurerm_resource_group.this.name
}

output "acr_login_server" {
  value = azurerm_container_registry.this.login_server
}

output "aks_name" {
  value = azurerm_kubernetes_cluster.this.name
}

output "aks_resource_group" {
  value = azurerm_resource_group.this.name
}

output "key_vault_name" {
  value = azurerm_key_vault.this.name
}

output "key_vault_uri" {
  value = azurerm_key_vault.this.vault_uri
}

output "user_assigned_identity_client_id" {
  value = azurerm_user_assigned_identity.aks.client_id
}

output "user_assigned_identity_principal_id" {
  value = azurerm_user_assigned_identity.aks.principal_id
}

output "tenant_id" {
  value = data.azurerm_client_config.current.tenant_id
}

output "workload_identity_namespace" {
  value = local.effective_namespace
}

output "workload_identity_service_account_name" {
  value = local.effective_sa_name
}

output "dns_zone_name" {
  value = try(azurerm_dns_zone.this[0].name, null)
}

output "databricks_workspace_name" {
  value = try(azurerm_databricks_workspace.this[0].name, null)
}

output "databricks_workspace_url" {
  value = try(azurerm_databricks_workspace.this[0].workspace_url, null)
}

output "static_web_app_name" {
  value = try(azurerm_static_web_app.this[0].name, null)
}

output "static_web_app_default_host_name" {
  value = try(azurerm_static_web_app.this[0].default_host_name, null)
}

output "postgresql_server_fqdn" {
  value = try(azurerm_postgresql_flexible_server.this[0].fqdn, null)
}

output "postgresql_database_name" {
  value = try(azurerm_postgresql_flexible_server_database.this[0].name, null)
}

output "eventhub_namespace_name" {
  value = try(azurerm_eventhub_namespace.this[0].name, null)
}

output "eventhub_namespace_id" {
  value = try(azurerm_eventhub_namespace.this[0].id, null)
}

output "eventhub_name" {
  value = try(azurerm_eventhub.this[0].name, null)
}

output "eventhub_consumer_group" {
  value = var.enable_eventhub_streaming ? var.eventhub_consumer_group : null
}

output "stream_ingestion_enabled" {
  value = var.stream_ingestion_enabled
}

output "prediction_loop_interval_seconds" {
  value = var.prediction_loop_interval_seconds
}

output "llm_provider" {
  value = var.llm_provider
}

output "llm_model" {
  value = var.llm_model
}

output "llm_endpoint" {
  value = var.llm_endpoint
}
