with encounters as (
    select * from {{ ref('stg_fact_encounters') }}
),
costs as (
    select * from {{ ref('stg_fact_costs') }}
),
departments as (
    select * from {{ ref('stg_dim_department') }}
)

select
    e.admit_date_id,
    d.department_name,
    c.payer_type,
    count(e.encounter_id) as total_encounters,
    avg(c.total_cost) as average_cost,
    sum(c.total_cost) as total_cost,
    sum(e.los_days) as total_los_days,
    sum(c.total_cost) / nullif(sum(e.los_days), 0) as average_cost_per_los_day
from encounters e
join costs c on e.encounter_id = c.encounter_id
join departments d on e.department_id = d.department_id
group by 1, 2, 3
