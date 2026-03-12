select * from {{ source('raw', 'fact_encounters') }}
