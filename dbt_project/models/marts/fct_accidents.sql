-- Table de faits finale (1 ligne = 1 accident, enrichie).
{{ config(materialized='table') }}

select * from {{ ref('int_accidents_enriched') }}
