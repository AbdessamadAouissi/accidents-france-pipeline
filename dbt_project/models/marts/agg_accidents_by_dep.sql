-- Agrégation par département × année.
{{ config(materialized='table') }}

select
    dep,
    year,
    count(*)                              as nb_accidents,
    sum(nb_tues)                          as nb_tues,
    sum(nb_blesses_hosp)                  as nb_blesses_hosp,
    sum(nb_blesses_legers)                as nb_blesses_legers,
    sum(case when is_fatal then 1 else 0 end) as nb_accidents_mortels,
    round(100.0 * sum(case when is_fatal then 1 else 0 end) / count(*), 2)
                                          as taux_mortalite_pct
from {{ ref('fct_accidents') }}
group by dep, year
order by dep, year
