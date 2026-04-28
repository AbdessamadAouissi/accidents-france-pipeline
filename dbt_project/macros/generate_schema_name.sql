-- Override du comportement par défaut de dbt qui préfixe les schemas avec le nom de la base.
-- Sans ce macro : schéma "marts" devient "main_marts" dans DuckDB.
-- Avec ce macro  : schéma "marts" reste "marts".
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
