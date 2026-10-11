COMPOSE=docker compose -f infra/docker-compose.yml --env-file infra/.env

.PHONY: up down logs ps rebuild scrape health

up:
	$(COMPOSE) up -d --build

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f

ps:
	$(COMPOSE) ps

rebuild:
	$(COMPOSE) up -d --build --force-recreate

scrape:
	curl -s -X POST http://localhost:8000/admin/trigger-scrape | python3 -m json.tool

health:
	curl -s http://localhost:8000/health | python3 -m json.tool
