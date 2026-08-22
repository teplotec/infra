# Cloudflare R2 is used through its S3-compatible API with Access Key ID and Secret Access Key.
# The original R2 API token is not used by Terraform.
# This backend is shared by plan and apply so failed applies can be diagnosed safely from state.
terraform {
  backend "s3" {}
}
