resource "random_bytes" "tunnel_secret" {
  length = 32
}

resource "cloudflare_zero_trust_tunnel_cloudflared" "erp" {
  account_id    = var.cloudflare_account_id
  name          = "teplotec-erp"
  config_src    = "cloudflare"
  tunnel_secret = random_bytes.tunnel_secret.base64
}

resource "cloudflare_zero_trust_tunnel_cloudflared_config" "erp" {
  account_id = var.cloudflare_account_id
  tunnel_id  = cloudflare_zero_trust_tunnel_cloudflared.erp.id
  source     = "cloudflare"

  config = {
    ingress = [
      {
        hostname = var.erp_hostname
        service  = "http://127.0.0.1:8080"
      },
      {
        service = "http_status:404"
      }
    ]
  }
}

data "cloudflare_zero_trust_tunnel_cloudflared_token" "erp" {
  account_id = var.cloudflare_account_id
  tunnel_id  = cloudflare_zero_trust_tunnel_cloudflared.erp.id
}

resource "cloudflare_dns_record" "erp" {
  zone_id = var.cloudflare_zone_id
  name    = var.erp_hostname
  type    = "CNAME"
  content = "${cloudflare_zero_trust_tunnel_cloudflared.erp.id}.cfargotunnel.com"
  proxied = true
  ttl     = 1
  comment = "ERPNext via Cloudflare Tunnel - managed by Terraform"
}

resource "cloudflare_zero_trust_access_identity_provider" "erp_otp" {
  account_id = var.cloudflare_account_id
  name       = "TeploTEC ERP one-time PIN"
  type       = "onetimepin"
  config     = {}
}

resource "cloudflare_zero_trust_access_policy" "erp" {
  account_id = var.cloudflare_account_id
  name       = "TeploTEC ERP allowed emails"
  decision   = "allow"

  include = [
    for email_address in var.access_allowed_emails : {
      email = {
        email = email_address
      }
    }
  ]
}

resource "cloudflare_zero_trust_access_application" "erp" {
  account_id = var.cloudflare_account_id
  name       = "TeploTEC ERPNext"
  domain     = var.erp_hostname
  type       = "self_hosted"

  allowed_idps = [cloudflare_zero_trust_access_identity_provider.erp_otp.id]

  policies = [
    {
      id         = cloudflare_zero_trust_access_policy.erp.id
      precedence = 1
    }
  ]
}
