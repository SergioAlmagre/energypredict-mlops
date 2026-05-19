locals {
  effective_variables      = merge(var.variables, var.create_azure_service_connection ? { AZURE_SERVICE_CONNECTION = var.azure_service_connection_name } : {})
  secret_variable_names    = toset(nonsensitive(keys(var.secret_variables)))
  duplicate_variable_names = setintersection(toset(keys(local.effective_variables)), local.secret_variable_names)
}

data "azuredevops_project" "this" {
  name = var.azuredevops_project_name
}

resource "azuredevops_serviceendpoint_azurerm" "this" {
  count = var.create_azure_service_connection ? 1 : 0

  project_id            = data.azuredevops_project.this.id
  service_endpoint_name = var.azure_service_connection_name
  description           = var.azure_service_connection_description

  credentials {
    serviceprincipalid  = var.azurerm_spn_clientid
    serviceprincipalkey = var.azurerm_spn_clientsecret
  }

  azurerm_subscription_id   = var.azurerm_subscription_id
  azurerm_subscription_name = var.azurerm_subscription_name
  azurerm_spn_tenantid      = var.azurerm_spn_tenantid

  lifecycle {
    precondition {
      condition = (
        var.azurerm_subscription_id != null &&
        var.azurerm_subscription_name != null &&
        var.azurerm_spn_tenantid != null &&
        var.azurerm_spn_clientid != null &&
        var.azurerm_spn_clientsecret != null
      )
      error_message = "When create_azure_service_connection is true, subscription/tenant/SPN values must be provided."
    }
  }
}

resource "azuredevops_variable_group" "shared" {
  project_id   = data.azuredevops_project.this.id
  name         = var.variable_group_name
  description  = var.description
  allow_access = var.allow_access

  dynamic "variable" {
    for_each = local.effective_variables
    content {
      name  = variable.key
      value = variable.value
    }
  }

  dynamic "variable" {
    for_each = local.secret_variable_names
    content {
      name         = variable.value
      is_secret    = true
      secret_value = var.secret_variables[variable.value]
    }
  }

  lifecycle {
    precondition {
      condition     = length(local.duplicate_variable_names) == 0
      error_message = "variables and secret_variables cannot contain the same keys."
    }
  }
}
