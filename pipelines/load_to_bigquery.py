import os
import glob
import pandas as pd
from google.cloud import bigquery
from dotenv import load_dotenv

load_dotenv()

def get_bigquery_type(dtype):
    dtype_str = str(dtype).lower()
    if 'int' in dtype_str:
        return bigquery.enums.SqlTypeNames.INT64
    elif 'float' in dtype_str:
        return bigquery.enums.SqlTypeNames.FLOAT64
    elif 'datetime' in dtype_str:
        return bigquery.enums.SqlTypeNames.TIMESTAMP
    elif 'bool' in dtype_str:
        return bigquery.enums.SqlTypeNames.BOOLEAN
    else:
        return bigquery.enums.SqlTypeNames.STRING

def main():
    project_id = os.environ.get("GCP_PROJECT")
    location = os.environ.get("BQ_LOCATION", "US")
    dataset_id = os.environ.get("BQ_RAW_DATASET", "raw")
    
    if not project_id:
        print("Error: GCP_PROJECT environment variable not set.")
        print("Please check your .env file and ensure GOOGLE_APPLICATION_CREDENTIALS is valid.")
        return

    # Initialize BigQuery client
    client = bigquery.Client(project=project_id, location=location)

    # Ensure dataset exists
    dataset_ref = f"{project_id}.{dataset_id}"
    dataset = bigquery.Dataset(dataset_ref)
    dataset.location = location
    try:
        client.get_dataset(dataset_ref)
        print(f"Dataset {dataset_ref} already exists.")
    except Exception:
        print(f"Dataset {dataset_ref} not found, creating it...")
        client.create_dataset(dataset, timeout=30)
        print(f"Created dataset {dataset_ref}")

    # Process all CSVs in data/synthetic
    csv_files = glob.glob('data/synthetic/*.csv')
    
    if not csv_files:
        print("No CSV files found in data/synthetic/. Please run `make gen-data` first.")
        return

    for csv_file in csv_files:
        table_name = os.path.basename(csv_file).replace('.csv', '')
        table_ref = f"{dataset_ref}.{table_name}"
        
        print(f"\nProcessing {csv_file} -> {table_ref}...")
        
        # Read a small sample to infer schema using pandas
        try:
            df_sample = pd.read_csv(csv_file, nrows=100)
        except Exception as e:
            print(f"Failed to read {csv_file}: {e}")
            continue

        # Build schema explicitly
        schema = []
        for col_name, dtype in df_sample.dtypes.items():
            bq_type = get_bigquery_type(dtype)
            # Make sure we don't have invalid column names 
            # (BigQuery is generally fine with alphanumeric + underscores)
            schema.append(bigquery.SchemaField(col_name, bq_type))
            
        print(f"Inferred schema with {len(schema)} columns.")

        job_config = bigquery.LoadJobConfig(
            schema=schema,
            source_format=bigquery.SourceFormat.CSV,
            write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
            # Skip the header row since we are defining schema
            skip_leading_rows=1,
        )

        try:
            with open(csv_file, "rb") as source_file:
                job = client.load_table_from_file(
                    source_file, table_ref, job_config=job_config
                )
            
            job.result()  # Wait for the job to complete
            
            table = client.get_table(table_ref)
            print(f"Successfully loaded {table.num_rows} rows and {len(table.schema)} columns to {table_ref}")
        except Exception as e:
            print(f"Failed to load {table_name}: {e}")

if __name__ == '__main__':
    main()
