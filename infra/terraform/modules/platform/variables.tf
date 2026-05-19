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

variable "key_vault_app_secrets" {
  type        = map(string)
  default     = {}
  description = "Application and integration secrets to store in Key Vault."
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
