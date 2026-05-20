output "resource_group_name" {
  value = module.platform.resource_group_name
}

output "acr_login_server" {
  value = module.platform.acr_login_server
}

output "aks_name" {
  value = module.platform.aks_name
}

output "key_vault_name" {
  value = module.platform.key_vault_name
}

output "key_vault_uri" {
  value = module.platform.key_vault_uri
}

output "identity_client_id" {
  value = module.platform.user_assigned_identity_client_id
}

output "tenant_id" {
  value = module.platform.tenant_id
}

output "workload_identity_namespace" {
  value = module.platform.workload_identity_namespace
}

output "workload_identity_service_account_name" {
  value = module.platform.workload_identity_service_account_name
}

output "databricks_workspace_name" {
  value = module.platform.databricks_workspace_name
}

output "databricks_workspace_url" {
  value = module.platform.databricks_workspace_url
}

output "static_web_app_name" {
  value = module.platform.static_web_app_name
}

output "static_web_app_default_host_name" {
  value = module.platform.static_web_app_default_host_name
}

output "postgresql_server_fqdn" {
  value = module.platform.postgresql_server_fqdn
}

output "postgresql_database_name" {
  value = module.platform.postgresql_database_name
}

output "eventhub_namespace_name" {
  value = module.platform.eventhub_namespace_name
}

output "eventhub_namespace_id" {
  value = module.platform.eventhub_namespace_id
}

output "eventhub_name" {
  value = module.platform.eventhub_name
}

output "eventhub_consumer_group" {
  value = module.platform.eventhub_consumer_group
}

output "stream_ingestion_enabled" {
  value = module.platform.stream_ingestion_enabled
}

output "prediction_loop_interval_seconds" {
  value = module.platform.prediction_loop_interval_seconds
}

output "llm_provider" {
  value = module.platform.llm_provider
}

output "llm_model" {
  value = module.platform.llm_model
}

output "llm_endpoint" {
  value = module.platform.llm_endpoint
}
