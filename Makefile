.PHONY: up up-prod install install-prod down build logs migrate test lint shell seed seed-demo superuser clean restart ps backup restore health

up:
	podman-compose up -d

up-prod:
	podman-compose -f podman-compose.yml -f podman-compose.prod.yml up -d --build

install:
	bash scripts/install.sh

install-prod:
	bash scripts/install.sh --prod

down:
	podman-compose down

backup:
	bash scripts/backup.sh

restore:
	bash scripts/restore.sh $(DUMP)

health:
	bash scripts/healthcheck.sh

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
	podman-compose exec django python manage.py seed_base

seed-demo:
	podman-compose exec django python manage.py seed_demo

superuser:
	podman-compose exec django python manage.py createsuperuser

clean:
	podman-compose down -v
	podman system prune -f

restart: down up

ps:
	podman-compose ps
