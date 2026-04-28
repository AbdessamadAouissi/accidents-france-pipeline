-- Test singulier : aucun accident ne peut avoir une date dans le futur.
select accident_id, accident_date
from {{ ref('fct_accidents') }}
where accident_date > current_date
