# Crypto Helper Telegram Bot - Simple Makefile
# Unified commands for all environments

.PHONY: help
help: ## Show this help message
	@echo "Crypto Helper Telegram Bot - Docker Commands"
	@echo "============================================="
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Main commands
.PHONY: build
build: ## Build Docker image
	docker-compose build

.PHONY: up
up: ## Start the bot
	docker-compose up -d

.PHONY: down
down: ## Stop the bot
	docker-compose down

.PHONY: restart
restart: ## Restart the bot
	docker-compose restart

.PHONY: logs
logs: ## Show logs
	docker-compose logs -f

.PHONY: shell
shell: ## Access container shell
	docker-compose exec crypto-helper-bot bash

.PHONY: status
status: ## Show container status
	docker-compose ps

# Development helpers
.PHONY: dev
dev: ## Start in development mode (with hot reload)
	LOG_LEVEL=DEBUG docker-compose up

.PHONY: test
test: ## Run tests
	docker-compose exec crypto-helper-bot python -m pytest tests/ -v

.PHONY: health
health: ## Check bot health
	curl -f http://localhost:8080/health || echo "Health check endpoint not available"

# Optional services
.PHONY: with-redis
with-redis: ## Start with Redis
	docker-compose --profile redis up -d

.PHONY: with-database
with-database: ## Start with PostgreSQL
	docker-compose --profile database up -d

.PHONY: with-all
with-all: ## Start with all services
	docker-compose --profile redis --profile database up -d

# Cleanup
.PHONY: clean
clean: ## Remove containers and images
	docker-compose down -v --rmi local

.PHONY: clean-all
clean-all: ## Remove everything (including volumes)
	docker-compose down -v --rmi all
	docker system prune -f

# Quick start
.PHONY: quick-start
quick-start: ## Quick start (build + up + logs)
	make build && make up && sleep 5 && make logs