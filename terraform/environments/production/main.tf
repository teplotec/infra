resource "hcloud_ssh_key" "admin" {
  name       = "teplotec-infra"
  public_key = var.ssh_public_key
}

module "application_host" {
  source = "../../modules/hetzner-application-host"

  name              = local.application_host_name
  server_type       = var.application_server_type
  image             = var.application_server_image
  location          = var.application_server_location
  ssh_key_ids       = [hcloud_ssh_key.admin.id]
  ssh_allowed_cidrs = var.ssh_allowed_cidrs
  labels            = local.common_labels

  user_data = templatefile("${path.module}/templates/cloud-init.yaml.tftpl", {
    bootstrap_script = base64encode(templatefile("${path.module}/templates/erp-bootstrap.sh.tftpl", {
      erp_hostname          = var.erp_hostname
      erpnext_version       = var.erpnext_version
      frappe_docker_version = var.frappe_docker_version
      cloudflared_version   = var.cloudflared_version
      tunnel_token          = data.cloudflare_zero_trust_tunnel_cloudflared_token.platform.token
    }))
  })
}
