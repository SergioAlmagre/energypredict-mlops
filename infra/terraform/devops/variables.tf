variable "azuredevops_org_service_url" {
  type        = string
  description = "Azure DevOps organization URL, for example: https://dev.azure.com/<org>."
}

variable "azuredevops_pat" {
  type        = string
  sensitive   = true
  description = "Azure DevOps PAT with permissions to manage variable groups."
}

variable "azuredevops_project_name" {
  type        = string
  description = "Azure DevOps project name where the variable group will be created."
}

variable "variable_group_name" {
  type        = string
  default     = "energypredict-shared"
  description = "Name of the Azure DevOps variable group to create/manage."
}

variable "description" {
  type        = string
  default     = "Managed by Terraform"
  description = "Description for the variable group."
}

variable "allow_access" {
  type        = bool
  default     = true
  description = "Allow all pipelines in the project to access this variable group."
}

variable "variables" {
  type        = map(string)
  default     = {}
  description = "Non-secret variables for the variable group."
}

variable "secret_variables" {
  type        = map(string)
  default     = {}
  sensitive   = true
  description = "Secret variables for the variable group."
}

variable "create_azure_service_connection" {
  type        = bool
  default     = false
  description = "When true, creates an AzureRM service connection in Azure DevOps."
}

variable "azure_service_connection_name" {
  type        = string
  default     = "energypredict-azure-rm"
  description = "Name for the AzureRM service connection."
}

variable "azure_service_connection_description" {
  type        = string
  default     = "Managed by Terraform"
  description = "Description for the AzureRM service connection."
}

variable "azurerm_subscription_id" {
  type        = string
  default     = null
  description = "Azure subscription ID used by the service connection."
}

variable "azurerm_subscription_name" {
  type        = string
  default     = null
  description = "Azure subscription display name used by the service connection."
}

variable "azurerm_spn_tenantid" {
  type        = string
  default     = null
  description = "Tenant ID for the service principal used by the service connection."
}

variable "azurerm_spn_clientid" {
  type        = string
  default     = null
  description = "Client ID (application ID) for the service principal used by the service connection."
}

variable "azurerm_spn_clientsecret" {
  type        = string
  default     = null
  sensitive   = true
  description = "Client secret for the service principal used by the service connection."
}
