# AGENT.md — Handoff / Continue From Here

**Last updated:** 2026-10-11  
**Project root:** `/home/naman/Projects/news-dashboard`  
**Source plan:** `/home/naman/plans/plan.md` (trimmed pointer) + canonical `/home/naman/Projects/news-dashboard/Plan.md`

---

## Status at stop

| Area | Status |
|------|--------|
| Monorepo scaffold | **Done** — all source files written |
| FastAPI API | **Verified running** — healthy; articles/categories/**topics**/stats/digest/bookmarks endpoints confirmed |
| Scraper service | **Verified running** — multiple full cycles completed (4→11 sources); heuristic + Ollama paths both exercised |
| Next.js web (JavaScript) | **Verified running** — build OK; `/`, `/digest`, `/bookmarks`, `/settings`, `/article/[id]` all HTTP 200 with real data; sidebar shows dynamic Topics section; mobile bottom nav + `/sections` + `/search` added 2026-10-11 (see below) |
| Capacitor mobile-shell | **Scaffolded** — config + fallback `www/`; Android project not generated (`npx cap add android` not run) |
| Docker Compose file | **Done** — stack builds and starts cleanly; `topics.txt` bind-mounted read-only into scraper |
| `docker compose up` | **Completed** — all 7 containers up (mongo, redis, ollama, ollama-init, api, scraper, web) |
| End-to-end verification | **Done** — scrape → filter → Mongo → API → UI verified; see "Fixes applied this session" |
| Research-topics feature (`topics.txt`) | **Done + verified** — see "Topics / research domains feature" below |
| Git init / commit / push | **Done** — per-file commits pushed to `github.com/naman-1905/Personal-Intelligence-Dashboard` (`main`) |

**You are here:** stack is up and fully verified. Ollama model `qwen2.5:3b-instruct-q4_K_M` pulled and in use (CPU inference ≈ 15–30 s/item). Final LLM-filtered cycle with the fixed prompt completed: **passed=56, filtered=27** (vs 10/72 before the prompt fix) — over-rejection resolved. Research-topics feature is live: `topics.txt` at repo root → scraper re-reads it after every scrape cycle → new domains/topics become Google-News-RSS sources in Mongo → `GET /topics` → sidebar renders them dynamically.

### Fixes applied this session (all verified)

1. **`services/api/app/models/schemas.py`** — `ArticleOut.id` now has `serialization_alias="id"`.
   FastAPI serializes response models by alias, so the API returned `_id` while the frontend uses `article.id` → every feed link rendered `/article/undefined`. Input still accepts `_id` (alias) or `id` (`populate_by_name`).
2. **`services/scraper/scheduler.py`** — pub/sub trigger handler now deletes the `scraper:trigger` key *immediately on message receipt* (before running the cycle). Previously a single `POST /admin/trigger-scrape` double-fired two overlapping scrape cycles (pub/sub + 5 s key-poll fallback), doubling LLM work.
3. **`services/scraper/agent/filter.py`** — prompt rewrite + `num_predict` 256→384. The old "strict news filter" prompt made the model reject legitimate headlines (`is_noise: true`) whenever the RSS excerpt was boilerplate (NASA nav text, HN "Points/Comments" meta). New prompt judges primarily from the headline and only rejects clickbait/gossip/promo in the headline itself. Verified: same item flipped `pass:false → pass:true` with a clean summary; full cycle pass rate went 10→56.

### Topics / research domains feature (this session)

- **`topics.txt`** (repo root) — one research domain or topic per line, `#` comments allowed. Domains are researched via Google News `site:` search; plain phrases are treated as keywords.
- **`services/scraper/topics.py`** (new) — `sync_topics()` reads the file and upserts each entry into Mongo: a `topics` doc (`slug`, `name`, `query`, `source_name`) plus a matching `sources` doc (`type: rss`, `url: <Google News RSS>`, `origin: "topics.txt"`, `trust_tier: 2`). Category is mapped by keyword hints (technology/science/world/business) with fallback to the new `topics` category.
- **`services/scraper/pipeline.py`** — `run_scrape_cycle()` now calls `sync_topics()` **after every cycle** (wrapped in try/except), so a domain added to `topics.txt` is picked up on the next run with no rebuild/restart. The file is bind-mounted read-only (`../topics.txt:/app/topics.txt:ro`) so host edits are seen live.
- **DB** — `infra/mongo-init/01-init.js` seeds the new `Topics` category (`slug: topics`, icon `tag`) and a unique index on `topics.slug`; API also creates the index at startup.
- **API** — new `GET /topics` (list enabled topics with live article counts); `/articles?topic=<slug>` filters by `source = "topic:<slug>"`.
- **Web** — layout fetches categories + topics, sidebar renders a "Research topics" section dynamically from the DB (badge = article count), feed page supports `/?topic=<slug>` with its own title/subtitle.

