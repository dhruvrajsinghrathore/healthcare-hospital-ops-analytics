import os
import numpy as np
import pandas as pd
from faker import Faker
from datetime import datetime, timedelta

fake = Faker()
Faker.seed(42)
np.random.seed(42)

OUT_DIR = "data/synthetic"
os.makedirs(OUT_DIR, exist_ok=True)

def save(df: pd.DataFrame, name: str) -> None:
    path = os.path.join(OUT_DIR, f"{name}.csv")
    df.to_csv(path, index=False)
    print(f"wrote {path} rows={len(df)}")

def gen_dim_date(start="2022-01-01", end="2025-12-31") -> pd.DataFrame:
    s = datetime.strptime(start, "%Y-%m-%d")
    e = datetime.strptime(end, "%Y-%m-%d")
    dates = [s + timedelta(days=i) for i in range((e - s).days + 1)]
    return pd.DataFrame({
        "date_id": [d.strftime("%Y%m%d") for d in dates],
        "date": [d.strftime("%Y-%m-%d") for d in dates],
        "year": [d.year for d in dates],
        "month": [d.month for d in dates],
        "day": [d.day for d in dates],
        "week": [int(d.strftime("%U")) for d in dates],
        "dow": [d.weekday() for d in dates],
        "is_weekend": [1 if d.weekday() >= 5 else 0 for d in dates],
    })

def main(n_patients=25000, n_encounters=110000) -> None:
    hospitals = pd.DataFrame({
        "hospital_id": [f"H{str(i).zfill(4)}" for i in range(1, 41)],
        "hospital_name": [fake.company() + " Hospital" for _ in range(40)],
        "state": [fake.state_abbr() for _ in range(40)],
        "bed_capacity": np.random.randint(120, 700, 40),
        "teaching_flag": np.random.choice([0, 1], 40, p=[0.7, 0.3]),
    })

    departments = ["ER","ICU","Surgery","Cardiology","Oncology","Orthopedics","Neurology","Pediatrics","Internal Medicine"]
    dim_department = pd.DataFrame({
        "department_id": [f"D{str(i).zfill(3)}" for i in range(1, len(departments) + 1)],
        "department_name": departments,
    })

    diag = [
        ("I10", "Hypertension"),
        ("E11", "Type 2 Diabetes"),
        ("J18", "Pneumonia"),
        ("I21", "Myocardial Infarction"),
        ("N18", "Chronic Kidney Disease"),
        ("K35", "Appendicitis"),
        ("S72", "Femur Fracture"),
        ("A41", "Sepsis"),
        ("F32", "Depression"),
    ]
    dim_diagnosis = pd.DataFrame(diag, columns=["diagnosis_code", "diagnosis_group"])

    patients = pd.DataFrame({
        "patient_id": [f"P{str(i).zfill(7)}" for i in range(1, n_patients + 1)],
        "age": np.clip(np.random.normal(50, 18, n_patients).astype(int), 0, 95),
        "sex": np.random.choice(["F", "M"], n_patients),
        "zip3": np.random.randint(700, 999, n_patients),
        "chronic_count": np.clip(np.random.poisson(1.3, n_patients), 0, 8),
        "risk_tier": np.random.choice(["low", "medium", "high"], n_patients, p=[0.55, 0.33, 0.12]),
    })

    start = pd.Timestamp("2022-01-01")
    end = pd.Timestamp("2025-12-31")
    # Wrap in pd.Series for proper datetimelike properties later
    admit_dates = pd.Series(pd.to_datetime(np.random.choice(pd.date_range(start, end), n_encounters)))

    enc = pd.DataFrame({
        "encounter_id": [f"E{str(i).zfill(9)}" for i in range(1, n_encounters + 1)],
        "patient_id": np.random.choice(patients["patient_id"], n_encounters),
        "hospital_id": np.random.choice(hospitals["hospital_id"], n_encounters),
        "department_id": np.random.choice(dim_department["department_id"], n_encounters),
        "diagnosis_code": np.random.choice(dim_diagnosis["diagnosis_code"], n_encounters),
        "admit_date": admit_dates,
        "admit_type": np.random.choice(["emergency", "elective", "urgent"], n_encounters, p=[0.62, 0.25, 0.13]),
    })

    dept_factor_map = {d: f for d, f in zip(dim_department["department_id"], np.random.uniform(0.8, 1.6, len(dim_department)))}
    enc["dept_factor"] = enc["department_id"].map(dept_factor_map)

    enc = enc.merge(patients[["patient_id","chronic_count","risk_tier"]], on="patient_id", how="left")
    risk_factor = enc["risk_tier"].map({"low": 0.9, "medium": 1.1, "high": 1.4})

    base_los = np.random.lognormal(mean=1.15, sigma=0.55, size=n_encounters)
    los = np.clip((base_los * enc["dept_factor"] * risk_factor).astype(int) + 1, 1, 35)
    enc["los_days"] = los
    discharge_date = enc["admit_date"] + pd.to_timedelta(enc["los_days"], unit="D")

    payer = np.random.choice(["Medicare","Medicaid","Commercial","Self-pay"], n_encounters, p=[0.37, 0.23, 0.33, 0.07])
    severity = np.clip(np.random.normal(0, 1, n_encounters), -2.5, 2.5)
    cost = 600 + (enc["los_days"] * 520) + (enc["chronic_count"] * 180) + (np.maximum(severity, 0) * 420)
    cost += np.where(payer == "Commercial", 250, 0)
    cost += np.random.normal(0, 240, n_encounters)
    cost = np.clip(cost, 150, 90000)

    fact_costs = pd.DataFrame({
        "encounter_id": enc["encounter_id"],
        "payer_type": payer,
        "total_cost": np.round(cost, 2),
    })

    diag_factor = enc["diagnosis_code"].map({
        "A41": 0.06, "N18": 0.04, "I21": 0.035, "J18": 0.03,
        "E11": 0.025, "I10": 0.02, "S72": 0.02, "K35": 0.015, "F32": 0.018
    }).fillna(0.02)
    readmit_prob = np.clip(
        0.03
        + diag_factor
        + enc["risk_tier"].map({"low": 0.0, "medium": 0.015, "high": 0.04})
        + (np.minimum(enc["los_days"], 10) * 0.001),
        0.01, 0.35
    )
    readmit_flag = (np.random.rand(n_encounters) < readmit_prob).astype(int)
    readmit_days = np.where(readmit_flag == 1, np.random.randint(3, 31, n_encounters), None)

    fact_readmissions = pd.DataFrame({
        "encounter_id": enc["encounter_id"],
        "readmitted_30d": readmit_flag,
        "readmit_days": readmit_days,
    })

    fact_encounters = enc.drop(columns=["admit_date"]).copy()
    fact_encounters["admit_date_id"] = admit_dates.dt.strftime("%Y%m%d")
    fact_encounters["discharge_date_id"] = discharge_date.dt.strftime("%Y%m%d")
    fact_encounters = fact_encounters.drop(columns=["dept_factor"])

    save(gen_dim_date(), "dim_date")
    save(hospitals, "dim_hospital")
    save(dim_department, "dim_department")
    save(dim_diagnosis, "dim_diagnosis")
    save(patients, "dim_patient")
    save(fact_encounters, "fact_encounters")
    save(fact_costs, "fact_costs")
    save(fact_readmissions, "fact_readmissions")

if __name__ == "__main__":
    main()
