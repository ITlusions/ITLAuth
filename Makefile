# Makefile for itl-kubectl-oidc-setup development

.PHONY: help install install-dev test lint format clean build upload upload-test

help:  ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install:  ## Install the package
	pip install .

install-dev:  ## Install the package in development mode with dev dependencies
	pip install -e .[dev]

test:  ## Run tests
	python -m pytest tests/ -v

test-coverage:  ## Run tests with coverage report
	python -m pytest tests/ -v --cov=itl_kubectl_oidc_setup --cov-report=html --cov-report=term

lint:  ## Run linting checks
	flake8 itl_kubectl_oidc_setup/
	mypy itl_kubectl_oidc_setup/

format:  ## Format code with black
	black itl_kubectl_oidc_setup/ tests/

format-check:  ## Check if code is properly formatted
	black --check itl_kubectl_oidc_setup/ tests/

clean:  ## Clean build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete

build:  ## Build the package
	python -m build

build-wheel:  ## Build wheel only
	python -m build --wheel

build-sdist:  ## Build source distribution only
	python -m build --sdist

upload-test:  ## Upload to test PyPI
	python -m twine upload --repository testpypi dist/*

upload:  ## Upload to PyPI
	python -m twine upload dist/*

run:  ## Run the tool locally
	python -m itl_kubectl_oidc_setup

check-all: format-check lint test  ## Run all checks (format, lint, test)

# Development workflow
dev-setup: install-dev  ## Setup development environment
	@echo "Development environment ready!"
	@echo "Run 'make test' to run tests"
	@echo "Run 'make run' to test the tool"

# Release workflow  
release-test: clean build upload-test  ## Build and upload to test PyPI

release: clean build upload  ## Build and upload to PyPI