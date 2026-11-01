-- Resultados de carreira por piloto (do 1º ao 6º lugar), somando todas as categorias.
-- Nomes de colunas da origem padronizados e números convertidos para inteiro.
--
-- A origem tem pilotos repetidos (ex.: Nello Pagani, Lukas Tulovic). Tratamento:
--   1. linhas idênticas contam uma vez só (SELECT DISTINCT);
--   2. linhas diferentes do mesmo piloto são somadas (estatísticas divididas na origem).
-- Resultado: exatamente uma linha por piloto, para nada ser contado em dobro.

DROP TABLE IF EXISTS refined.rider_career_stats;

CREATE TABLE refined.rider_career_stats (
    rider_id      INTEGER PRIMARY KEY REFERENCES riders (rider_id),
    victories     INTEGER,
    second_places INTEGER,
    third_places  INTEGER,
    fourth_places INTEGER,
    fifth_places  INTEGER,
    sixth_places  INTEGER
);

WITH distinct_rows AS (
    SELECT DISTINCT
        TRIM("Rider")                                AS rider_name,
        CAST(NULLIF(TRIM("Victories"), '')      AS INTEGER) AS victories,
        CAST(NULLIF(TRIM("NumberofSecond"), '') AS INTEGER) AS second_places,
        CAST(NULLIF(TRIM("NumberofThird"), '')  AS INTEGER) AS third_places,
        CAST(NULLIF(TRIM("Numberof4th"), '')    AS INTEGER) AS fourth_places,
        CAST(NULLIF(TRIM("Numberof5th"), '')    AS INTEGER) AS fifth_places,
        CAST(NULLIF(TRIM("Numberof6th"), '')    AS INTEGER) AS sixth_places,
        NULLIF(UPPER(TRIM("Country")), '')                  AS country_code
    FROM raw.riders_finishing_positions
    WHERE TRIM("Rider") <> ''
)
INSERT INTO refined.rider_career_stats
SELECT
    r.rider_id,
    SUM(d.victories),
    SUM(d.second_places),
    SUM(d.third_places),
    SUM(d.fourth_places),
    SUM(d.fifth_places),
    SUM(d.sixth_places)
FROM distinct_rows AS d
JOIN refined.riders AS r ON r.rider_name = d.rider_name
GROUP BY r.rider_id;
