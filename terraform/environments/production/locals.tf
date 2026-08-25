locals {
  environment = "production"

  hetzner_location_metadata = {
    hel1 = {
      name         = "helsinki"
      network_zone = "eu-central"
    }
    nbg1 = {
      name         = "nuremberg"
      network_zone = "eu-central"
    }
    fsn1 = {
      name         = "falkenstein"
      network_zone = "eu-central"
    }
  }[var.application_server_location]

  application_host_name = format(
    "teplotec-%s-%s-%s-application-%02d",
    local.environment,
    local.hetzner_location_metadata.network_zone,
    local.hetzner_location_metadata.name,
    var.application_host_sequence,
  )
  origin_tunnel_name = "teplotec-${local.environment}-origin"

  common_labels = {
    project       = "teplotec"
    environment   = local.environment
    provider      = "hetzner"
    network_zone  = local.hetzner_location_metadata.network_zone
    location      = local.hetzner_location_metadata.name
    location_code = var.application_server_location
    role          = "application"
    managed_by    = "terraform"
  }
}
