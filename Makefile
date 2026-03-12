.PHONY: setup gen-data up load-postgres dbt-run dbt-test export-powerbi down clean

setup:
	python3 -m venv venv
	. venv/bin/activate && pip install -r requirements.txt
	cp -n .env.example .env || true
	mkdir -p data/synthetic exports pipelines dbt/models/staging dbt/models/marts

gen-data:
	. venv/bin/activate && python pipelines/generate_synthetic.py

up:
	docker-compose up -d
	echo "Waiting for PostgreSQL to be ready..."
	sleep 5

load-postgres:
	. venv/bin/activate && python pipelines/load_to_postgres.py

dbt-run:
	. venv/bin/activate && cd dbt && dbt run

dbt-test:
	. venv/bin/activate && cd dbt && dbt test

export-powerbi:
	. venv/bin/activate && python pipelines/export_marts_for_powerbi.py

down:
	docker-compose down

clean:
	rm -rf data/synthetic/* exports/*
	docker-compose down -v
