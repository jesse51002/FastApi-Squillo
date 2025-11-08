.PHONY: help install dev run test clean lint format

run:
	poetry run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000 --log-level debug

lint:
	poetry run ruff check src/

format:
	poetry run black src/

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
