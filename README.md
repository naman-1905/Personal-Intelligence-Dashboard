# Brief — Personal News Dashboard

Self-hosted news briefing stack. Everything runs **locally** via Docker: MongoDB, Redis, Ollama, FastAPI, scraper workers, and a Next.js (JavaScript) web app. Capacitor wraps the same UI for Android.

No cloud APIs, no hosted DB, no engagement-ranked feed.

## Monorepo layout

```
apps/web              Next.js App Router (JavaScript, not TypeScript)
apps/mobile-shell     Capacitor shell → local Next.js server
services/api          FastAPI REST API
services/scraper      RSS scrape → Redis staging → Ollama filter → MongoDB
packages/shared       JSON schemas shared across services
infra/                docker-compose, mongo-init, .env
```

## Prerequisites

- Docker + Docker Compose
- Node 20+ (only needed for local web/Capacitor outside Docker)
- Optional: Android Studio for Capacitor device builds
- Optional: NVIDIA Container Toolkit for GPU Ollama (CPU works)

## Quick start (all local)

```bash
cd /home/naman/Projects/news-dashboard
cp infra/.env.example infra/.env   # already present if you used the scaffold
make up
```

Then:

| Service   | URL |
|-----------|-----|
| Web UI    | http://localhost:3000 |
| API docs  | http://localhost:8000/docs |
| MongoDB   | localhost:27017 |
| Redis     | localhost:6379 |
| Ollama    | http://localhost:11434 |

First boot pulls a small local LLM (`qwen2.5:3b-instruct-q4_K_M`) into the Ollama volume — that can take several minutes on CPU.

```bash
make health
make scrape          # manual scrape trigger
make logs
```

## Data flow

1. Scheduler (every 6h, plus light check hourly) scrapes enabled RSS sources  
2. Raw items land in Redis staging (`staging:<category>:<hash>`)  
3. Filter agent (Ollama, with heuristic fallback) scores importance + summary  
4. Passes write to MongoDB `articles`; frontend only talks to FastAPI  

## Capacitor (mobile)

With the web container running:

```bash
cd apps/mobile-shell
npm install
npx cap add android    # once
npx cap sync
npx cap open android
```

Emulator uses `10.0.2.2:3000` (host localhost). Physical device: set `server.url` in `capacitor.config.json` to your LAN IP, e.g. `http://192.168.x.x:3000`.

## Design choices (vs original plan)

- **Next.js = JavaScript** (no TypeScript)  
- **shared-types → JSON Schema** in `packages/shared` (no TS package)  
- **Capacitor**, not Flutter — one UI codebase  
- **Ollama heuristic fallback** so scrapes still work while the model pulls  
- **`user_id = "local"`** stub for multi-user later  
- Stack is **100% docker-compose local** — no external SaaS  

## Phases

Phase 1 (this scaffold): health, RSS → Mongo → `/articles`, Next.js cards, Docker, Capacitor shell.  
Later: richer HTML scrapers, notifications, prune/archive, Play Store prep — see `Plan.md`.
