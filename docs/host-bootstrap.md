# Production application host lifecycle

TeploTEC deliberately separates durable cloud infrastructure, first-boot runtime bootstrap, repeatable host configuration, workload deployment, and application data.

The canonical production application host is `teplotec-production-eu-central-helsinki-application-01`.

## Naming convention

Host names follow:

```text
teplotec-<environment>-<network-zone>-<location>-<role>-<ordinal>
```

Current value:

```text
teplotec-production-eu-central-helsinki-application-01
```

- `teplotec`: organization/project
- `production`: environment
- `eu-central`: Hetzner network zone
- `helsinki`: human-readable location
- `application`: shared application-compute role
- `01`: ordinal within that environment, network zone, location, and role

The provider-facing location code remains `hel1`. Terraform derives `eu-central` and `helsinki` from that provider code so network zone and location cannot contradict each other. Provider code and human-readable topology are also stored as labels.

## Responsibility split

### Terraform

Terraform owns external and durable infrastructure resources:

- Hetzner CX33 shared application host and firewall
- SSH public key attachment
- Cloudflare DNS, platform Tunnel, and Access resources
- Terraform remote state

The production Terraform root is `terraform/environments/production`. Reusable host infrastructure lives under `terraform/modules/hetzner-application-host`.

Terraform does not own GitHub runner registration tokens or application passwords.

### cloud-init

`terraform/environments/production/templates/cloud-init.yaml.tftpl` and the ERP bootstrap template are used only during first server creation to make the host usable and bootstrap the first ERP workload:

- install Docker
- clone the pinned `frappe_docker` checkout
- create the initial ERPNext Compose runtime
- create the initial site if necessary
- start `cloudflared`

Changing cloud-init for an already-created host is not the normal host-configuration mechanism. Repeatable host configuration after creation belongs in Ansible.

### Ansible

`ansible/playbooks/app-host.yml` owns repeatable host administration configuration:

- the unprivileged `github-runner` user
- `/usr/local/sbin/teplotec-erp-admin`
- the restricted sudo policy for that ERP helper
- the pinned GitHub Actions runner installation
- the repository runner service

The host is generic; the ERP admin helper and its runner capability label remain workload-specific.

### GitHub Actions and GHCR

GitHub-hosted runners build and test immutable application images and publish them to registries where appropriate.

The CX33 self-hosted runner is a local deployment/control agent only. It is not a general-purpose privileged build runner.

## What survives a host replacement

| Item | Source of truth | Survives replacing the VM? | Manual re-entry? |
| --- | --- | --- | --- |
| Hetzner API token | GitHub Secret `HCLOUD_TOKEN` | yes | no |
| Cloudflare API token | GitHub Secret `CLOUDFLARE_API_TOKEN` | yes | no |
| R2 state credentials | GitHub Secrets | yes | no |
| Terraform state | Cloudflare R2 | yes | no |
| Cloudflare Tunnel identity/config | Terraform + Cloudflare | yes | no |
| cloudflared tunnel token used by the connector | derived by Terraform from Cloudflare | yes | no |
| SSH public key | GitHub variable `SSH_PUBLIC_KEY` | yes | no |
| operator SSH private key | operator machine | yes | no, if the local key is retained |
| ERP Administrator secret used by workflows | GitHub Secret `ERPNEXT_ADMIN_PASSWORD` | yes | no |
| generated ERP DB password in `/root/erpnext-credentials.txt` | VM-local | no | no; a replacement demo host can generate a new one |
| generated initial ERP Administrator password in `/root/erpnext-credentials.txt` | VM-local | no | no if `ERPNEXT_ADMIN_PASSWORD` is already stored in GitHub; sync it after bootstrap |
| GitHub runner registration token | short-lived GitHub API response | intentionally no | no copy/paste; generate a fresh token with `gh api` |
| registered runner credentials under `/home/github-runner/actions-runner` | VM-local GitHub runner identity | no | no persistent token to preserve; register the replacement host once |
| Project/Kamal PostgreSQL data or workload-local secrets | workload/server-local unless separately backed up | no | restore/redeploy according to the workload repository |

The important distinction is that the only runner token entered during bootstrap is deliberately short-lived. It should never be preserved or stored as durable infrastructure state.

## Configure an existing host

Create the production inventory once:

```bash
cp ansible/inventory/production.yml.example ansible/inventory/production.yml
```

Configure `~/.ssh/config` so the canonical alias resolves through Cloudflare Access:

```sshconfig
Host teplotec-production-eu-central-helsinki-application-01 teplotec-production
  HostName ssh.teplotec.com
  User root
  IdentityFile ~/.ssh/teplotec
  ProxyCommand /opt/homebrew/bin/cloudflared access ssh --hostname %h
```

For an already-registered host:

```bash
ansible-playbook \
  -i ansible/inventory/production.yml \
  ansible/playbooks/app-host.yml
```

## Bootstrap a replacement host

A fresh host needs a short-lived GitHub runner registration token once. Generate it on the operator machine and expose it only through the Ansible process environment:

```bash
export GITHUB_RUNNER_REGISTRATION_TOKEN="$(
  gh api \
    --method POST \
    repos/teplotec/infra/actions/runners/registration-token \
    --jq .token
)"

ansible-playbook \
  -i ansible/inventory/production.yml \
  ansible/playbooks/app-host.yml

unset GITHUB_RUNNER_REGISTRATION_TOKEN
```

Do not store the registration token in Terraform variables, Terraform state, the repository, or Ansible inventory.

## ERP Administrator password

`ERP Reset` and password synchronization use the repository secret `ERPNEXT_ADMIN_PASSWORD`.

If that secret is not yet populated and the existing host is still available, copy the generated value into GitHub Secrets without printing it:

```bash
ssh teplotec-production-eu-central-helsinki-application-01 \
  "awk -F= '/^ERP_ADMIN_PASSWORD=/{print substr(\$0, index(\$0, \"=\") + 1)}' /root/erpnext-credentials.txt" \
  | gh secret set ERPNEXT_ADMIN_PASSWORD --repo teplotec/infra
```

Once it exists in GitHub, a replacement host does not require the old generated Administrator password to survive.

## Recovery sequence

For a replacement application host:

```text
Terraform Apply
  -> cloud-init completes
  -> Ansible app-host bootstrap
  -> workload deployment / data restore
  -> ERP admin password sync
  -> migrations / verification
```

A replacement VM is therefore reproducible from durable control-plane state plus workload backups. Do not treat the VM filesystem itself as the source of truth.
