.PHONY: setup gen-data load-bigquery dbt-run dbt-test export-tableau clean

setup:
	python3 -m venv venv
	. venv/bin/activate && pip install -r requirements.txt
	cp -n .env.example .env || true
	mkdir -p data/synthetic exports pipelines dbt/models/staging dbt/models/marts

gen-data:
	. venv/bin/activate && python pipelines/generate_synthetic.py

load-bigquery:
	. venv/bin/activate && python pipelines/load_to_bigquery.py

dbt-run:
	. venv/bin/activate && set -a && . ./.env && set +a && cd dbt && GOOGLE_APPLICATION_CREDENTIALS=../$$(basename "$$GOOGLE_APPLICATION_CREDENTIALS") dbt deps || true
	. venv/bin/activate && set -a && . ./.env && set +a && cd dbt && GOOGLE_APPLICATION_CREDENTIALS=../$$(basename "$$GOOGLE_APPLICATION_CREDENTIALS") dbt run

dbt-test:
	. venv/bin/activate && set -a && . ./.env && set +a && cd dbt && GOOGLE_APPLICATION_CREDENTIALS=../$$(basename "$$GOOGLE_APPLICATION_CREDENTIALS") dbt test

export-tableau:
	. venv/bin/activate && python pipelines/export_marts_for_tableau.py

clean:
	rm -rf data/synthetic/*.csv exports_gcp_bigquery/*.csv
