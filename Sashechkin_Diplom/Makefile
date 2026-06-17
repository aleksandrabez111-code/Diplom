.PHONY: backend-install backend-migrate backend-seed backend-run docker-up docker-down

backend-install:
	cd backend && python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt

backend-migrate:
	cd backend && . .venv/bin/activate && alembic upgrade head

backend-seed:
	cd backend && . .venv/bin/activate && python -m scripts.seed

backend-run:
	cd backend && . .venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

docker-up:
	docker compose up --build

docker-down:
	docker compose down
