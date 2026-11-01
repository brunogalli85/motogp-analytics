-- Pergunta 1: quais fabricantes dominaram cada década na categoria principal (500cc/MotoGP)?
-- Mostra a era das fábricas europeias, o domínio japonês e a virada recente.
-- O percentual usa como base TODAS as vitórias da década (inclusive fabricante desconhecido).

DROP TABLE IF EXISTS marts.constructor_wins_by_decade;

CREATE TABLE marts.constructor_wins_by_decade AS
WITH wins AS (
    SELECT
        (w.season / 10) * 10 AS decade,
        k.constructor_name,
        COUNT(*)             AS wins
    FROM refined.race_wins     AS w
    JOIN refined.constructors  AS k USING (constructor_id)
    WHERE w.is_premier_class = 1
    GROUP BY 1, 2
),
with_totals AS (
    SELECT
        decade,
        constructor_name,
        wins,
        SUM(wins) OVER (PARTITION BY decade) AS decade_total_wins
    FROM wins
)
SELECT
    decade,
    constructor_name,
    wins,
    decade_total_wins,
    ROUND(100.0 * wins / decade_total_wins, 1)                      AS share_pct,
    RANK() OVER (PARTITION BY decade ORDER BY wins DESC)            AS rank_in_decade
FROM with_totals
WHERE constructor_name <> 'Desconhecido'
ORDER BY decade, rank_in_decade;
