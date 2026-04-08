# Deploy (Oracle Cloud ARM + Docker + Caddy)

This guide targets a **free-tier Oracle Cloud ARM VM** (Ubuntu), **GitHub Actions** for CI/CD, and a **single domain** for the UI with `/api` proxied to FastAPI (production build uses `VITE_API_URL=/api`).

## Security expectations

- This stack is suitable for a **personal demo**. There is **no end-user authentication** in the app; a public URL can consume your **OpenAI / Cohere** quotas.
- **Do not** expose Qdrant or Redis ports on the public internet. The provided Compose file keeps dependency services on an internal Docker network only; the API binds to **127.0.0.1:8080** for Caddy.

## One-time: Oracle VM

1. Create an **Always Free** ARM instance (Ubuntu 22.04/24.04 LTS).
2. **Ingress rules:** open **TCP 22** (SSH), **80**, and **443** to `0.0.0.0/0` (or your IP for SSH if you prefer).
3. SSH in as the default user (`ubuntu` or `opc`).

Install Docker (official docs) and the Compose plugin:

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl
# Follow: https://docs.docker.com/engine/install/ubuntu/
sudo usermod -aG docker "$USER"
newgrp docker
```

## One-time: app checkout and env

```bash
sudo mkdir -p /opt/rag-project
sudo chown "$USER:$USER" /opt/rag-project
cd /opt/rag-project
git clone https://github.com/YOUR_USER/YOUR_REPO.git .
cp .env.production.example .env
chmod 600 .env
nano .env   # set OPENAI_API_KEY, COHERE_API_KEY, etc.
```

Values in `.env` must use **Docker service names** for URLs (see [.env.production.example](.env.production.example)).

## One-time: Caddy + static site directory

```bash
sudo mkdir -p /var/www/rag
sudo chown "$USER:$USER" /var/www/rag
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https curl
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update
sudo apt install caddy
```

Copy [deploy/Caddyfile.example](deploy/Caddyfile.example) to `/etc/caddy/Caddyfile` (or a drop-in), replace `YOUR_DOMAIN` with your DNS A record pointing at the VM public IP, then:

```bash
sudo systemctl reload caddy
```

Caddy obtains **Let’s Encrypt** certificates automatically when DNS points to this host.

## Run the stack

From `/opt/rag-project` (repo root):

```bash
docker compose -f deploy/docker-compose.prod.yml --env-file .env up -d --build
```

Check API via SSH tunnel if needed:

```bash
curl -sS http://127.0.0.1:8080/health
```

## GitHub Actions CD

### Repository secrets

| Secret | Purpose |
|--------|---------|
| `DEPLOY_HOST` | VM public IP or DNS |
| `DEPLOY_USER` | SSH user (e.g. `ubuntu`) |
| `SSH_PRIVATE_KEY` | Private key for that user (PEM) |
| `DEPLOY_PATH` | Optional. Default `/opt/rag-project` if unset |

### What deploy does

On each successful **CI** run on your default integration branch (`main` or `master`), the **Deploy** workflow:

1. Downloads the `frontend-dist` artifact from that CI run.
2. `rsync`s it to `/var/www/rag` on the VM.
3. SSHs in, runs `git pull` and `docker compose -f deploy/docker-compose.prod.yml ... up -d --build`.

Ensure the VM user can:

- `git pull` (deploy key or HTTPS credential).
- Run `docker` without sudo (user in `docker` group).

### First deploy before Actions

Push your default branch with workflows enabled, or manually on the VM:

```bash
cd /opt/rag-project
git pull
docker compose -f deploy/docker-compose.prod.yml --env-file .env up -d --build
```

Copy a built `frontend/dist` once to `/var/www/rag` (or wait for the first green CD run).

## Troubleshooting

| Symptom | Check |
|---------|--------|
| Ingest stuck / file not found | API and worker share volume `uploads_data` at `UPLOAD_DIR=/app/uploads`; both services must use the same Compose file. |
| Parse failures | Unstructured is memory-heavy; ensure the VM has enough RAM; `docker compose logs unstructured`. |
| Chat stream drops | Caddy must use long timeouts and `flush_interval -1` on the API proxy (see [deploy/Caddyfile.example](deploy/Caddyfile.example)). |
| 502 on `/api` | `docker compose ps`; `curl http://127.0.0.1:8080/health` on the VM. |

## Backups

Qdrant data lives in the Docker volume `qdrant_data`. For a demo, snapshot the volume or instance periodically; add automation when you need RPO/RTO.
