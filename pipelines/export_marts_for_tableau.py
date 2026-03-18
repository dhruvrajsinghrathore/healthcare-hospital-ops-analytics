import os
from google.cloud import bigquery
from dotenv import load_dotenv
import warnings

load_dotenv()

def main():
    # Fix BigQuery Storage Warning manually by ignoring the noisy console output
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        
    project_id = os.environ.get("GCP_PROJECT")
    dataset_id = os.environ.get("BQ_ANALYTICS_DATASET", "public")
    
    if not project_id:
        print("Error: GCP_PROJECT environment variable not set.")
        return

    client = bigquery.Client(project=project_id)
        
    out_dir = "exports_gcp_bigquery"
    os.makedirs(out_dir, exist_ok=True)
    
    marts = [
        "mart_hc_kpi_daily",
        "mart_hc_kpi_department",
        "mart_hc_readmission_drivers",
        "mart_hc_cost_drivers"
    ]
    
    for mart in marts:
        out_path = os.path.join(out_dir, f"{mart}.csv")
        try:
            print(f"Exporting {project_id}.{dataset_id}.{mart} to {out_path}...")
            # Query the table directly from BigQuery
            query = f"SELECT * FROM `{project_id}.{dataset_id}.{mart}`"
            df = client.query(query).to_dataframe()
            
            # Write to CSV
            df.to_csv(out_path, index=False)
            print(f"Exported {len(df)} rows to {out_path}")
        except Exception as e:
            print(f"Failed to export {mart}: {e}")

if __name__ == '__main__':
    main()
