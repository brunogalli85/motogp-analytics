-- Corridas com pódio 100% de uma mesma nacionalidade.
-- A coluna de origem tem um acento grave no nome ("Riders` Nation").

DROP TABLE IF EXISTS refined.podium_lockouts;

CREATE TABLE refined.podium_lockouts (
    season           INTEGER NOT NULL,
    class_name       TEXT    NOT NULL,
    is_premier_class INTEGER NOT NULL,
    circuit_name     TEXT,
    nation_code      TEXT
);

INSERT INTO refined.podium_lockouts (season, class_name, is_premier_class, circuit_name, nation_code)
SELECT
    CAST(TRIM("Season") AS INTEGER),
    TRIM(REPLACE("Class", '™', '')),
    CASE WHEN TRIM(REPLACE("Class", '™', '')) IN ('MotoGP', '500cc') THEN 1 ELSE 0 END,
    NULLIF(TRIM("Track"), ''),
    NULLIF(UPPER(TRIM("Riders` Nation")), '')
FROM raw.same_nation_podium_lockouts;
