import os
import psycopg2
from contextlib import closing
from dotenv import load_dotenv

load_dotenv()

def main():
    conn = psycopg2.connect(
        host=os.environ.get("PGHOST", "localhost"),
        port=os.environ.get("PGPORT", "5432"),
        dbname=os.environ.get("PGDATABASE", "healthcare"),
        user=os.environ.get("PGUSER", "postgres"),
        password=os.environ.get("PGPASSWORD", "postgres")
    )
    
    out_dir = "exports"
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
            with conn.cursor() as cur:
                with open(out_path, 'w', newline='') as f:
                    query = f"COPY public.{mart} TO STDOUT WITH CSV HEADER"
                    cur.copy_expert(query, f)
            print(f"Exported {mart} to {out_path}")
        except Exception as e:
            conn.rollback()
            print(f"Failed to export {mart}: {e}")

if __name__ == '__main__':
    main()
