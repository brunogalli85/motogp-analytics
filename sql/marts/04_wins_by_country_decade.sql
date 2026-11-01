-- Pergunta 4: quais países mais venceram em cada década (todas as categorias)?
-- Usa a nacionalidade registrada na própria vitória.

DROP TABLE IF EXISTS marts.wins_by_country_decade;

CREATE TABLE marts.wins_by_country_decade AS
WITH wins AS (
    SELECT
        (season / 10) * 10                       AS decade,
        COALESCE(rider_country_code, 'N/D')      AS country_code,
        COUNT(*)                                 AS wins,
        SUM(is_premier_class)                    AS premier_class_wins
    FROM refined.race_wins
    GROUP BY 1, 2
)
SELECT
    decade,
    country_code,
    wins,
    premier_class_wins,
    ROUND(100.0 * wins / SUM(wins) OVER (PARTITION BY decade), 1) AS share_pct,
    RANK() OVER (PARTITION BY decade ORDER BY wins DESC)          AS rank_in_decade
FROM wins
ORDER BY decade, rank_in_decade;
