-- Campeões mundiais de construtores por temporada e categoria.

DROP TABLE IF EXISTS refined.constructor_championships;

CREATE TABLE refined.constructor_championships (
    season           INTEGER NOT NULL,
    class_name       TEXT    NOT NULL,
    is_premier_class INTEGER NOT NULL,
    constructor_id   INTEGER NOT NULL REFERENCES constructors (constructor_id)
);

INSERT INTO refined.constructor_championships (season, class_name, is_premier_class, constructor_id)
SELECT
    CAST(TRIM(w."Season") AS INTEGER),
    TRIM(REPLACE(w."Class", '™', '')),
    CASE WHEN TRIM(REPLACE(w."Class", '™', '')) IN ('MotoGP', '500cc') THEN 1 ELSE 0 END,
    k.constructor_id
FROM raw.constructure_world_championship AS w
JOIN refined.constructors AS k
  ON k.constructor_name = COALESCE(NULLIF(TRIM(w."Constructor"), ''), 'Desconhecido');
