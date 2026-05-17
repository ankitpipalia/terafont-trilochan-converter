# Self-hosting in production (Docker)

This guide walks through deploying the **Gujarati Font Converter** as a self-hosted web service with **all features enabled** — text conversion, image OCR, PDF OCR, DOCX import/export, and PDF export.

The desktop app is great for individuals. For a team / office / public service, the Docker image is what you want.

---

## What you get

A single container exposing the same UI you'd see in the desktop app, served over HTTP. Everything stays on your server — no third-party calls, no telemetry.

| Endpoint | Method | What it does |
|----------|--------|--------------|
| `/` | GET | The web UI (same code as desktop) |
| `/api/health` | GET | Health check (returns 200 + JSON) |
| `/api/version` | GET | App version string |
| `/api/capabilities` | GET | Which features are active in this build |
| `/api/convert/unicode-to-tera` | POST | `{text}` → `{text}` |
| `/api/convert/tera-to-unicode` | POST | reverse direction |
| `/api/upload` | POST | multipart `.txt` / `.docx` → `{text}` |
| `/api/export/docx` | POST | `{content, filename}` → DOCX download |
| `/api/export/pdf` | POST | `{content, filename}` → PDF download with TeraFont embedded |
| `/api/ocr/image` | POST | multipart image → `{text, confidence, duration_ms}` |
| `/api/ocr/pdf` | POST | multipart PDF → `{text, pages: [...], total_pages}` |
| `/api/ocr/pdf-info` | POST | multipart PDF → `{page_count, file_size, path}` |

