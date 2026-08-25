variable "name" {
  description = "Canonical hostname/resource name for the application host."
  type        = string
}

variable "server_type" {
  description = "Hetzner Cloud server type."
  type        = string
}

variable "image" {
  description = "Hetzner Cloud OS image."
  type        = string
}

variable "location" {
  description = "Hetzner Cloud location code, for example hel1, nbg1, or fsn1."
  type        = string
}

variable "ssh_key_ids" {
  description = "Hetzner SSH key IDs attached to the host."
  type        = list(number)
}

variable "ssh_allowed_cidrs" {
  description = "CIDRs allowed to reach SSH directly. Empty means TCP/22 stays closed from the Internet."
  type        = list(string)
  default     = []
}

variable "labels" {
  description = "Provider labels describing environment, role, ownership, and identity."
  type        = map(string)
}

variable "user_data" {
  description = "Create-time cloud-init payload. Changes are intentionally ignored after creation."
  type        = string
  sensitive   = true
}
