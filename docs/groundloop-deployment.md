# GroundLoop deployment

GroundLoop has two production runtimes from `teplotec/groundloop`:

- `apps/web`: Next-compatible UI deployed to Cloudflare Worker `groundloop-web`.
- Python API: FastAPI + calculation core deployed on `teplotec-production-eu-central-helsinki-application-01`.

Public application: `https://groundloop.teplotec.com`.
Python API: `https://groundloop-api.teplotec.com`.

The API hostname intentionally uses a first-level `teplotec.com` subdomain so Cloudflare Universal SSL covers it.

## Network boundary

```text
Browser
  -> groundloop.teplotec.com
  -> Cloudflare Worker groundloop-web
  -> /api/calculate
  -> https://groundloop-api.teplotec.com
  -> Cloudflare Tunnel
  -> cloudflared on teplotec-production-eu-central-helsinki-application-01
  -> 127.0.0.1:8000
  -> GroundLoop FastAPI container
```

The API container binds only to `127.0.0.1:8000`. Do not open port 8000 in the Hetzner firewall and do not point public DNS directly at the server IP.

`groundloop-api.teplotec.com` intentionally has no interactive Cloudflare Access application because the public Worker calls it server-to-server. Add application-to-application authentication and rate limiting before treating it as a stable public compute surface.

## Infrastructure

Production Terraform lives in:

```text
terraform/environments/production
```

Terraform owns the proxied `groundloop-api.teplotec.com` DNS record and Cloudflare Tunnel ingress:

```text
groundloop-api.teplotec.com -> http://127.0.0.1:8000
```

Do not create this DNS record manually.

## Cloudflare Worker frontend

Worker configuration is version-controlled in `teplotec/groundloop/apps/web/wrangler.jsonc`. That file owns the worker name, production custom domain, runtime backend URL, compatibility settings, and observability configuration.

The vinext migration uses its native Cloudflare deployment command from `apps/web/package.json`. In Workers Builds, use:

```text
Root directory: apps/web
Production branch: main
Deploy command: npm run deploy
Version / preview command: npm run deploy:preview
```

The runtime backend URL is not a secret and is committed as:

```text
GROUNDLOOP_API_URL=https://groundloop-api.teplotec.com
```

Do not maintain a conflicting build-time variable in the Cloudflare dashboard.

## One-time host bootstrap for automated API deployment

The production runner is deliberately not allowed arbitrary passwordless `sudo`. Ansible installs a root-owned deployment helper and a narrow sudo policy for only that helper.

After the infra change is merged, apply the production application-host playbook once:

```bash
cp -n ansible/inventory/production.yml.example ansible/inventory/production.yml
ansible-playbook \
  -i ansible/inventory/production.yml \
  ansible/playbooks/app-host.yml
```

On an existing host the already-registered GitHub runner is reused, so no new registration token is required.

Verify the helper on the host if desired:

```bash
ssh teplotec-production-eu-central-helsinki-application-01
sudo /usr/local/sbin/teplotec-groundloop-api-admin status
```

## Normal API deployment

After the one-time helper bootstrap, API releases no longer require an SSH deployment sequence.

In GitHub Actions for `teplotec/infra`, run:

```text
GroundLoop / Production / 01 Deploy API
```

from `main` and enter:

```text
DEPLOY
```

The restricted helper then:

1. synchronizes `/opt/teplotec/groundloop/app` to `teplotec/groundloop` `main`;
2. builds a revision-tagged Docker image;
3. replaces only the `groundloop-api` container;
4. keeps port 8000 bound to `127.0.0.1`;
5. verifies local health and rolls back to the previous container image if the new container fails health;
6. lets the workflow verify the public Cloudflare health endpoint and a real calculation request.

## Verification

Local origin:

```bash
curl --fail http://127.0.0.1:8000/health
```

Through Cloudflare Tunnel:

```bash
curl --fail https://groundloop-api.teplotec.com/health
```

End-to-end frontend:

```text
https://groundloop.teplotec.com
```

Run a calculation and confirm the UI receives a result through `/api/calculate`.

## Emergency manual fallback

If GitHub Actions is unavailable, the restricted deployment helper can still be run over the existing Cloudflare Access SSH path:

```bash
ssh teplotec-production-eu-central-helsinki-application-01
sudo /usr/local/sbin/teplotec-groundloop-api-admin deploy
```

Prefer the GitHub Actions workflow during normal operation so deployment history and production approvals remain visible in one place.
