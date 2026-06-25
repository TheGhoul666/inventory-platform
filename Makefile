# BusOps Monorepo — root orchestration
# Usage: make <target>

.PHONY: all setup dev web backend android ios codegen seed clean

ROOT := $(shell pwd)

# ── Setup ─────────────────────────────────────────────────────────────────────
setup:
	@echo "=== Installing backend deps ==="
	cd backend && pip install -r requirements.txt
	@echo "=== Installing web deps ==="
	cd web && npm install
	@echo "=== Done. Run 'make dev' to start the full stack ==="

# ── Development ───────────────────────────────────────────────────────────────
dev:
	docker compose -f docker-compose.yml up --build

dev-backend:
	cd backend && uvicorn app.main:app --reload --port 8000

dev-web:
	cd web && npm run dev

# ── Mobile ────────────────────────────────────────────────────────────────────
android:
	cd mobile-android && ./gradlew assembleDebug

android-release:
	cd mobile-android && ./gradlew bundleRelease

ios:
	cd mobile-ios && xcodebuild -workspace BusOpsInventory.xcworkspace \
		-scheme BusOpsInventory -configuration Debug \
		-destination 'platform=iOS Simulator,name=iPhone 15 Pro'

# ── Code generation from OpenAPI spec ─────────────────────────────────────────
codegen: codegen-android codegen-ios codegen-web

codegen-spec:
	curl -s http://localhost:8000/api/openapi.json > shared/openapi/openapi.json

codegen-android:
	openapi-generator-cli generate \
		-i shared/openapi/openapi.json \
		-g kotlin \
		-o shared/generated/android \
		-c shared/codegen/android/config.yaml

codegen-ios:
	openapi-generator-cli generate \
		-i shared/openapi/openapi.json \
		-g swift5 \
		-o shared/generated/ios \
		-c shared/codegen/ios/config.yaml

codegen-web:
	openapi-generator-cli generate \
		-i shared/openapi/openapi.json \
		-g typescript-axios \
		-o shared/generated/web \
		-c shared/codegen/web/config.yaml

# ── Database ──────────────────────────────────────────────────────────────────
seed:
	cd backend && python ../scripts/seed.py

migrate:
	cd backend && alembic upgrade head

# ── Utilities ─────────────────────────────────────────────────────────────────
clean:
	cd mobile-android && ./gradlew clean
	cd web && rm -rf dist node_modules/.cache
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null; true