Verified: sync reports `{total: 7, added: 7}`; `GET /topics` returns all 7; a test fetch of `topic:quantum-computing` returned 40 real items from Google News RSS; sidebar renders all topic links; full scrape with the 11 sources (incl. topics) ran clean.

### Source catalog expansion (2026-10-11)

- **`infra/mongo-init/sources-catalog.json`** — plain list of `{name, display_name, category, url, trust_tier}`; grew from 374 → **812 sources**. Consumed two ways: `01-init.js` on fresh Mongo volumes, and `services/api/app/db/seed.py::ensure_seed()` on **every API startup** (bind-mounted live at `/app/sources-catalog.json`, `$setOnInsert` upsert — new names inserted, existing rows untouched). So loading a bigger catalog only needs `docker compose restart api`.
- **`infra/mongo-init/add_sources.py`** — idempotent generator that merges the 2026-10 expansion batch (gaming, technology, software, AI/ML, India, cars, F1, entertainment, marvel) into the catalog. Re-running adds 0. Dedup rules:
  - Google News `site:` feeds dedupe by the *target site*, not `news.google.com`; non-`site:` GN queries get unique markers.
  - Multi-tenant platforms (`github.io`, `substack.com`, `medium.com`, `googleblog.com`, …) dedupe by subdomain or first path segment.
  - `MULTI_DOMAINS` (normalized: `amazon.com`, `microsoft.com`, `nvidia.com`, `arxiv.org`, `reddit.com`, …) allows multiple feeds per domain where legitimate.
- Sites with known native RSS use it; everything else falls back to a Google News `site:` search feed (`gn()` helper).
- Feed spot-checks: GN fallbacks return valid XML; path-specific feeds verified (`aws-ai-blog`); redirects OK because the scraper uses `httpx(follow_redirects=True)` (`e27`, `nvidia-blog`). Fixes applied: `baeldung` → `/feed` (not `/rss.xml`); `theprint` → GN fallback (`site:theprint.in`) because the site serves HTML at its feed path.
- Pre-existing broken feeds noticed during sampling but **left as-is** (out of scope): `lwn-net`, `kotlin-blog` 404.

### Mobile UI / bottom navigation (2026-10-11)

- **`lucide-react`** added to `apps/web`.
- **Bottom nav** (`components/MobileNav.js`, replaces the old text-only mobile links): five icon tabs — Top stories (`/`), Sections (`/sections`), Search (`/search`), Bookmarks (`/bookmarks`), Settings (`/settings`). Visible ≤840px, fixed to bottom with `env(safe-area-inset-bottom)` padding; ≥44 px touch targets. Desktop keeps the sidebar (hidden on mobile).
- **New routes**: `/sections` (server component — category grid with unread counts + research topics with article counts + links to briefing/bookmarks so nothing is unreachable on mobile) and `/search` (client component — full-text search over titles/summaries/tags via `GET /articles?q=`, results rendered as `ArticleCard`s, supports `?q=` prefill).
- **Responsive CSS** (`globals.css`): toolbar stacks vertically with full-width 44 px inputs/buttons on mobile; article cards get tighter padding, smaller headings, 3-line summary clamp; `viewportFit: cover` in the layout viewport export for safe-area insets.

---

## What the user asked for

1. Follow `plans/plan.md`, improve it  
2. Local-only stack (no cloud)  
3. Next.js in **JavaScript** (not TypeScript)  
4. FastAPI, MongoDB, Capacitor, Redis, Ollama  
5. Backend + frontend in Docker  
6. Monorepo under `/home/naman/Projects`  
7. Check dependencies and set everything up  

---

## Decisions locked in (improvements over draft plan)

- **Capacitor** wrapping Next.js (not Flutter)  
- **JavaScript** frontend (no TS)  
- Shared contracts = **JSON Schema** in `packages/shared` (not a TS `shared-types` package)  
- Everything via **local Docker Compose**  
- `user_id = "local"` — **no auth planned** (app is in testing; no Play Store publish, per user 2026-10-11)  
- Ollama with **heuristic filter fallback** if model unavailable  
- Next.js `output: "standalone"` for Docker  
- Capacitor uses `server.url` → local Next (emulator `10.0.2.2:3000`), not forced static export for personal use  
- Redis pub/sub channel `scraper:commands` for manual scrape trigger  

