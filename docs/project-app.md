# TeploTEC Project application

`https://project.teplotec.com` is the internal TeploTEC project/knowledge application.

## Infrastructure boundary

Terraform in this repository owns:

- the existing Hetzner CX33 host
- the existing Cloudflare Tunnel
- DNS for `project.teplotec.com`
- the Cloudflare Tunnel route `project.teplotec.com -> http://127.0.0.1:3001`
- the Cloudflare Access application and policy

The Rails application repository owns:

- application source code
- Docker image
- Kamal configuration
- PostgreSQL accessory used by the application
- Rails secrets and application database credentials

The initial Rails source repository is:

```text
sergii/tp-installer-3f3
```

When it is transferred to the `teplotec` organization, Terraform should not need to change. Only the Rails repository's registry/image configuration may need to change.

## Access

The Project application intentionally differs from ERP access:

- only `access_trusted_emails` are allowed
- only the Cloudflare identity provider is allowed
- one-time PIN is not enabled for Project

This means a trusted user signs in with the configured Cloudflare account identity before Cloudflare forwards any request to Rails.

## Network path

```text
Browser
  -> Cloudflare Access
  -> Cloudflare Tunnel
  -> cloudflared on CX33
  -> 127.0.0.1:3001
  -> kamal-proxy
  -> Rails container
  -> PostgreSQL accessory on the private Kamal Docker network
```

No Project HTTP or PostgreSQL port is opened in the Hetzner firewall.

## Deployment

Terraform and application deployment are intentionally separate operations.

### 1. Infrastructure

Merge the infrastructure PR, then run the existing manual `Terraform Apply` workflow from `main` with the `APPLY` confirmation.

The apply adds the Project DNS record, Access application/policy, and tunnel ingress route. It does not restart or replace ERPNext.

### 2. Rails application

Deploy from the Rails application checkout using Kamal. Kamal connects to the same host through `ssh.teplotec.com` and Cloudflare Access.

The first deployment uses:

```bash
bin/kamal setup
```

Normal subsequent deployments use:

```bash
bin/kamal deploy
```

The Rails repository documents the required local environment variables and the one-time PostgreSQL initialization.

## Port allocation

| Service | Loopback endpoint |
| --- | --- |
| ERPNext | `127.0.0.1:8080` |
| TeploTEC Project | `127.0.0.1:3001` |
| SSH tunnel target | `127.0.0.1:22` |

Do not point `project.teplotec.com` at the Hetzner public IP.
