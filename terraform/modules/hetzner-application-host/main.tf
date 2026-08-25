resource "hcloud_firewall" "this" {
  name = var.name

  dynamic "rule" {
    for_each = length(var.ssh_allowed_cidrs) > 0 ? [1] : []

    content {
      direction   = "in"
      protocol    = "tcp"
      port        = "22"
      source_ips  = var.ssh_allowed_cidrs
      description = "SSH from explicitly allowed CIDRs"
    }
  }
}

resource "hcloud_server" "this" {
  name         = var.name
  server_type  = var.server_type
  image        = var.image
  location     = var.location
  ssh_keys     = var.ssh_key_ids
  firewall_ids = [hcloud_firewall.this.id]

  delete_protection  = true
  rebuild_protection = true
  backups            = false

  public_net {
    ipv4_enabled = true
    ipv6_enabled = true
  }

  labels    = var.labels
  user_data = var.user_data

  # cloud-init is a create-time bootstrap. Repeatable host lifecycle belongs
  # to Ansible; changing a template must not implicitly replace production.
  lifecycle {
    ignore_changes = [user_data]
  }
}
