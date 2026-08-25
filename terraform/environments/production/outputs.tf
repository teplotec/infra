output "erp_url" {
  description = "ERP URL protected by Cloudflare Access."
  value       = "https://${var.erp_hostname}"
}

output "project_url" {
  description = "Project application URL protected by Cloudflare Access."
  value       = "https://${var.project_hostname}"
}

output "groundloop_api_url" {
  description = "GroundLoop API URL routed through the production Cloudflare origin tunnel."
  value       = "https://${var.groundloop_api_hostname}"
}

output "ssh_hostname" {
  description = "Administrative SSH hostname protected by Cloudflare Access."
  value       = var.ssh_hostname
}

output "application_host_name" {
  description = "Canonical production application host name."
  value       = local.application_host_name
}

output "server_id" {
  description = "Hetzner production application host ID."
  value       = module.application_host.server_id
}

output "server_ipv4" {
  description = "Hetzner public IPv4. Application HTTP ports are not exposed by the firewall."
  value       = module.application_host.ipv4_address
}

output "cloudflare_tunnel_id" {
  description = "Production Cloudflare origin tunnel ID."
  value       = cloudflare_zero_trust_tunnel_cloudflared.platform.id
}

output "credentials_path" {
  description = "Path on the application host containing generated ERP Administrator and MariaDB credentials."
  value       = "/root/erpnext-credentials.txt"
}
