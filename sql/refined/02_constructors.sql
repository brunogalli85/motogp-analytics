-- Dimensão de fabricantes: todos os que venceram corridas ou campeonatos.
-- Fabricante em branco na origem vira 'Desconhecido' ("membro desconhecido"),
-- para nenhuma vitória ou campeonato se perder no JOIN.

DROP TABLE IF EXISTS refined.constructors;

CREATE TABLE refined.constructors (
    constructor_id   INTEGER PRIMARY KEY,
    constructor_name TEXT NOT NULL UNIQUE
);

WITH all_names AS (
    SELECT COALESCE(NULLIF(TRIM("Constructor"), ''), 'Desconhecido') AS constructor_name
    FROM raw.grand_prix_race_winners
    UNION
    SELECT COALESCE(NULLIF(TRIM("Constructor"), ''), 'Desconhecido')
    FROM raw.constructure_world_championship
)
INSERT INTO refined.constructors (constructor_id, constructor_name)
SELECT
    ROW_NUMBER() OVER (ORDER BY constructor_name),
    constructor_name
FROM all_names;
