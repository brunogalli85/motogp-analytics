-- Pergunta 3: quem são os maiores vencedores da categoria principal?
-- Inclui o período de vitórias e em quantas temporadas diferentes o piloto venceu.

DROP TABLE IF EXISTS marts.top_riders_premier;

CREATE TABLE marts.top_riders_premier AS
SELECT
    DENSE_RANK() OVER (ORDER BY COUNT(*) DESC) AS rank_position,
    r.rider_name,
    r.country_code,
    COUNT(*)                                   AS wins,
    COUNT(DISTINCT w.season)                   AS winning_seasons,
    MIN(w.season)                              AS first_win_season,
    MAX(w.season)                              AS last_win_season
FROM refined.race_wins AS w
JOIN refined.riders    AS r USING (rider_id)
WHERE w.is_premier_class = 1
  AND r.rider_name <> 'Desconhecido'
GROUP BY r.rider_id, r.rider_name, r.country_code
ORDER BY rank_position, r.rider_name;
