-- Números gerais do campeonato, para os cartões do dashboard.

DROP TABLE IF EXISTS marts.kpi_summary;

CREATE TABLE marts.kpi_summary AS
SELECT
    MIN(w.season)                                                          AS first_season,
    MAX(w.season)                                                          AS last_season,
    COUNT(*)                                                               AS total_race_wins,
    SUM(w.is_premier_class)                                                AS premier_class_wins,
    COUNT(DISTINCT CASE WHEN r.rider_name <> 'Desconhecido' THEN w.rider_id END)             AS distinct_winning_riders,
    COUNT(DISTINCT CASE WHEN k.constructor_name <> 'Desconhecido' THEN w.constructor_id END) AS distinct_winning_constructors,
    COUNT(DISTINCT w.rider_country_code)                                   AS distinct_winning_countries
FROM refined.race_wins    AS w
JOIN refined.riders       AS r USING (rider_id)
JOIN refined.constructors AS k USING (constructor_id);
