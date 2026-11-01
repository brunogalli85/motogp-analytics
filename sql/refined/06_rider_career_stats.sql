-- Resultados de carreira por piloto (do 1º ao 6º lugar), somando todas as categorias.
-- Nomes de colunas da origem padronizados e números convertidos para inteiro.

DROP TABLE IF EXISTS refined.rider_career_stats;

CREATE TABLE refined.rider_career_stats (
    rider_id      INTEGER NOT NULL REFERENCES riders (rider_id),
    victories     INTEGER,
    second_places INTEGER,
    third_places  INTEGER,
    fourth_places INTEGER,
    fifth_places  INTEGER,
    sixth_places  INTEGER
);

INSERT INTO refined.rider_career_stats
SELECT
    r.rider_id,
    CAST(NULLIF(TRIM(f."Victories"), '')      AS INTEGER),
    CAST(NULLIF(TRIM(f."NumberofSecond"), '') AS INTEGER),
    CAST(NULLIF(TRIM(f."NumberofThird"), '')  AS INTEGER),
    CAST(NULLIF(TRIM(f."Numberof4th"), '')    AS INTEGER),
    CAST(NULLIF(TRIM(f."Numberof5th"), '')    AS INTEGER),
    CAST(NULLIF(TRIM(f."Numberof6th"), '')    AS INTEGER)
FROM raw.riders_finishing_positions AS f
JOIN refined.riders AS r ON r.rider_name = TRIM(f."Rider");
