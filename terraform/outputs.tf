output "erp_url" {
  description = "ERP URL protected by Cloudflare Access."
  value       = "https://${var.erp_hostname}"
}

output "ssh_hostname" {
  description = "Administrative SSH hostname protected by Cloudflare Access."
  value       = var.ssh_hostname
}

output "server_id" {
  description = "Hetzner server ID."
  value       = hcloud_server.erp.id
}

output "server_ipv4" {
  description = "Hetzner public IPv4. No ERP HTTP ports are exposed by the firewall."
  value       = hcloud_server.erp.ipv4_address
}

output "cloudflare_tunnel_id" {
  description = "Cloudflare Tunnel ID."
  value       = cloudflare_zero_trust_tunnel_cloudflared.erp.id
}

output "credentials_path" {
  description = "Path on the server containing the generated ERP Administrator and MariaDB credentials."
  value       = "/root/erpnext-credentials.txt"
}
