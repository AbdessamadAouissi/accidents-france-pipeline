{{ config(materialized='view') }}

select
    cast(date as date)              as date,
    dep,
    cast(temperature_2m_max as double) as temp_max,
    cast(temperature_2m_min as double) as temp_min,
    cast(precipitation_sum as double)  as precipitation,
    cast(rain_sum as double)           as rain,
    cast(snowfall_sum as double)       as snowfall,
    cast(windspeed_10m_max as double)  as wind_max,
    case
        when precipitation_sum > 10 then 'pluvieux'
        when snowfall_sum > 0       then 'neigeux'
        when windspeed_10m_max > 50 then 'venteux'
        else 'normal'
    end as weather_category
from {{ source('staging_raw', 'meteo') }}
