with encounters as (
    select * from {{ ref('stg_fact_encounters') }}
),
costs as (
    select * from {{ ref('stg_fact_costs') }}
),
reads as (
    select * from {{ ref('stg_fact_readmissions') }}
)

select
    e.admit_date_id,
    count(e.encounter_id) as encounters_volume,
    avg(e.los_days) as average_los,
    sum(case when r.readmitted_30d = 1 then 1 else 0 end) * 100.0 / count(e.encounter_id) as readmission_rate_pct,
    avg(c.total_cost) as average_cost_per_encounter
from encounters e
left join costs c on e.encounter_id = c.encounter_id
left join reads r on e.encounter_id = r.encounter_id
group by 1
