with encounters as (
    select * from {{ ref('stg_fact_encounters') }}
),
costs as (
    select * from {{ ref('stg_fact_costs') }}
),
reads as (
    select * from {{ ref('stg_fact_readmissions') }}
),
departments as (
    select * from {{ ref('stg_dim_department') }}
)

select
    e.admit_date_id,
    d.department_name,
    count(e.encounter_id) as encounters_volume,
    avg(e.los_days) as average_los,
    sum(case when r.readmitted_30d = 1 then 1 else 0 end) * 100.0 / count(e.encounter_id) as readmission_rate_pct,
    avg(c.total_cost) as average_cost_per_encounter
from encounters e
join departments d on e.department_id = d.department_id
left join costs c on e.encounter_id = c.encounter_id
left join reads r on e.encounter_id = r.encounter_id
group by 1, 2
