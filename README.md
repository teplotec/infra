# TeploTEC infrastructure

Terraform for TeploTEC production infrastructure.

The first workload is ERPNext at `https://erp.teplotec.com`.

## Architecture

```text
Browser
  -> Cloudflare Access (exact allowed emails, one-time PIN)
  -> Cloudflare Tunnel
  -> cloudflared on Hetzner CX33
  -> 127.0.0.1:8080
  -> ERPNext / Frappe Docker
     -> MariaDB
     -> Redis
```

The ERPNext HTTP port is bound to loopback only. Hetzner Firewall has no public inbound rules by default. SSH is also closed unless `ssh_allowed_cidrs` is explicitly configured.

## Pinned versions

- Terraform 1.15.8
- Hetzner provider 1.68.0
- Cloudflare provider 5.23.0
- Hetzner server `cx33` in `hel1`
- Ubuntu 24.04
- `frappe_docker` v3.2.1
- ERPNext v16.31.1
- cloudflared 2026.8.2

## GitHub Actions configuration

### Repository secrets

Create these under `Settings -> Secrets and variables -> Actions -> Secrets`:

- `HCLOUD_TOKEN`
- `CLOUDFLARE_API_TOKEN`
- `R2_ACCESS_KEY_ID`
- `R2_SECRET_ACCESS_KEY`

### Repository variables

Create these under `Settings -> Secrets and variables -> Actions -> Variables`:

- `CLOUDFLARE_ACCOUNT_ID`
- `CLOUDFLARE_ZONE_ID`
- `TF_STATE_BUCKET` - recommended: `teplotec-terraform-state`
- `SSH_PUBLIC_KEY` - full `ssh-ed25519 ...` public key
- `ACCESS_ALLOWED_EMAILS_JSON` - JSON array, for example `["admin@teplotec.com"]`

## Hetzner token

In the Hetzner Cloud project:

`Security -> API Tokens -> Generate API Token`

Create `github-actions-terraform` with **Read & Write** permission and save the token as `HCLOUD_TOKEN`.

## Cloudflare API token

Create a scoped API token for the TeploTEC account and `teplotec.com` zone with these permissions:

Account permissions:

- Cloudflare Tunnel - Edit
- Access: Apps and Policies - Edit
- Access: Organizations, Identity Providers, and Groups - Edit

Zone permissions:

- DNS - Edit

Save it as `CLOUDFLARE_API_TOKEN`.

## R2 Terraform state

Create an R2 bucket named `teplotec-terraform-state` (or another name and set `TF_STATE_BUCKET`).

Create an R2 API token scoped to that bucket with Object Read & Write. Save the generated S3 credentials as:

- `R2_ACCESS_KEY_ID`
- `R2_SECRET_ACCESS_KEY`

Terraform uses the S3 backend against the R2 S3-compatible endpoint and enables the S3 lockfile. GitHub Actions also serializes Terraform runs with a concurrency group.

Treat the state bucket as sensitive. Terraform state contains infrastructure metadata and the Cloudflare Tunnel credential used to bootstrap `cloudflared`.

## SSH key

Generate a dedicated key locally:

```bash
ssh-keygen -t ed25519 -f ~/.ssh/teplotec -C "teplotec-infra"
cat ~/.ssh/teplotec.pub
```

Put only the public key into `SSH_PUBLIC_KEY`. Keep the private key local.

SSH is deliberately blocked by the Hetzner firewall by default. If emergency SSH is needed, set `ssh_allowed_cidrs` through Terraform to a narrow CIDR. The Hetzner web console remains available independently.

## Workflow

Pull requests touching Terraform run:

```text
terraform fmt -check
terraform init
terraform validate
terraform plan
```

Production changes are not automatically applied after merge. Run `Terraform Apply` manually from the `main` branch after reviewing the plan.

## First deployment

1. Add the secrets and variables above.
2. Merge the infrastructure PR.
3. Open `Actions -> Terraform Apply -> Run workflow` on `main`.
4. Type `APPLY` into the confirmation field and start the workflow.
5. Wait for cloud-init to install Docker, start ERPNext, create the site, and start `cloudflared`.
6. Open `https://erp.teplotec.com` and authenticate through Cloudflare Access.

ERPNext credentials are generated on the server rather than in Terraform. Retrieve them from the Hetzner web console:

```bash
sudo cat /root/erpnext-credentials.txt
```

The file is mode `0600` and contains the ERPNext `Administrator` password and MariaDB root password.

## Notes

- Hetzner server delete/rebuild protection is enabled.
- Hetzner backups are currently disabled to keep the initial deployment lean. Add a backup policy before ERPNext contains business-critical data.
- Do not point `erp.teplotec.com` directly at the Hetzner public IP. It is intentionally routed only through Cloudflare Tunnel.
