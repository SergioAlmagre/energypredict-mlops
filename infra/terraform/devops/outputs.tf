output "project_id" {
  value = data.azuredevops_project.this.id
}

output "variable_group_id" {
  value = azuredevops_variable_group.shared.id
}

output "variable_group_name" {
  value = azuredevops_variable_group.shared.name
}

output "azure_service_connection_id" {
  value = try(azuredevops_serviceendpoint_azurerm.this[0].id, null)
}

output "azure_service_connection_name" {
  value = var.create_azure_service_connection ? var.azure_service_connection_name : null
}
