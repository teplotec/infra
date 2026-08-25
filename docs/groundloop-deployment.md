# GroundLoop deployment

GroundLoop is split into two deployable runtimes from `teplotec/groundloop`:

- `apps/web`: Next.js UI deployed to Cloudflare Workers.
- Python API: FastAPI + GroundLoop calculation core deployed on the shared production application host `teplotec-production-eu-central-helsinki-application-01`.

The public application hostname is `groundloop.teplotec.com`.
The Python API hostname is `api.groundloop.teplotec.com`.

## Network boundary

```text
Browser
  -> groundloop.teplotec.com
  -> Cloudflare Worker (Next.js)
  -> /api/calculate route handler
  -> https://api.groundloop.teplotec.com
  -> Cloudflare Tunnel
  -> cloudflared on teplotec-production-eu-central-helsinki-application-01
  -> 127.0.0.1:8000
  -> GroundLoop FastAPI container
```

The API container must bind only to `127.0.0.1:8000`. Do not open port 8000 in the Hetzner firewall and do not create a DNS record pointing directly at the server IP.

`api.groundloop.teplotec.com` intentionally has no interactive Cloudflare Access application because the public GroundLoop Worker calls it server-to-server. Add application-to-application authentication and rate limiting before treating the API as a stable public compute surface.

## 1. Apply production infrastructure

Merge the GroundLoop API route and platform-infrastructure PRs first. Then run the `Terraform Apply` workflow from `main` with confirmation `APPLY`.

The production Terraform root is:

```text
terraform/environments/production
```

Terraform creates the proxied `api.groundloop.teplotec.com` CNAME and adds an ingress rule to the existing production Cloudflare Tunnel. Do not create that DNS record manually in the Cloudflare dashboard.

Expected production origin route:

```text
api.groundloop.teplotec.com -> http://127.0.0.1:8000
```

## 2. First Python API deployment

Connect through the Cloudflare Access SSH route, then clone and run the GroundLoop container:

```bash
ssh teplotec-production-eu-central-helsinki-application-01

sudo mkdir -p /opt/teplotec/groundloop
sudo chown "$USER":"$USER" /opt/teplotec/groundloop
cd /opt/teplotec/groundloop

git clone https://github.com/teplotec/groundloop.git app
cd app

docker build -t teplotec-groundloop-api:latest .
docker rm -f groundloop-api 2>/dev/null || true
docker run -d \
  --name groundloop-api \
  --restart unless-stopped \
  -p 127.0.0.1:8000:8000 \
  teplotec-groundloop-api:latest

curl --fail http://127.0.0.1:8000/health
```

After Terraform applies the GroundLoop tunnel/DNS route, verify through Cloudflare:

```bash
curl --fail https://api.groundloop.teplotec.com/health
```

## 3. Create the Cloudflare Worker frontend

Use Cloudflare Workers, not Pages. The current Next.js app contains the `/api/calculate` Route Handler and therefore is not a static-only site.

In the Cloudflare dashboard:

1. Open `Workers & Pages`.
2. Select `Create application`.
3. Under `Import a repository`, select `Get started`.
4. Connect the GitHub account/organization that can read `teplotec/groundloop`.
5. Select repository `teplotec/groundloop`.
6. Set the Worker name to `groundloop`.
7. Set the production branch to `main`.
8. Set the root directory to `apps/web`.
9. Keep the production deploy command as `npx wrangler deploy` unless Cloudflare's generated configuration explicitly changes it.
10. Save and deploy.

If `apps/web` does not yet contain a Wrangler configuration, Workers Builds automatic configuration will detect Next.js and may open a GitHub configuration PR. Review and merge that generated PR before relying on production deploys. The Worker name in the generated Wrangler configuration must remain `groundloop` so it matches the Worker created in the dashboard.

## 4. Configure the backend URL

After the Worker exists:

1. Open `Workers & Pages` -> `groundloop` -> `Settings`.
2. Open `Variables and Secrets`.
3. Add a Text variable named `GROUNDLOOP_API_URL`.
4. Set its value to `https://api.groundloop.teplotec.com`.
5. Deploy the settings change if Cloudflare prompts for a deployment.

This is not a secret. The browser does not consume it directly; the Next.js Worker uses it when `/api/calculate` proxies a calculation request to FastAPI.

## 5. Enable pull-request previews

In `Workers & Pages` -> `groundloop` -> `Settings` -> `Build` -> `Branch control`:

1. Confirm the production branch is `main`.
2. Enable `Builds for non-production branches`.

Production branch pushes use the normal deploy command. Non-production branches use the preview deploy command, normally `npx wrangler versions upload`, so they get Worker preview versions without replacing production.

Cloudflare's GitHub integration can post build status and preview URLs on pull requests.

## 6. Add the production custom domain

Only after a Worker preview and the calculation flow are working:

1. Open `Workers & Pages` -> `groundloop`.
2. Open `Settings` -> `Domains & Routes`.
3. Select `Add` -> `Custom Domain`.
4. Enter `groundloop.teplotec.com`.
5. Select `Add Custom Domain`.

Do not pre-create a CNAME for `groundloop.teplotec.com`. Cloudflare Custom Domains create the required DNS record and certificate automatically, and an existing CNAME can block Custom Domain creation.

## 7. End-to-end verification

Verify in this order:

```bash
# On the production application host
curl --fail http://127.0.0.1:8000/health

# Through the Cloudflare Tunnel
curl --fail https://api.groundloop.teplotec.com/health
```

Then open the Worker preview URL and run a calculation. Finally open:

```text
https://groundloop.teplotec.com
```

Run the same calculation and confirm the browser receives a valid result through `/api/calculate`.

## Updating the API manually

Until automated GroundLoop deployment is introduced:

```bash
ssh teplotec-production-eu-central-helsinki-application-01
cd /opt/teplotec/groundloop/app
git pull --ff-only origin main
docker build -t teplotec-groundloop-api:latest .
docker rm -f groundloop-api 2>/dev/null || true
docker run -d \
  --name groundloop-api \
  --restart unless-stopped \
  -p 127.0.0.1:8000:8000 \
  teplotec-groundloop-api:latest
curl --fail http://127.0.0.1:8000/health
```

This manual step is intentionally temporary. A dedicated restricted deployment workflow can replace it after the first production boundary is validated.