---

## Repo layout (created)

```
news-dashboard/
├── AGENT.md                 ← this handoff
├── Plan.md                  ← improved canonical plan
├── README.md
├── Makefile                 ← make up | down | logs | health | scrape
├── package.json             ← npm workspaces: apps/web, apps/mobile-shell
├── .gitignore
├── apps/
│   ├── web/                 # Next.js 15 App Router, JS
│   │   ├── app/             # pages: /, /digest, /bookmarks, /settings, /article/[id]
│   │   ├── components/      # Feed, ArticleCard, Sidebar, AppShell, SettingsForm, …
│   │   ├── lib/api.js       # PUBLIC + INTERNAL API base URLs
│   │   ├── lib/time.js
│   │   ├── Dockerfile       # multi-stage standalone
│   │   ├── next.config.mjs  # output: "standalone"
│   │   ├── capacitor.config.json
│   │   └── public/          # manifest.json, icon.svg (PWA)
│   └── mobile-shell/        # Capacitor thin shell
│       ├── capacitor.config.json
│       ├── package.json
│       └── www/index.html   # fallback only
├── services/
│   ├── api/                 # FastAPI
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── app/
│   │       ├── main.py
│   │       ├── core/config.py, logging.py
│   │       ├── db/mongo.py, redis_client.py, seed.py
│   │       ├── models/schemas.py
│   │       └── routers/     # health, categories, sources, articles, preferences, stats, admin
│   └── scraper/
│       ├── Dockerfile
│       ├── requirements.txt
│       ├── config.py
│       ├── scheduler.py     # APScheduler + Redis trigger listener
│       ├── pipeline.py      # scrape → stage → filter → Mongo
│       ├── sources/rss.py
│       └── agent/filter.py, dedupe.py, categorize.py
├── packages/shared/
│   ├── article.schema.json
│   └── raw-item.schema.json
└── infra/
    ├── docker-compose.yml   # mongo, redis, ollama, ollama-init, api, scraper, web
    ├── .env / .env.example
    └── mongo-init/01-init.js
```

---

## System deps checked (host)

| Tool | Result |
|------|--------|
| Docker | 29.6.1 present |
| Docker Compose | v5.3.1 present |
| Node | v20.20.2 (nvm) |
| npm | 10.8.2 |
| Python | 3.14.4 (host; containers use 3.12) |
| Redis / Mongo / Ollama on host | **Not installed** — intended to run in Docker only |
| NVIDIA / GPU | `nvidia-smi` empty — Ollama will be CPU; GPU block commented in compose |

Projects folder was empty; project created at `/home/naman/Projects/news-dashboard`.

---

## Docker Compose services (intended)

| Service | Role | Host ports |
|---------|------|------------|
| `mongo` | Persistent DB + init indexes/seed | 27017 |
| `redis` | Staging + dedup + scrape trigger | 6379 |
| `ollama` | Local LLM | 11434 |
| `ollama-init` | One-shot `ollama pull` of model | — |
| `api` | FastAPI | 8000 |
| `scraper` | Scheduled + triggered scrape | — |
| `web` | Next.js standalone | 3000 |

Env file: `infra/.env` (already created from example).

Default model: `qwen2.5:3b-instruct-q4_K_M` (first pull can take a long time on CPU).

---

## API endpoints implemented

```
GET  /health
GET  /categories
GET  /sources
GET  /articles?category=&importance=&since=&page=&q=
GET  /articles/{id}
GET  /articles/digest?when=morning
GET  /articles/bookmarks
GET  /bookmarks                    # alias
POST /preferences
GET  /preferences
POST /articles/{id}/read
POST /articles/{id}/bookmark
GET  /stats
POST /admin/trigger-scrape         # Redis publish scraper:commands
```

Seeded RSS sources (API `seed.py` + mongo-init): Ars Technica, HN frontpage, NASA, BBC World.

---

## Frontend features scaffolded

- Feed with search, load-more, scrape trigger button  
- Category nav + unread badges  
- Morning briefing (`/digest`)  
- Bookmarks  
- Article detail + mark-read on mount  
- Settings (categories, mute keywords, digest hour, theme)  
- Keyboard shortcuts: `j`/`k`, `b`, `/`  
- Light/dark/system theme via `data-theme`  
- Reading-app aesthetic (near-monochrome + single accent)  

---

## What already failed / was fixed

1. **YAML error** in `infra/docker-compose.yml`: duplicate `environment` key under `ollama-init`  
   - **Fixed** — merged into one `environment` block  
