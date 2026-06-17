variable "environment" {
  type = string
}

variable "project_name" {
  type = string
}

variable "location" {
  type = string
}

variable "resource_group_name" {
  type = string
}

variable "acr_name" {
  type = string
}

variable "aks_name" {
  type = string
}

variable "key_vault_name" {
  type = string
}

variable "key_vault_purge_protection_enabled" {
  type        = bool
  default     = true
  description = "Enable purge protection for Key Vault. Keep true in prod; use false in ephemeral dev/test environments."
}

variable "key_vault_soft_delete_retention_days" {
  type        = number
  default     = 7
  description = "Soft-delete retention days for Key Vault. Azure requires at least 7 days."
}

variable "log_analytics_name" {
  type = string
}

variable "dns_zone_name" {
  type    = string
  default = null
}

variable "create_dns_zone" {
  type    = bool
  default = false
}

variable "dns_resource_group_name" {
  type    = string
  default = null
}

variable "kubernetes_version" {
  type    = string
  default = null
}

variable "aks_location" {
  type    = string
  default = null
}

variable "node_count" {
  type    = number
  default = 2
}

variable "node_vm_size" {
  type    = string
  default = "Standard_D2s_v5"
}

variable "tags" {
  type    = map(string)
  default = {}
}

variable "enable_databricks" {
  type    = bool
  default = false
}

variable "databricks_workspace_name" {
  type    = string
  default = null
}

variable "databricks_sku" {
  type    = string
  default = "standard"
}

variable "enable_static_web_app" {
  type    = bool
  default = false
}

variable "static_web_app_name" {
  type    = string
  default = null
}

variable "static_web_app_sku_tier" {
  type    = string
  default = "Free"
}

variable "static_web_app_sku_size" {
  type    = string
  default = "Free"
}

variable "enable_workload_identity" {
  type    = bool
  default = true
}

variable "enable_key_vault_csi" {
  type    = bool
  default = true
}

variable "kubernetes_namespace" {
  type    = string
  default = null
}

variable "workload_identity_service_account_name" {
  type    = string
  default = null
}

variable "workload_identity_additional_service_account_names" {
  type        = list(string)
  default     = []
  description = "Additional Kubernetes ServiceAccount names allowed to use the AKS managed identity."
}

variable "key_vault_app_secrets" {
  type        = map(string)
  default     = {}
  description = "Application and integration secrets to store in Key Vault."
}

variable "enable_model_storage" {
  type        = bool
  default     = true
  description = "Provision Azure Blob containers for model artifacts, registry cache and processed data."
}

variable "model_storage_account_name" {
  type    = string
  default = null
}

variable "model_storage_replication_type" {
  type    = string
  default = "LRS"
}

variable "blob_models_container" {
  type    = string
  default = "models"
}

variable "blob_registry_container" {
  type    = string
  default = "registry"
}

variable "blob_processed_container" {
  type    = string
  default = "processed"
}

variable "enable_postgresql" {
  type    = bool
  default = false
}

variable "postgresql_server_name" {
  type    = string
  default = null
}

variable "postgresql_location" {
  type    = string
  default = null
}

variable "postgresql_database_name" {
  type    = string
  default = "energypredict"
}

variable "postgresql_admin_username" {
  type    = string
  default = null
}

variable "postgresql_admin_password" {
  type      = string
  default   = null
  sensitive = true
}

variable "postgresql_sku_name" {
  type    = string
  default = "B_Standard_B1ms"
}

variable "postgresql_storage_mb" {
  type    = number
  default = 32768
}

variable "postgresql_version" {
  type    = string
  default = "16"
}

variable "postgresql_public_access_enabled" {
  type    = bool
  default = true
}

variable "enable_eventhub_streaming" {
  type    = bool
  default = false
}

variable "eventhub_namespace_name" {
  type    = string
  default = null
}

variable "eventhub_namespace_sku" {
  type    = string
  default = "Standard"
}

variable "eventhub_namespace_capacity" {
  type    = number
  default = 1
}

variable "eventhub_name" {
  type    = string
  default = null
}

variable "eventhub_partition_count" {
  type    = number
  default = 2
}

variable "eventhub_message_retention_days" {
  type    = number
  default = 1
}

variable "eventhub_consumer_group" {
  type    = string
  default = "energypredict-consumer"
}

variable "stream_ingestion_enabled" {
  type    = bool
  default = false
}

variable "prediction_loop_interval_seconds" {
  type    = number
  default = 10
}

variable "llm_provider" {
  type    = string
  default = "none"
}

variable "llm_model" {
  type    = string
  default = ""
}

variable "llm_endpoint" {
  type    = string
  default = ""
}
