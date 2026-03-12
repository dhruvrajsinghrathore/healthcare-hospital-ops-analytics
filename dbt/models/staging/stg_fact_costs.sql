select * from {{ source('raw', 'fact_costs') }}
