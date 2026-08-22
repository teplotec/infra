# Cloudflare R2 is used through its S3-compatible API with Access Key ID and Secret Access Key.
# The original R2 API token is not used by Terraform.
terraform {
  backend "s3" {}
}
