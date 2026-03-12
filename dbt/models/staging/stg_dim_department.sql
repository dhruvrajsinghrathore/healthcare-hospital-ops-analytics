select * from {{ source('raw', 'dim_department') }}
