-- Jointure spatio-temporelle accidents × météo + gravité.
{{ config(materialized='view') }}

with accidents as (
    select * from {{ ref('stg_accidents') }}
),
severity as (
    select * from {{ ref('stg_severity') }}
),
meteo as (
    select * from {{ ref('stg_meteo') }}
)

select
    a.*,
    s.nb_usagers,
    s.nb_tues,
    s.nb_blesses_hosp,
    s.nb_blesses_legers,
    s.worst_gravity,
    s.is_fatal,
    m.temp_max,
    m.temp_min,
    m.precipitation,
    m.rain,
    m.snowfall,
    m.wind_max,
    m.weather_category
from accidents a
left join severity s using (accident_id)
left join meteo m
       on a.accident_date = m.date
      and a.dep = m.dep
