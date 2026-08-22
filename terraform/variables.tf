variable "cloudflare_account_id" {
  description = "Cloudflare account ID that owns teplotec.com and Zero Trust."
  type        = string
}

variable "cloudflare_zone_id" {
  description = "Cloudflare zone ID for teplotec.com."
  type        = string
}

variable "access_trusted_emails" {
  description = "Trusted ERP users. They receive the longest Cloudflare Access session."
  type        = list(string)
  default     = []
}

variable "access_staff_emails" {
  description = "Regular ERP staff users."
  type        = list(string)
  default     = []
}

variable "access_guest_emails" {
  description = "Temporary or external ERP users."
  type        = list(string)
  default     = []
}

variable "access_trusted_session_duration" {
  description = "Cloudflare Access session duration for trusted ERP users."
  type        = string
  default     = "720h"
}

variable "access_staff_session_duration" {
  description = "Cloudflare Access session duration for regular ERP staff."
  type        = string
  default     = "168h"
}

variable "access_guest_session_duration" {
  description = "Cloudflare Access session duration for temporary or external ERP users."
  type        = string
  default     = "24h"
}

variable "ssh_public_key" {
  description = "Public SSH key installed on the Hetzner server."
  type        = string
}

variable "ssh_allowed_cidrs" {
  description = "CIDRs allowed to connect to SSH. Empty by default, so port 22 is closed from the Internet."
  type        = list(string)
  default     = []
}

variable "erp_hostname" {
  description = "Public ERPNext hostname protected by Cloudflare Access."
  type        = string
  default     = "erp.teplotec.com"
}

variable "ssh_hostname" {
  description = "Cloudflare Access hostname for administrative SSH over the existing tunnel."
  type        = string
  default     = "ssh.teplotec.com"
}

variable "server_type" {
  description = "Hetzner Cloud server type."
  type        = string
  default     = "cx33"
}

variable "server_location" {
  description = "Hetzner Cloud location."
  type        = string
  default     = "hel1"
}

variable "server_image" {
  description = "Hetzner Cloud OS image."
  type        = string
  default     = "ubuntu-24.04"
}

variable "frappe_docker_version" {
  description = "Pinned frappe_docker release."
  type        = string
  default     = "v3.2.1"
}

variable "erpnext_version" {
  description = "Pinned ERPNext release."
  type        = string
  default     = "v16.31.1"
}

variable "cloudflared_version" {
  description = "Pinned cloudflared container release."
  type        = string
  default     = "2026.8.2"
}
