resource "cloudflare_zero_trust_tunnel_cloudflared" "erp" {
  account_id = var.cloudflare_account_id
  name       = "teplotec-erp"
  config_src = "cloudflare"
}

resource "cloudflare_zero_trust_tunnel_cloudflared_config" "erp" {
  account_id = var.cloudflare_account_id
  tunnel_id  = cloudflare_zero_trust_tunnel_cloudflared.erp.id

  config = {
    ingress = [
      {
        hostname = var.erp_hostname
        service  = "http://127.0.0.1:8080"
      },
      {
        hostname = var.ssh_hostname
        service  = "ssh://127.0.0.1:22"
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
  comment = "ERP via Cloudflare Tunnel - managed by Terraform"
}

resource "cloudflare_dns_record" "ssh" {
  zone_id = var.cloudflare_zone_id
  name    = var.ssh_hostname
  type    = "CNAME"
  content = "${cloudflare_zero_trust_tunnel_cloudflared.erp.id}.cfargotunnel.com"
  proxied = true
  ttl     = 1
  comment = "Administrative SSH via Cloudflare Tunnel - managed by Terraform"
}

resource "cloudflare_zero_trust_access_identity_provider" "erp_otp" {
  account_id = var.cloudflare_account_id
  name       = "TeploTEC ERP one-time PIN"
  type       = "onetimepin"
  config     = {}
}

data "cloudflare_zero_trust_access_identity_providers" "account" {
  account_id = var.cloudflare_account_id
}

locals {
  access_all_emails = concat(
    var.access_trusted_emails,
    var.access_staff_emails,
    var.access_guest_emails,
  )

  cloudflare_identity_provider_ids = [
    for identity_provider in data.cloudflare_zero_trust_access_identity_providers.account.result : identity_provider.id
    if identity_provider.type == "cloudflare"
  ]
}

check "erp_access_has_users" {
  assert {
    condition     = length(local.access_all_emails) > 0
    error_message = "At least one trusted, staff, or guest email must be allowed to access ERP."
  }
}

check "erp_access_emails_are_unique" {
  assert {
    condition     = length(distinct(local.access_all_emails)) == length(local.access_all_emails)
    error_message = "An ERP email may belong to only one Access tier. Move duplicate emails to the desired tier."
  }
}

check "cloudflare_identity_provider_exists" {
  assert {
    condition     = length(local.cloudflare_identity_provider_ids) > 0
    error_message = "Cloudflare identity provider is not enabled for this Zero Trust account."
  }
}

resource "cloudflare_zero_trust_access_policy" "erp_trusted" {
  count = length(var.access_trusted_emails) > 0 ? 1 : 0

  account_id       = var.cloudflare_account_id
  name             = "TeploTEC ERP trusted users"
  decision         = "allow"
  session_duration = var.access_trusted_session_duration

  include = [
    for email_address in var.access_trusted_emails : {
      email = {
        email = email_address
      }
    }
  ]
}

resource "cloudflare_zero_trust_access_policy" "erp_staff" {
  count = length(var.access_staff_emails) > 0 ? 1 : 0

  account_id       = var.cloudflare_account_id
  name             = "TeploTEC ERP staff"
  decision         = "allow"
  session_duration = var.access_staff_session_duration

  include = [
    for email_address in var.access_staff_emails : {
      email = {
        email = email_address
      }
    }
  ]
}

resource "cloudflare_zero_trust_access_policy" "erp_guests" {
  count = length(var.access_guest_emails) > 0 ? 1 : 0

  account_id       = var.cloudflare_account_id
  name             = "TeploTEC ERP guests"
  decision         = "allow"
  session_duration = var.access_guest_session_duration

  include = [
    for email_address in var.access_guest_emails : {
      email = {
        email = email_address
      }
    }
  ]
}

resource "cloudflare_zero_trust_access_policy" "ssh_admins" {
  account_id       = var.cloudflare_account_id
  name             = "TeploTEC SSH trusted admins"
  decision         = "allow"
  session_duration = "24h"

  include = [
    for email_address in var.access_trusted_emails : {
      email = {
        email = email_address
      }
    }
  ]
}

resource "cloudflare_zero_trust_access_application" "erp" {
  account_id = var.cloudflare_account_id
  name       = "ERP"
  domain     = var.erp_hostname
  type       = "self_hosted"

  allowed_idps = concat(
    local.cloudflare_identity_provider_ids,
    [cloudflare_zero_trust_access_identity_provider.erp_otp.id],
  )

  policies = concat(
    length(var.access_trusted_emails) > 0 ? [
      {
        id         = cloudflare_zero_trust_access_policy.erp_trusted[0].id
        precedence = 1
      }
    ] : [],
    length(var.access_staff_emails) > 0 ? [
      {
        id         = cloudflare_zero_trust_access_policy.erp_staff[0].id
        precedence = 2
      }
    ] : [],
    length(var.access_guest_emails) > 0 ? [
      {
        id         = cloudflare_zero_trust_access_policy.erp_guests[0].id
        precedence = 3
      }
    ] : [],
  )
}

resource "cloudflare_zero_trust_access_application" "ssh" {
  account_id = var.cloudflare_account_id
  name       = "SSH"
  domain     = var.ssh_hostname
  type       = "ssh"

  allowed_idps = local.cloudflare_identity_provider_ids

  policies = [
    {
      id         = cloudflare_zero_trust_access_policy.ssh_admins.id
      precedence = 1
    }
  ]
}
