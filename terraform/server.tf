resource "hcloud_ssh_key" "admin" {
  name       = "teplotec-infra"
  public_key = var.ssh_public_key
}

resource "hcloud_firewall" "erp" {
  name = "teplotec-erp"

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

resource "hcloud_server" "erp" {
  name         = "teplotec-erp"
  server_type  = var.server_type
  image        = var.server_image
  location     = var.server_location
  ssh_keys     = [hcloud_ssh_key.admin.id]
  firewall_ids = [hcloud_firewall.erp.id]

  delete_protection  = true
  rebuild_protection = true
  backups            = false

  public_net {
    ipv4_enabled = true
    ipv6_enabled = true
  }

  labels = {
    project     = "teplotec"
    application = "erpnext"
    environment = "production"
    managed_by  = "terraform"
  }
}
