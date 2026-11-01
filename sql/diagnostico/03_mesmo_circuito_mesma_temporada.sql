-- Houve mais de uma corrida no mesmo circuito, na mesma temporada e categoria?
-- Em 2020 e 2021 isso aconteceu de verdade (Jerez, Misano, Aragón, Áustria, Catar...).
-- Se esta consulta vier vazia, o dataset guardou só uma vitória por circuito e temporada.
SELECT
    season,
    class_name,
    circuit_name,
    COUNT(*) AS vitorias
FROM refined.race_wins
WHERE season BETWEEN 2019 AND 2022
GROUP BY season, class_name, circuit_name
HAVING COUNT(*) > 1
ORDER BY season, class_name, circuit_name;
