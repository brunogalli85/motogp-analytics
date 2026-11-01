-- Corridas da categoria principal por temporada, para comparar com o calendário real.
-- Referências: 2019 = 19 corridas, 2020 = 14, 2021 = 18, 2022 = 20.
SELECT
    season,
    COUNT(*)                     AS corridas_no_dataset,
    COUNT(DISTINCT circuit_name) AS circuitos_distintos
FROM refined.race_wins
WHERE is_premier_class = 1
  AND season >= 2000
GROUP BY season
ORDER BY season;
