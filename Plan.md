# Personal News Dashboard — Build Plan (improved)

Living plan for `/home/naman/Projects/news-dashboard`. Supersedes the draft in `~/plans/plan.md` where they disagree.

## Decisions locked in

| Topic | Decision |
|-------|----------|
| Mobile | **Capacitor** wrapping Next.js (not Flutter) |
| Frontend language | **JavaScript** (not TypeScript) |
| Hosting | **Local only** — Docker Compose on this machine |
| Shared contracts | JSON Schema in `packages/shared` (not a TS types package) |
| Auth | **None** — `user_id = "local"`; no auth planned while in testing, no Play Store publish |
| Storage | Summary + link only (not full article body) |
| LLM | Local Ollama; heuristic fallback if model unavailable |

## Goal

One self-hosted system that:

- Scrapes only categories/sources you enable
- Refreshes on a 6h schedule (+ light hourly pass)
- Filters with a **local** LLM (Ollama) before Mongo writes
- Serves via FastAPI → Next.js (web + Capacitor)
- No algorithmic feed / engagement bait

## Architecture

```
Scraper (Python) → Redis staging → Ollama filter → MongoDB
                                         ↑
                              FastAPI (only public gate)
                                         ↓
                         Next.js web  ←→  Capacitor shell
```

Infra services (all local containers): `mongo`, `redis`, `ollama`, `api`, `scraper`, `web`.

## Monorepo

```
news-dashboard/
├── apps/web                 # Next.js (JS), App Router, PWA manifest
├── apps/mobile-shell        # Capacitor config + android/ios projects
├── services/api             # FastAPI
├── services/scraper         # APScheduler workers
├── packages/shared          # JSON schemas
├── infra/docker-compose.yml
└── Plan.md
```

## Improvements over the draft plan

1. **JS-first frontend** — matches the requirement; avoids TS build friction for a personal app.
2. **Heuristic LLM fallback** — first boot / CPU-only machines still populate the feed while `ollama pull` runs.
3. **Redis command channel** — `POST /admin/trigger-scrape` publishes to `scraper:commands` (plus key fallback).
4. **`scrape_runs` collection** — operational visibility when a source goes silent.
5. **Internal vs public API URL** — Next.js server components call `http://api:8000` inside Docker; browser uses `http://localhost:8000`.
6. **Standalone Next output** — slim production image via `output: "standalone"`.
7. **Capacitor `server.url`** — points at local Next (no static export required for personal use); static `www/` is fallback only.
8. **Mute keywords applied in API** — never reach the client payload.
9. **Seeded trusted RSS set** — Ars, HN, NASA, BBC World (Reuters sample disabled until URL verified).

## API surface

```
GET  /health
GET  /categories
GET  /sources
GET  /articles?category=&importance=&since=&page=&q=
GET  /articles/{id}
GET  /articles/digest?when=morning
GET  /articles/bookmarks
GET  /bookmarks
POST /preferences
GET  /preferences
POST /articles/{id}/read
POST /articles/{id}/bookmark
GET  /stats
POST /admin/trigger-scrape
```

## Phased delivery

**Phase 1 — Skeleton (implemented)**  
Mongo + Redis + API `/health`, RSS scrape pipeline, Next.js cards, Docker Compose, Capacitor shell scaffold.

**Phase 2 — Pipeline hardening**  
More sources, HTML scrapers with robots/UA/delay, better Ollama prompts, source health metrics.

**Phase 3 — Frontend polish**  
Drag-reorder categories, swipe gestures, stronger unread badges, settings UX.

**Phase 4 — Focus**  
Digest notifications (local only), keyboard polish, time-saved accuracy.

**Phase 5 — Mobile**  
`cap add android`, device testing, optional local push for `importance=high`.

**Phase 6 — Hardening**  
Backoff/retry, archive after 30d, prune weak sources.

**Phase 7 — Play Store (optional)**  
No auth (explicitly not planned for now — testing only, no Play Store publish). Privacy policy / ToS review per source — only ever if a publish is actually pursued.

## Local ops

```bash
make up       # build & start full stack
make health
make scrape
make logs
make down
```

Ollama GPU: uncomment the `deploy.resources` block under `ollama` in `infra/docker-compose.yml` when NVIDIA Container Toolkit is installed.

## Open product choices (still soft)

- Exact 8–12 sources per category (edit Mongo `sources` or re-seed `infra/mongo-init`)
- Digest hour default: **7** (override in Settings)
- When/if Play Store is real: revisit redistribution ToS — personal scrape ≠ public redistribution
