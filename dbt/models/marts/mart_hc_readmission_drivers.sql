with encounters as (
    select * from {{ ref('stg_fact_encounters') }}
),
reads as (
    select * from {{ ref('stg_fact_readmissions') }}
),
patients as (
    select * from {{ ref('stg_dim_patient') }}
),
diagnoses as (
    select * from {{ ref('stg_dim_diagnosis') }}
)

select
    e.admit_date_id,
    d.diagnosis_group,
    p.risk_tier,
    case
        when p.age < 18 then '0-17'
        when p.age < 35 then '18-34'
        when p.age < 50 then '35-49'
        when p.age < 65 then '50-64'
        else '65+'
    end as age_band,
    count(e.encounter_id) as total_encounters,
    sum(case when r.readmitted_30d = 1 then 1 else 0 end) as readmitted_count,
    sum(case when r.readmitted_30d = 1 then 1 else 0 end) * 100.0 / count(e.encounter_id) as readmission_rate_pct
from encounters e
join reads r on e.encounter_id = r.encounter_id
join patients p on e.patient_id = p.patient_id
join diagnoses d on e.diagnosis_code = d.diagnosis_code
group by 1, 2, 3, 4
