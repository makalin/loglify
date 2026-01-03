.PHONY: help install setup run api bot cli test clean docker-up docker-down

help:
	@echo "Loglify - Life Logging System"
	@echo ""
	@echo "Available commands:"
	@echo "  make setup      - Initial setup (venv, install deps, create .env)"
	@echo "  make install    - Install dependencies"
	@echo "  make run        - Run API + Telegram bot"
	@echo "  make api        - Run API server only"
	@echo "  make bot        - Run Telegram bot only"
	@echo "  make cli        - Show CLI help"
	@echo "  make test       - Run tests"
	@echo "  make clean      - Clean Python cache files"
	@echo "  make docker-up  - Start with Docker Compose"
	@echo "  make docker-down - Stop Docker Compose"

setup:
	@./setup.sh

install:
	@pip install -r requirements.txt

run:
	@python3 run.py

api:
	@uvicorn main:app --reload

bot:
	@python3 telegram_bot.py

cli:
	@python3 cli.py --help

test:
	@python3 -m pytest tests/ -v

clean:
	@find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete
	@find . -type f -name "*.pyo" -delete

docker-up:
	@docker-compose up -d --build

docker-down:
	@docker-compose down

