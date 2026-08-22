# TeploTEC infrastructure

Terraform for TeploTEC production infrastructure.

The first workload is ERPNext at `https://erp.teplotec.com`.

## Architecture

```text
Browser
  -> Cloudflare Access
     -> Cloudflare account session for configured users
     -> One-time PIN fallback
  -> Cloudflare Tunnel
  -> cloudflared on Hetzner CX33
  -> 127.0.0.1:8080
  -> ERPNext / Frappe Docker
     -> MariaDB
     -> Redis

Administrator terminal
  -> ssh.teplotec.com
  -> Cloudflare Access
  -> Cloudflare Tunnel
  -> localhost:22
```

The ERP HTTP port is bound to loopback only. Hetzner Firewall has no public inbound rules by default. Public SSH ingress remains closed; administrative SSH is routed through Cloudflare Tunnel.

## Cloudflare Access sessions

ERP access is split into three email tiers:

- Trusted users: 30 days (`720h`)
- Staff: 7 days (`168h`)
- Guests / external users: 24 hours (`24h`)

Users can authenticate either with the Cloudflare identity provider or with the one-time PIN identity provider. A trusted user whose email is also a member of the TeploTEC Cloudflare account can use the existing Cloudflare session instead of receiving an email PIN.

SSH only allows trusted emails and only exposes the Cloudflare identity provider. One-time PIN is intentionally not enabled for SSH.

An email must belong to only one ERP tier.

## Pinned versions

- Terraform 1.15.8
- Hetzner provider 1.68.0
- Cloudflare provider 5.23.0
- Hetzner server `cx33` in `hel1`
- Ubuntu 24.04
- `frappe_docker` v3.2.1
- ERPNext v16.31.1
- cloudflared 2026.8.2 on the server

## GitHub Actions configuration

Use repository-level secrets and variables under `Settings -> Secrets and variables -> Actions`. Environment and organization secrets/variables are not required for the Terraform deployment.

### Repository secrets

- `HCLOUD_TOKEN`
- `CLOUDFLARE_API_TOKEN`
- `R2_ACCESS_KEY_ID`
- `R2_SECRET_ACCESS_KEY`
- `ERPNEXT_ADMIN_PASSWORD` - used only by the separate ERP Admin workflow

### Repository variables

- `CLOUDFLARE_ACCOUNT_ID`
- `CLOUDFLARE_ZONE_ID`
- `TF_STATE_BUCKET` - recommended: `teplotec-terraform-state`
- `SSH_PUBLIC_KEY` - full `ssh-ed25519 ...` public key
- `ACCESS_TRUSTED_EMAILS_JSON` - JSON array, e.g. `["owner@example.com"]`
- `ACCESS_STAFF_EMAILS_JSON` - JSON array, e.g. `["employee@example.com"]`
- `ACCESS_GUEST_EMAILS_JSON` - JSON array, e.g. `[]`

All three Access email variables must exist. Use `[]` for a tier that currently has no users.

## Hetzner token

In the Hetzner Cloud project:

`Security -> API Tokens -> Generate API Token`

Create `github-actions-terraform` with **Read & Write** permission and save the token as `HCLOUD_TOKEN`. Hetzner displays the full token only once.

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

Terraform uses those two S3 credentials directly. The original R2 API token used to generate them is not stored in GitHub and is not required by the Terraform workflow.

Terraform uses the S3 backend against the R2 S3-compatible endpoint and enables the S3 lockfile. GitHub Actions also serializes Terraform runs with a concurrency group.

Treat the state bucket as sensitive. Terraform state contains infrastructure metadata and the Cloudflare Tunnel credential used to bootstrap `cloudflared`.

## SSH key

Generate a dedicated key locally:

```bash
ssh-keygen -t ed25519 -f ~/.ssh/teplotec -C "teplotec-infra"
cat ~/.ssh/teplotec.pub
```

Put only the public key into `SSH_PUBLIC_KEY`. Keep the private key local.

