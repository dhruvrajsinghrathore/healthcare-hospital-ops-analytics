# 🏥 Healthcare Hospital Ops Analytics

## 📖 Overview
Hospitals face constant challenges in reducing Length of Stay (LOS), minimizing readmission rates, and managing cost per encounter, all while trying to increase department throughput and bed capacity utilization. 

This project simulates a **Healthcare Hospital Operations Analytics** end-to-end data pipeline. Real patient data is restricted by HIPAA and other regulations, so this project uses a Python-based synthetic data generator to create highly realistic encounter-level data.

The data flows through a modern data stack:
1. **Python** (Synthetic Data Generation)
2. **PostgreSQL** (Local Data Warehouse)
3. **dbt Core** (Data Transformation & Testing)
4. **Power BI** (Data Visualization via exported CSVs)

---

## 🏗️ Project Architecture & Components

*   **`pipelines/generate_synthetic.py`**: A Python script using `pandas`, `numpy`, and `Faker` to generate realistic star-schema data (Dimensions: Date, Hospital, Department, Diagnosis, Patient. Facts: Encounters, Costs, Readmissions).
*   **`docker-compose.yml`**: Provisions a local PostgreSQL 15 database to act as our Data Warehouse.
*   **`pipelines/load_to_postgres.py`**: A Python script that creates the target database (if missing) and a `raw` schema in PostgreSQL, automatically infers table structures from the generated CSVs, and uses `COPY` for bulk loading the data into the database.
*   **`dbt/` (Data Build Tool)**: Contains our transformation logic.
    *   **Staging Models (`stg_*`)**: Clean up and establish the base views from the `raw` tables.
    *   **Marts (`mart_*`)**: Business-level aggregated tables combining facts and dimensions to answer specific KPIs (e.g., daily KPIs, department KPIs, readmission drivers, cost drivers).
    *   **Tests (`schema.yml`)**: Asserts data quality (uniqueness, non-null values, referential integrity, and accepted value constraints).
*   **`pipelines/export_marts_for_powerbi.py`**: Extracts the finalized dbt mart tables into clean CSVs inside the `exports/` folder, which can be directly loaded into Power BI.

---

## 🚀 Step-by-Step Execution Guide

### Prerequisites
Make sure you have the following installed:
*   [Python 3.9+](https://www.python.org/downloads/)
*   [Docker & Docker Compose](https://docs.docker.com/get-docker/)
*   `make` (Usually pre-installed on Mac/Linux)
*   [Power BI Desktop](https://powerbi.microsoft.com/desktop/) (For the final visualization step)

### Step 1: Initial Setup
Clone the repository and run the setup command. This will create a virtual environment, install the required Python packages (including dbt and psycopg2), copy the environment variables template, and create necessary directories.

```bash
make setup
```

### Step 2: Generate Synthetic Data
Run the data generator to create realistic hospital data (2022-2025). This will populate the `data/synthetic/` folder with 8 CSV files representing our dimensions and facts.

```bash
make gen-data
```
*Verification:* Check the `data/synthetic` directory. You should see files like `dim_patient.csv`, `fact_encounters.csv`, etc.

### Step 3: Start the Data Warehouse
Start the local PostgreSQL database using Docker Compose in detached mode.

```bash
make up
```
*Verification:* Run `docker ps` to ensure the `healthcare_pg` container is running on port 5432.

### Step 4: Load Data into PostgreSQL
Load the generated CSVs from `data/synthetic/` into the `raw` schema of the PostgreSQL database. This script handles target database creation, schema setup, and fast bulk loading.

```bash
make load-postgres
```
*Verification:* The console output will confirm tables like `raw.dim_patient` and `raw.fact_encounters` were created and loaded.

### Step 5: Transform Data with dbt
Execute the dbt models to transform the raw data into business-ready KPI marts within the `public` schema.

```bash
make dbt-run
```
*Verification:* In your terminal, you will see dbt compile and run 8 view models (staging) and 4 table models (marts). All should show a green `SUCCESS` status.

### Step 6: Test Data Quality
Run dbt tests to ensure data integrity constraints are met (e.g., no orphaned records, no null IDs, valid admitted types).

```bash
make dbt-test
```
*Verification:* The terminal should show exactly 20 tests passing successfully.

### Step 7: Export to Power BI
Extract the final dbt mart tables into the `exports/` directory as CSV files, so they can be imported into Power BI without needing a direct database connection.

```bash
make export-powerbi
```
*Verification:* Check the `exports/` directory. You will find `mart_hc_kpi_daily.csv`, `mart_hc_kpi_department.csv`, `mart_hc_readmission_drivers.csv`, and `mart_hc_cost_drivers.csv`.

---

## 📊 Connecting to Power BI
1. Open **Power BI Desktop**.
2. Click **Get Data** -> **Text/CSV**.
3. Select the exported CSV files from the `exports/` folder:
   - `mart_hc_kpi_daily.csv`
   - `mart_hc_kpi_department.csv`
   - `mart_hc_readmission_drivers.csv`
   - `mart_hc_cost_drivers.csv`
4. Build your dashboard using the pre-calculated KPIs!

### Key KPIs to Visualize:
*   **Executive Overview**: Average LOS, Overall Readmission Rate (30d), Cost per Encounter, Encounters per Day.
*   **Department Performance**: Encounters volume, LOS distribution, and cost per department.
*   **Readmission Drivers**: Readmission rates sliced by diagnosis groups, risk tiers, and patient age bands.
*   **Cost Analysis**: Average cost per LOS day, total costs sliced by payer type (Medicare, Medicaid, Commercial, Self-pay).

---

## 🧹 Cleanup
When you are done, you can stop the database, remove the volumes, and clean all generated files using:

```bash
make clean
```
