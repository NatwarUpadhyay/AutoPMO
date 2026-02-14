# AutoPMO - Makefile (MVP)

.PHONY: help install-min run-api test lint format deps

help:
	@echo "Targets:"
	@echo "  install-min  - Install minimal deps for MVP API"
	@echo "  run-api      - Run FastAPI MVP server"
	@echo "  test         - Placeholder for tests"
	@echo "  lint         - Run flake8 if available"
	@echo "  format       - Run black if available"

install-min:
	python3 -m pip install --upgrade pip
	pip install fastapi uvicorn pydantic

run-api:
	python -m api.main

# Placeholder - no test suite yet in MVP
test:
	@echo "No tests in MVP. Add tests under tests/ in future commits."

lint:
	@if command -v flake8 >/dev/null 2>&1; then \
	  flake8 . ; \
	else \
	  echo "flake8 not installed" ; \
	fi

format:
	@if command -v black >/dev/null 2>&1; then \
	  black . ; \
	else \
	  echo "black not installed" ; \
	fi
