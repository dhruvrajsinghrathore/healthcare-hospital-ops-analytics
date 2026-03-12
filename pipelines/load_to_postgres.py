import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import pandas as pd
from contextlib import closing
from dotenv import load_dotenv

load_dotenv()

def ensure_database():
    db_name = os.environ.get("PGDATABASE", "healthcare")
    user = os.environ.get("PGUSER", "postgres")
    password = os.environ.get("PGPASSWORD", "postgres")
    host = os.environ.get("PGHOST", "localhost")
    port = os.environ.get("PGPORT", "5432")

    try:
        conn = psycopg2.connect(host=host, port=port, dbname=db_name, user=user, password=password)
        conn.close()
    except psycopg2.OperationalError as e:
        if "does not exist" in str(e):
            print(f"Database {db_name} does not exist. Creating...")
            conn = psycopg2.connect(host=host, port=port, dbname="postgres", user=user, password=password)
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            with closing(conn.cursor()) as cur:
                cur.execute(f"CREATE DATABASE {db_name};")
            conn.close()
        else:
            raise e

def main():
    ensure_database()
    conn = psycopg2.connect(
        host=os.environ.get("PGHOST", "localhost"),
        port=os.environ.get("PGPORT", "5432"),
        dbname=os.environ.get("PGDATABASE", "healthcare"),
        user=os.environ.get("PGUSER", "postgres"),
        password=os.environ.get("PGPASSWORD", "postgres")
    )
    conn.autocommit = True
    
    with closing(conn.cursor()) as cur:
        cur.execute("CREATE SCHEMA IF NOT EXISTS raw;")
        print("Ensured schema 'raw' exists.")
        
        data_dir = "data/synthetic"
        if not os.path.exists(data_dir):
            print(f"Directory {data_dir} does not exist. Run generator first.")
            return

        files = [f for f in os.listdir(data_dir) if f.endswith(".csv")]
        
        for file in files:
            table_name = file.replace(".csv", "")
            file_path = os.path.join(data_dir, file)
            
            df = pd.read_csv(file_path, nrows=100)
            
            create_col_statements = []
            for col in df.columns:
                dtype = str(df[col].dtype)
                if "int" in dtype:
                    pg_type = "INTEGER"
                elif "float" in dtype:
                    pg_type = "NUMERIC"
                else:
                    pg_type = "VARCHAR(255)"
                create_col_statements.append(f"{col} {pg_type}")
                
            create_table_sql = f"CREATE TABLE IF NOT EXISTS raw.{table_name} (" + ", ".join(create_col_statements) + ");"
            
            cur.execute(f"DROP TABLE IF EXISTS raw.{table_name} CASCADE;")
            cur.execute(create_table_sql)
            print(f"Created table raw.{table_name}")
            
            with open(file_path, 'r') as f:
                copy_sql = f"COPY raw.{table_name} FROM STDIN WITH CSV HEADER"
                cur.copy_expert(copy_sql, f)
            print(f"Loaded {file_path} into raw.{table_name}")

    print("Postgres loading complete.")

if __name__ == '__main__':
    main()
