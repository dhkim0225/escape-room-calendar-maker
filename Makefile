.PHONY: build up down restart logs clean

build:
	@echo "🔨 Building Docker image..."
	docker-compose build
	@echo "🚀 Starting service..."
	docker-compose up -d
	@echo "✅ Service is running at http://localhost:8501"

up:
	@echo "🚀 Starting service..."
	docker-compose up -d
	@echo "✅ Service is running at http://localhost:8501"

down:
	@echo "🛑 Stopping service..."
	docker-compose down

restart:
	@echo "🔄 Restarting service..."
	docker-compose restart

logs:
	docker-compose logs -f

clean:
	@echo "🧹 Cleaning up..."
	docker-compose down -v
	docker system prune -f
	@echo "✅ Cleanup complete"
