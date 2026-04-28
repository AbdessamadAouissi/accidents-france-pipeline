{{ config(materialized='view') }}

select
    accident_id,
    cast(nb_usagers as int)        as nb_usagers,
    cast(nb_tues as int)           as nb_tues,
    cast(nb_blesses_hosp as int)   as nb_blesses_hosp,
    cast(nb_blesses_legers as int) as nb_blesses_legers,
    worst_gravity,
    cast(is_fatal as boolean)      as is_fatal
from {{ source('staging_raw', 'severity') }}
