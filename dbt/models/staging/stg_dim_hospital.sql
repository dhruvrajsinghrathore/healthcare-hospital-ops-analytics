select * from {{ source('raw', 'dim_hospital') }}
