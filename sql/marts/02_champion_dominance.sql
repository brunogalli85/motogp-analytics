-- Pergunta 2: o fabricante campeão do mundo venceu quantas % das corridas da temporada?
-- Distingue títulos de domínio absoluto de títulos conquistados com regularidade.

DROP TABLE IF EXISTS marts.champion_dominance;

CREATE TABLE marts.champion_dominance AS
WITH season_wins AS (
    SELECT season, constructor_id, COUNT(*) AS wins
    FROM refined.race_wins
    WHERE is_premier_class = 1
    GROUP BY season, constructor_id
),
season_totals AS (
    SELECT season, SUM(wins) AS races
    FROM season_wins
    GROUP BY season
)
SELECT
    c.season,
    k.constructor_name                                      AS champion_constructor,
    COALESCE(sw.wins, 0)                                    AS champion_wins,
    t.races                                                 AS season_races,
    ROUND(100.0 * COALESCE(sw.wins, 0) / t.races, 1)        AS champion_win_pct
FROM refined.constructor_championships AS c
JOIN refined.constructors  AS k  USING (constructor_id)
JOIN season_totals         AS t  ON t.season = c.season
LEFT JOIN season_wins      AS sw ON sw.season = c.season AND sw.constructor_id = c.constructor_id
WHERE c.is_premier_class = 1
ORDER BY c.season;
