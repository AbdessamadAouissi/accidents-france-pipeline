# Dictionnaire de données

## Source ONISR — fichiers BAAC

### caracteristiques (1 ligne = 1 accident)

| Colonne brute | Colonne nettoyée | Type | Description |
|---|---|---|---|
| `Num_Acc` | `accident_id` | string | Identifiant unique d'accident |
| `an, mois, jour` | `date` | date | Date de l'accident |
| `hrmn` | `hour` | int (0-23) | Heure (extraite de hhmm) |
| `lat, long` | `lat, lon` | float | Coordonnées WGS84 (0 → NaN) |
| `dep` | `dep` | string | Code département (zfill 2) |
| `com` | `commune_code` | string | Code commune INSEE |
| `lum` | `light_condition` | string | Luminosité (mappée) |
| `atm` | `weather_condition` | string | Météo (mappée) |

### usagers (1 ligne = 1 personne)

| Colonne | Type | Description |
|---|---|---|
| `accident_id` | string | FK → caracteristiques |
| `gravity` | string | indemne / blesse_leger / blesse_hospitalise / tue |
| `age` | int | source_year - an_nais |

### severity (agrégé par accident)

| Colonne | Type | Description |
|---|---|---|
| `accident_id` | string | PK |
| `nb_usagers` | int | Nombre total d'usagers impliqués |
| `nb_tues` | int | Nombre de décès |
| `nb_blesses_hosp` | int | Blessés hospitalisés |
| `nb_blesses_legers` | int | Blessés légers |
| `worst_gravity` | string | Pire gravité observée |
| `is_fatal` | bool | nb_tues > 0 |

## Source Météo (Open-Meteo Archive API)

| Colonne | Type | Description |
|---|---|---|
| `date` | date | Jour |
| `dep` | string | Département (centroïde) |
| `temp_max, temp_min` | float | °C |
| `precipitation` | float | mm |
| `rain, snowfall` | float | mm |
| `wind_max` | float | km/h |
| `weather_category` | string | normal / pluvieux / neigeux / venteux |

## Mappings ONISR

### `lum` (luminosité)
| Code | Label |
|---|---|
| 1 | plein_jour |
| 2 | crepuscule_aube |
| 3 | nuit_sans_eclairage |
| 4 | nuit_eclairage_non_allume |
| 5 | nuit_eclairage_allume |

### `atm` (conditions atmosphériques)
| Code | Label |
|---|---|
| 1 | normale |
| 2 | pluie_legere |
| 3 | pluie_forte |
| 4 | neige_grele |
| 5 | brouillard_fumee |
| 6 | vent_fort_tempete |
| 7 | temps_eblouissant |
| 8 | temps_couvert |
| 9 | autre |

### `grav` (gravité usager)
| Code | Label |
|---|---|
| 1 | indemne |
| 2 | tue |
| 3 | blesse_hospitalise |
| 4 | blesse_leger |

## Marts dbt

### `marts.fct_accidents`
Table de faits enrichie : 1 ligne = 1 accident, jointe avec gravité + météo.

### `marts.agg_accidents_by_dep`
Agrégation département × année (KPIs).

### `marts.agg_temporal_patterns`
Heatmap heure × jour de semaine (saisonnalité).