Interactive API docs (FastAPI's auto-generated Swagger UI) are at `/docs`.

---

## Resource expectations

| | Minimum | Recommended |
|---|---------|-------------|
| RAM | 2 GB | **4 GB** (PaddleOCR holds ~800 MB per worker) |
| CPU | 1 core | 2+ cores |
| Disk | 2 GB | 4 GB (image + PaddleOCR model cache) |
| Network | n/a | only outbound on first run, to download PaddleOCR models |

The image is **~1.2 GB on disk** because PaddleOCR + paddlepaddle dominate the dependency tree. There's no smaller way to ship Gujarati OCR with comparable accuracy.

---

## 1-command start

```bash
git clone https://github.com/ankitpipalia/terafont-trilochan-converter.git
cd terafont-trilochan-converter

docker compose -f docker-compose.prod.yml up -d
```

Visit **http://localhost:8000**. First OCR request will take ~10 s while the PaddleOCR model warms up; subsequent calls are 0.5–2 s per page.

Check it's healthy:

```bash
curl -s http://localhost:8000/api/health | python3 -m json.tool
# {
#   "status": "ok",
#   "version": "0.1.0",
#   "ocr": true,
#   "ocr_error": null
# }
```

Tail the logs:

```bash
docker compose -f docker-compose.prod.yml logs -f
```

Stop:

```bash
docker compose -f docker-compose.prod.yml down
```

---

## Configuration (environment variables)

| Variable | Default | Notes |
|----------|---------|-------|
| `PORT` | `8000` | Host port to publish |
| `UVICORN_WORKERS` | `2` | More workers = more concurrent OCR. Each holds ~800 MB. Don't exceed `(RAM_GB / 1) - 1`. |
| `CORS_ALLOW_ORIGINS` | empty (same-origin only) | Comma-separated list, e.g. `https://app.example.com,https://staging.example.com`. Set if you serve the UI from a different domain than the API. |

Drop a `.env` next to `docker-compose.prod.yml`:

```env
PORT=8000
UVICORN_WORKERS=2
CORS_ALLOW_ORIGINS=https://gujarati.example.com
```

---

## Production deployment with HTTPS

Put a reverse proxy in front. Three working recipes follow — pick one.

### Option A — Caddy (easiest, auto-HTTPS)

`Caddyfile`:

```caddy
gujarati.example.com {
    encode gzip zstd
    reverse_proxy localhost:8000 {
        # OCR on large PDFs can be slow; bump timeouts.
        transport http {
            response_header_timeout 5m
            read_timeout 10m
        }
    }

    # Cap request size — generous enough for typical legal scans
    request_body {
        max_size 100MB
    }
}
```

```bash
sudo apt install caddy   # or brew install caddy
sudo systemctl reload caddy
```

Caddy auto-provisions a Let's Encrypt cert. Done.

### Option B — Nginx + Certbot

`/etc/nginx/sites-available/gujarati.conf`:

```nginx
server {
    server_name gujarati.example.com;
    listen 80;

    client_max_body_size 100M;
    proxy_read_timeout 600s;
    proxy_send_timeout 600s;
    proxy_connect_timeout 60s;

    location / {
        proxy_pass         http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header   Host              $host;
        proxy_set_header   X-Real-IP         $remote_addr;
        proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/gujarati.conf /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
sudo certbot --nginx -d gujarati.example.com
```

### Option C — Traefik (Docker-native)

Add labels to `docker-compose.prod.yml`:

```yaml
services:
  app:
    # ... existing config ...
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.gujarati.rule=Host(`gujarati.example.com`)"
      - "traefik.http.routers.gujarati.entrypoints=websecure"
      - "traefik.http.routers.gujarati.tls.certresolver=letsencrypt"
      - "traefik.http.services.gujarati.loadbalancer.server.port=8000"
    networks:
      - web

networks:
  web:
    external: true
```

(Assumes a Traefik instance already running with a `web` network.)

---

## Building the image yourself

```bash
docker build -f Dockerfile.prod -t gujarati-converter:latest .
# Or with a version tag matching pyproject.toml:
docker build -f Dockerfile.prod -t gujarati-converter:0.1.0 -t gujarati-converter:latest .
```

Push to a registry (GHCR example):

```bash
docker tag  gujarati-converter:latest ghcr.io/ankitpipalia/gujarati-converter:latest
docker push ghcr.io/ankitpipalia/gujarati-converter:latest
```

---

## Operations

### Watch logs

```bash
docker compose -f docker-compose.prod.yml logs -f --tail 100
```

### Restart on config change

```bash
docker compose -f docker-compose.prod.yml restart app
```

### Upgrade

```bash
git pull
docker compose -f docker-compose.prod.yml build --pull
docker compose -f docker-compose.prod.yml up -d
```

### Health probe (Kubernetes, Nomad, etc.)

```yaml
livenessProbe:
  httpGet:
    path: /api/health
    port: 8000
  initialDelaySeconds: 60
  periodSeconds: 30

readinessProbe:
  httpGet:
    path: /api/health
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10
```

The `start_period: 60s` in the compose healthcheck accounts for PaddleOCR's cold-init time; do the same for k8s.

---

## Security checklist for a public deployment

- [ ] **Run behind HTTPS** — passwords / tokens aren't involved, but uploaded documents may contain personal data.
- [ ] **Rate-limit OCR endpoints** — they're CPU-heavy. Caddy `rate_limit` or nginx `limit_req` keep one user from monopolizing a worker.
- [ ] **Cap upload size** — Caddy `max_size`, nginx `client_max_body_size`. The image accepts large files by default.
- [ ] **Don't expose `/docs`** — the FastAPI auto-docs page reveals all endpoints. Optionally guard with basic auth in your proxy, or set `app.docs_url=None` for the next release.
- [ ] **Run as non-root** — already done in the Dockerfile (`USER app`).
- [ ] **Keep logs out of public view** — `docker compose logs` may include filenames of uploaded docs.
- [ ] **Persist `paddle-cache` volume** so PaddleOCR doesn't re-download models from the public CDN on every container restart.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| 503 on `/api/ocr/*` | PaddleOCR init failed | `docker compose logs app | grep -i paddle`; usually a missing system lib — rebuild the image |
| First-request OCR very slow (~10–15 s) | Model warm-up | Expected. Subsequent requests are fast. Pre-warm with `curl /api/health` after restart. |
| `413 Request Entity Too Large` | Reverse proxy size limit | Bump `client_max_body_size` (nginx) / `request_body max_size` (Caddy) |
| OOM kill | PaddleOCR worker exceeded RAM | Lower `UVICORN_WORKERS`, or give the host more RAM |
| Browser shows "Browser-only mode" toast | Backend not reachable from the page | Open browser devtools → Network — check `/api/health` returns 200 |
| Conversion works but OCR/PDF buttons error | `capabilities` reports `ocr=false` | Confirm you're running `Dockerfile.prod`, not the test `Dockerfile` |

---

## Architecture notes

The same web UI runs in three modes:

1. **Desktop** (PyWebView): JS calls `window.pywebview.api.*` directly.
2. **Self-hosted** (this Docker setup): `api-bridge.js` probes `/api/health`, finds the FastAPI server, and shims the same `window.pywebview.api` to `fetch()` REST calls. **No UI changes needed.**
3. **Static** (GitHub Pages): no backend; conversion still works (it's pure JS), OCR/PDF/DOCX features show friendly "requires desktop or server" errors.

The conversion logic lives once in Python (`app/converter.py`) and is exposed identically through both transports. The 133 golden tests gate every release.

---

## Roadmap

Not yet shipped, on the to-do list for a future release if there's demand:

- **Async OCR job queue** — currently `/api/ocr/pdf` is synchronous. For 100+ page PDFs you'll want a job ID + polling. Architectural hooks for this are in `app/workers.py`.
- **Multi-user state** — `recent_files`, `settings` are client-side only in server mode. Add session cookies + a SQLite store if you need server-side persistence.
- **Built-in HTTPS** — currently relies on a reverse proxy. Adding `uvicorn --ssl-keyfile` flags is trivial if there's demand.
- **Auth** — no built-in auth. Use your reverse proxy (basic auth, OAuth-proxy, Cloudflare Access).

Open an issue with your use case if any of these matter.
