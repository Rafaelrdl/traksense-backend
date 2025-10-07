SHELL := /bin/bash

compose := docker compose -f infra/docker-compose.yml

.PHONY: up down logs migrate seed ps frontend

up:
	$(compose) up -d --build

down:
	$(compose) down -v

logs:
	$(compose) logs -f --tail=200

migrate:
	$(compose) exec api python manage.py migrate

seed:
	$(compose) exec api python scripts/seed_dev.py

ps:
	$(compose) ps

frontend:
	$(compose) --profile frontend up -d --build
