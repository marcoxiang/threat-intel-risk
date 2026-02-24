.PHONY: up down logs

up:
	docker compose --env-file .env up --build

down:
	docker compose down

logs:
	docker compose logs -f --tail=200
