.PHONY: dev reset seed

dev:
	docker compose up --build

reset:
	docker compose down -v --remove-orphans

seed:
	docker compose run --rm mssql-init
