select * from {{ source('raw', 'dim_patient') }}
