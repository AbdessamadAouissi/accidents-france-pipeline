-- Patterns temporels (jour × heure) pour heatmap saisonnalité.
{{ config(materialized='table') }}

select
    day_of_week,
    hour,
    time_of_day,
    count(*)                              as nb_accidents,
    sum(nb_tues)                          as nb_tues,
    avg(nb_usagers)                       as avg_usagers,
    sum(case when is_fatal then 1 else 0 end) as nb_accidents_mortels
from {{ ref('fct_accidents') }}
group by day_of_week, hour, time_of_day
order by day_of_week, hour
