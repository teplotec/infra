# GroundLoop deployment

GroundLoop is split into two deployable runtimes from `teplotec/groundloop`:

- `apps/web`: Next.js UI deployed to Cloudflare Workers.
- Python API: FastAPI + GroundLoop calculation core deployed on the existing Hetzner CX33.

The public application hostname is expected to be `groundloop.teplotec.com`.
The Python API hostname is `api.groundloop.teplotec.com`.

## Network boundary

```text
Browser
  -> groundloop.teplotec.com
  -> Cloudflare Worker (Next.js)
  -> /api/calculate route handler
  -> https://api.groundloop.teplotec.com
  -> Cloudflare Tunnel
  -> cloudflared on Hetzner CX33
  -> 127.0.0.1:8000
  -> GroundLoop FastAPI container
```

The API container must bind only to `127.0.0.1:8000`. Do not open port 8000 in the Hetzner firewall and do not create a DNS record pointing directly at the server IP.

`api.groundloop.teplotec.com` intentionally has no interactive Cloudflare Access application. It is an application-to-application endpoint used by the public GroundLoop Worker. Authentication/rate limiting can be added at the API or Cloudflare layer when the public API contract becomes stable.

## First API deployment

Connect through the existing Cloudflare Access SSH route, then clone and run the GroundLoop container:

```bash
ssh teplotec-erp

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

After Terraform applies the GroundLoop tunnel/DNS route, also verify:

```bash
curl --fail https://api.groundloop.teplotec.com/health
```

## Updating the API manually

Until automated GroundLoop deployment is introduced:

```bash
ssh teplotec-erp
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

This manual step is intentionally temporary. A dedicated restricted deployment workflow can replace it once the first production boundary is validated.
