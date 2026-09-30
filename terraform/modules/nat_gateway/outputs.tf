output "nat_gateway_id" {
  value       = azurerm_nat_gateway.nat_gw.id
  description = "NAT Gateway ID"
}

output "public_ip_address" {
  value       = azurerm_public_ip.nat_pip.ip_address
  description = "Static Egress Public IP Address"
}
