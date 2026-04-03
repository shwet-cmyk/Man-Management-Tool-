.PHONY: dev reset seed prepr-check

dev:
	docker compose up --build

reset:
	docker compose down -v --remove-orphans

seed:
	docker compose run --rm mssql-init

prepr-check:
	python tools/pre_pr_guardrail_check.py
