-- Couche staging : nettoyage 1:1, typage strict.
{{ config(materialized='view') }}

with src as (
    select * from {{ source('staging_raw', 'accidents') }}
)

select
    accident_id,
    cast(date as date)            as accident_date,
    extract(year from date)::int  as year,
    extract(month from date)::int as month,
    extract(dow from date)::int   as day_of_week,
    cast(hour as int)             as hour,
    case
        when hour between 6  and 9  then 'matin'
        when hour between 10 and 13 then 'midi'
        when hour between 14 and 17 then 'apres_midi'
        when hour between 18 and 21 then 'soiree'
        else 'nuit'
    end                           as time_of_day,
    cast(lat as double)           as lat,
    cast(lon as double)           as lon,
    cast(dep as varchar)          as dep,
    cast(com as varchar)          as commune_code,
    light_condition,
    weather_condition
from src
where accident_id is not null
  and date is not null
