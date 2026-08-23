# ERP host lifecycle

TeploTEC deliberately separates infrastructure creation, first-boot runtime bootstrap, repeatable host configuration, application image delivery, and ERP site data.

## Responsibility split

### Terraform

Terraform owns external and durable infrastructure resources:

- Hetzner CX33 server and firewall
- SSH public key attachment
- Cloudflare DNS, Tunnel, and Access resources
- Terraform remote state

Terraform does not own GitHub runner registration tokens or application passwords.

### cloud-init

`terraform/bootstrap.sh.tftpl` is used only during first server creation to make the new host usable:

- install Docker
- clone the pinned `frappe_docker` checkout
- create the initial ERPNext Compose runtime
- create the initial site if necessary
- start `cloudflared`

Changing cloud-init for an already-created `hcloud_server` is intentionally avoided as a host-configuration mechanism. Host configuration after creation belongs in Ansible.

### Ansible

`ansible/playbooks/erp-host.yml` owns repeatable host administration configuration:

- the unprivileged `github-runner` user
- `/usr/local/sbin/teplotec-erp-admin`
- the restricted sudo policy for that helper
- the pinned GitHub Actions runner installation
- the `teplotec-erp-admin` runner service

The playbook is idempotent. An already-registered runner does not need another registration token.

### GitHub Actions and GHCR

GitHub-hosted runners build and test the immutable ERP image and publish it to GHCR.

The CX33 self-hosted runner does not build ERP images. It is only a local deployment/control agent. The production deploy workflow tells it which immutable GHCR SHA tag to pull, then the restricted ERP admin helper switches Compose to that image and runs Frappe migrations.

## Configure an existing host

Install Ansible locally and create the production inventory once:

```bash
cp ansible/inventory/production.yml.example ansible/inventory/production.yml
```

The inventory intentionally uses the `teplotec-erp` SSH host alias, so the existing Cloudflare Access `ProxyCommand` in `~/.ssh/config` remains the single SSH configuration source.

For an already-registered host, run:

```bash
ansible-playbook \
  -i ansible/inventory/production.yml \
  ansible/playbooks/erp-host.yml
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
  ansible/playbooks/erp-host.yml

unset GITHUB_RUNNER_REGISTRATION_TOKEN
```

Do not store the registration token in Terraform variables, Terraform state, the repository, or Ansible inventory.

## Administrator password secret

`ERP Reset` and password synchronization use the repository secret `ERPNEXT_ADMIN_PASSWORD`. The initial generated password already exists only on the ERP host in `/root/erpnext-credentials.txt`.

To copy the existing generated Administrator password into GitHub Secrets without printing it to the terminal, run from the operator machine:

```bash
ssh teplotec-erp \
  "awk -F= '/^ERP_ADMIN_PASSWORD=/{print substr(\$0, index(\$0, \"=\") + 1)}' /root/erpnext-credentials.txt" \
  | gh secret set ERPNEXT_ADMIN_PASSWORD --repo teplotec/infra
```

After the secret exists, re-run the failed `ERP Reset` job.

## Recovery sequence

For a replacement CX33, the intended sequence is:

```text
Terraform Apply
  -> cloud-init completes
  -> Ansible ERP host bootstrap
  -> ERP Image Deploy or data restore
  -> migrate / verify
```

The runner registration token is needed only during the Ansible bootstrap of a previously unregistered host.
