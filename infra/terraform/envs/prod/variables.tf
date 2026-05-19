variable "environment" { type = string }
variable "project_name" { type = string }
variable "location" { type = string }
variable "resource_group_name" { type = string }
variable "acr_name" { type = string }
variable "aks_name" { type = string }
variable "key_vault_name" { type = string }
variable "log_analytics_name" { type = string }
variable "create_dns_zone" { type = bool }
variable "dns_zone_name" { type = string }
variable "dns_resource_group_name" { type = string }
variable "kubernetes_version" { type = string }
variable "node_count" { type = number }
variable "node_vm_size" { type = string }
variable "tags" { type = map(string) }
variable "enable_databricks" { type = bool }
variable "databricks_workspace_name" { type = string }
variable "databricks_sku" { type = string }
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
  default = "Standard"
}
variable "static_web_app_sku_size" {
  type    = string
  default = "Standard"
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
  type = map(string)
}
variable "enable_postgresql" { type = bool }
variable "postgresql_server_name" { type = string }
variable "postgresql_database_name" { type = string }
variable "postgresql_admin_username" { type = string }
variable "postgresql_admin_password" {
  type      = string
  sensitive = true
}
variable "postgresql_sku_name" { type = string }
variable "postgresql_storage_mb" { type = number }
variable "postgresql_version" { type = string }
variable "postgresql_public_access_enabled" { type = bool }
