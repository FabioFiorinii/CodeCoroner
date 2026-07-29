.PHONY: up down build logs migrate test lint shell clean

up:
	podman-compose up -d

down:
	podman-compose down

build:
	podman-compose build

logs:
	podman-compose logs -f

migrate:
	podman-compose exec django python manage.py migrate

test:
	podman-compose exec django pytest

lint:
	podman-compose exec django ruff check .
	podman-compose exec django mypy .

shell:
	podman-compose exec django python manage.py shell

seed:
	podman-compose exec django python manage.py seed_demo

superuser:
	podman-compose exec django python manage.py createsuperuser

clean:
	podman-compose down -v
	podman system prune -f

restart: down up

ps:
	podman-compose ps
