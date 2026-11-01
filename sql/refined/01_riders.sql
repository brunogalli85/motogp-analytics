-- Dimensão de pilotos.
-- Junta os nomes das duas tabelas que usam o formato "Nome Sobrenome"
-- e fica com uma linha por piloto. O país é o da vitória mais recente.
--
-- Vitórias com o piloto em branco na origem recebem o piloto 'Desconhecido'
-- (técnica de "membro desconhecido"): assim nenhuma vitória se perde no JOIN.

DROP TABLE IF EXISTS refined.riders;

CREATE TABLE refined.riders (
    rider_id     INTEGER PRIMARY KEY,
    rider_name   TEXT NOT NULL UNIQUE,
    country_code TEXT
);

WITH all_names AS (
    SELECT
        COALESCE(NULLIF(TRIM("Rider"), ''), 'Desconhecido') AS rider_name,
        NULLIF(UPPER(TRIM("Country")), '')                   AS country_code,
        CAST(TRIM("Season") AS INTEGER)                      AS season
    FROM raw.grand_prix_race_winners

    UNION ALL

    SELECT
        TRIM("Rider"),
        NULLIF(UPPER(TRIM("Country")), ''),
        NULL
    FROM raw.riders_finishing_positions
    WHERE TRIM("Rider") <> ''
),
ranked AS (
    SELECT
        rider_name,
        country_code,
        ROW_NUMBER() OVER (
            PARTITION BY rider_name
            ORDER BY season IS NULL, season DESC
        ) AS rn
    FROM all_names
)
INSERT INTO refined.riders (rider_id, rider_name, country_code)
SELECT
    ROW_NUMBER() OVER (ORDER BY rider_name),
    rider_name,
    CASE WHEN rider_name = 'Desconhecido' THEN NULL ELSE country_code END
FROM ranked
WHERE rn = 1;