### SSH through Cloudflare Access

On macOS install the client-side connector once:

```bash
brew install cloudflared
```

Find the executable:

```bash
command -v cloudflared
```

Add this to `~/.ssh/config`, adjusting the `ProxyCommand` path if Homebrew installed `cloudflared` elsewhere:

```sshconfig
Host teplotec-erp
  HostName ssh.teplotec.com
  User root
  IdentityFile ~/.ssh/teplotec
  ProxyCommand /opt/homebrew/bin/cloudflared access ssh --hostname %h
```

Then connect with:

```bash
ssh teplotec-erp
```

`cloudflared` opens a browser when Cloudflare authentication is required. Once a valid Cloudflare Access session exists, SSH continues in the normal terminal. Hetzner TCP/22 remains closed to the public Internet.

## ERP administrator password

The initial Administrator password is generated on the server rather than stored in Terraform state:

```bash
sudo cat /root/erpnext-credentials.txt
```

Application passwords are managed separately from Terraform. The `ERP Admin` GitHub workflow reads `ERPNEXT_ADMIN_PASSWORD` from GitHub Secrets and updates ERP locally on the CX33 self-hosted runner.

## ERP Admin self-hosted runner

The admin workflow deliberately does not automate through remote SSH. A small GitHub self-hosted runner lives on the CX33 and connects outbound to GitHub. The runner is not in the `docker` group and does not receive general sudo access. It can only run the root-owned `/usr/local/sbin/teplotec-erp-admin` command, which accepts a small whitelist of operations.

One-time setup after `ssh teplotec-erp` works:

1. Clone this repository on your Mac and copy the two setup scripts to the server:

```bash
gh repo clone teplotec/infra
cd infra
scp scripts/erp-admin scripts/install-erp-admin teplotec-erp:/tmp/
ssh teplotec-erp 'sudo bash /tmp/install-erp-admin /tmp/erp-admin'
```

2. In GitHub open `teplotec/infra -> Settings -> Actions -> Runners -> New self-hosted runner`. Select Linux x64 and use the commands GitHub generates. Run the download/extract/config commands as the `github-runner` user in `/home/github-runner/actions-runner` and add the custom label `teplotec-erp-admin` to the `config.sh` command.

3. Install and start the runner service as root:

```bash
cd /home/github-runner/actions-runner
sudo ./svc.sh install github-runner
sudo ./svc.sh start
sudo ./svc.sh status
```

4. Add the repository secret `ERPNEXT_ADMIN_PASSWORD` with the Administrator password you want ERP to use.

5. Open `Actions -> ERP Admin -> Run workflow`, select `sync-admin-password`, enter `APPLY`, and run it.

The same workflow also exposes guarded `status`, `restart`, and `migrate` operations. `status` is read-only; mutating operations require the explicit `APPLY` confirmation.

## Workflow

Pull requests touching Terraform run syntax, provider-schema validation, and a real plan when all credentials are configured.

Production infrastructure changes are not automatically applied after merge. Run `Terraform Apply` manually from the `main` branch after reviewing the plan.

ERP application administration uses the separate `ERP Admin` workflow and self-hosted runner described above.

## First deployment

1. Add the secrets and variables above.
2. Review the real Terraform plan in the pull request.
3. Merge the infrastructure PR.
4. Open `Actions -> Terraform Apply -> Run workflow` on `main`.
5. Type `APPLY` into the confirmation field and start the workflow.
6. Wait for cloud-init to install Docker, start ERPNext, create the site, and start `cloudflared`.
7. Open `https://erp.teplotec.com` and authenticate through Cloudflare Access.

## Notes

- Hetzner server delete/rebuild protection is enabled.
- Hetzner backups are currently disabled to keep the initial deployment lean. Add a backup policy before ERPNext contains business-critical data.
- Do not point `erp.teplotec.com` or `ssh.teplotec.com` directly at the Hetzner public IP. They are intentionally routed only through Cloudflare Tunnel.
