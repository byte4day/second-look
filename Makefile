.PHONY: dev test check seed lint-backend lint-frontend \
	dev-backend dev-frontend docker-up docker-down

export DEMO_MODE ?= true

dev:
	@echo "Start backend: make dev-backend"
	@echo "Start frontend (other terminal): make dev-frontend"

dev-backend:
	cd backend && . .venv/bin/activate && \
		DEMO_MODE=$(DEMO_MODE) uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend:
	cd frontend && npm run dev -- --host 0.0.0.0 --port 5173

seed:
	cd backend && . .venv/bin/activate && python ../scripts/seed.py

lint-backend:
	cd backend && . .venv/bin/activate && ruff check app tests

lint-frontend:
	cd frontend && npm run lint && npx tsc --noEmit

test-backend:
	cd backend && . .venv/bin/activate && DEMO_MODE=true pytest -q

test-frontend:
	cd frontend && npm test -- --run

test: test-backend test-frontend

check: lint-backend test-backend lint-frontend test-frontend
	cd backend && . .venv/bin/activate && DEMO_MODE=true python ../scripts/eval_safety.py
	cd frontend && npx tsx ../scripts/check_contrast.ts

docker-up:
	docker compose up --build

docker-down:
	docker compose down
