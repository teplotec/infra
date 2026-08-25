output "server_id" {
  description = "Hetzner server ID."
  value       = hcloud_server.this.id
}

output "ipv4_address" {
  description = "Hetzner public IPv4 address. Application HTTP ports remain closed by firewall policy."
  value       = hcloud_server.this.ipv4_address
}

output "firewall_id" {
  description = "Hetzner firewall ID attached to the host."
  value       = hcloud_firewall.this.id
}