2. **Second `docker compose up -d --build`** — aborted (session limit / user stop)  
   - **Not retried after abort**  
   - No images/containers confirmed running  

---

## Exact next steps for the continuing agent

The stack is already up (as of 2026-10-11 ~06:20). Quick re-check if needed:

```bash
cd /home/naman/Projects/news-dashboard
docker compose -f infra/docker-compose.yml ps          # all services should be Up/Healthy
curl -s http://localhost:8000/health | python3 -m json.tool
curl -s 'http://localhost:8000/articles?page_size=5' | python3 -m json.tool
# open http://localhost:3000
```

If the stack is down, bring it up with:

```bash
docker compose -f infra/docker-compose.yml --env-file infra/.env up -d --build
# or: make up
```

### 1. Final LLM-filtered scrape cycle — CONFIRMED

Completed with the fixed prompt: **`Scrape done: sources=4 raw=83 staged=83 passed=56 filtered=27`** (pre-fix run was 10/72). Staging queue drained to 0; new docs have LLM summaries. A follow-up cycle covering all 11 sources (4 RSS + 7 topic feeds) was then triggered via `POST /admin/trigger-scrape`.

To watch a running cycle:

```bash
docker logs news-dashboard-scraper-1 2>&1 | grep -aE 'Scrape done|Topics synced|ERROR' | tail -5
curl -s http://localhost:8000/topics            # live topic list + article counts
curl -s 'http://localhost:8000/articles?topic=quantum-computing'   # per-topic feed
```

### 2. Useful commands

```bash
make logs
docker compose -f infra/docker-compose.yml logs -f scraper api web ollama-init
curl -s -X POST http://localhost:8000/admin/trigger-scrape | python3 -m json.tool
```

### 3. Likely issues to watch

- **Ollama pull slow / fails** — scraper `agent/filter.py` falls back to heuristics; feed should still fill  
- **Mongo init only runs on empty volume** — API `ensure_seed()` also seeds categories/sources on startup  
- **Web can’t reach API from browser** — browser uses `NEXT_PUBLIC_API_URL=http://localhost:8000`; SSR uses `INTERNAL_API_URL=http://api:8000`  
- **RSS fetch failures** — check scraper logs / network from container  
- **Route order** — `/articles/digest` and `/articles/bookmarks` are registered before `/{id}` in `articles.py`  
- **Capacitor Android** not generated yet:

```bash
cd apps/mobile-shell && npm install && npx cap add android && npx cap sync
```

### 4. Optional follow-ups (not started)

- Confirm/optimize Reuters source URL (seeded disabled in mongo-init)  
- Distinguish title-dedup skips from LLM rejections in pipeline counters (`filtered_out` currently lumps both)  
- GPU passthrough: uncomment `deploy.resources` under `ollama` in compose when NVIDIA toolkit exists  
- Phase 2+: HTML scrapers, source health, archive/prune (auth explicitly out of scope — see locked decisions)  

---

## Commands cheat sheet

```bash
cd /home/naman/Projects/news-dashboard
make up          # build + start
make down
make logs
make health
make scrape
make ps
```

URLs once up:

- Web: http://localhost:3000  
- API docs: http://localhost:8000/docs  
- Mongo: localhost:27017  
- Redis: localhost:6379  
- Ollama: http://localhost:11434  

---

## Files intentionally not created / incomplete

- No `apps/mobile-shell/android/` (needs `cap add android`)  
- No npm `node_modules` installed on host (Docker builds install inside images)  
- No verification that Next.js builds cleanly (build happens in Docker `web` stage)  
- `~/plans/plan.md` was overwritten with a short pointer to this project’s `Plan.md`  

---

## Prompt starter for next session

> Continue from `/home/naman/Projects/news-dashboard/AGENT.md`.  
> Run `make up`, fix any build/runtime errors, verify `/health`, trigger scrape, confirm articles in API and UI at localhost:3000.  
> Everything must stay local (Docker). Do not introduce cloud services.

---

**Stop point:** Docker stack up and verified end-to-end (health → scrape → filter (heuristic + Ollama) → Mongo → API → web UI). Three bugs fixed during verification (API id serialization, trigger double-fire, over-strict LLM prompt); final cycle confirmed with passed=56/filtered=27. Research-topics feature (`topics.txt` → per-cycle sync → `GET /topics` → dynamic sidebar) implemented and verified. Repo pushed to `github.com/naman-1905/Personal-Intelligence-Dashboard` with one commit per file on `main`.
