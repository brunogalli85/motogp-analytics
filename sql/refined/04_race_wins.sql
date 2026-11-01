-- Tabela fato: uma linha por vitória em Grande Prêmio.
-- Liga cada vitória ao piloto e ao fabricante pelas chaves das dimensões.
-- Limpeza: tira o símbolo ™ das categorias e marca a categoria principal
-- (500cc até 2001, MotoGP a partir de 2002).

DROP TABLE IF EXISTS refined.race_wins;

CREATE TABLE refined.race_wins (
    race_win_id        INTEGER PRIMARY KEY,
    season             INTEGER NOT NULL,
    class_name         TEXT    NOT NULL,
    is_premier_class   INTEGER NOT NULL,          -- 1 = 500cc/MotoGP
    circuit_name       TEXT,
    rider_id           INTEGER NOT NULL REFERENCES riders (rider_id),
    constructor_id     INTEGER NOT NULL REFERENCES constructors (constructor_id),
    rider_country_code TEXT                        -- nacionalidade na data da vitória
);

WITH cleaned AS (
    SELECT
        CAST(TRIM("Season") AS INTEGER)            AS season,
        TRIM(REPLACE("Class", '™', ''))            AS class_name,
        NULLIF(TRIM("Circuit"), '')                AS circuit_name,
        COALESCE(NULLIF(TRIM("Rider"), ''), 'Desconhecido')       AS rider_name,
        COALESCE(NULLIF(TRIM("Constructor"), ''), 'Desconhecido') AS constructor_name,
        NULLIF(UPPER(TRIM("Country")), '')         AS rider_country_code
    FROM raw.grand_prix_race_winners
)
INSERT INTO refined.race_wins (
    race_win_id, season, class_name, is_premier_class, circuit_name,
    rider_id, constructor_id, rider_country_code
)
SELECT
    ROW_NUMBER() OVER (ORDER BY c.season, c.class_name, c.circuit_name, c.rider_name),
    c.season,
    c.class_name,
    CASE WHEN c.class_name IN ('MotoGP', '500cc') THEN 1 ELSE 0 END,
    c.circuit_name,
    r.rider_id,
    k.constructor_id,
    c.rider_country_code
FROM cleaned AS c
JOIN refined.riders       AS r ON r.rider_name       = c.rider_name
JOIN refined.constructors AS k ON k.constructor_name = c.constructor_name;
