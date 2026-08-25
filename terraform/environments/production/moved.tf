# State moves are explicit because this environment root and application host
# module replace the original ERP-centric root resources without replacing
# physical resources.
moved {
  from = hcloud_firewall.erp
  to   = module.application_host.hcloud_firewall.this
}

moved {
  from = hcloud_server.erp
  to   = module.application_host.hcloud_server.this
}

moved {
  from = cloudflare_zero_trust_tunnel_cloudflared.erp
  to   = cloudflare_zero_trust_tunnel_cloudflared.platform
}

moved {
  from = cloudflare_zero_trust_tunnel_cloudflared_config.erp
  to   = cloudflare_zero_trust_tunnel_cloudflared_config.platform
}
