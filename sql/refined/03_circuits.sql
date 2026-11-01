-- Dimensão de circuitos, com quantos GPs cada um já recebeu.

DROP TABLE IF EXISTS refined.circuits;

CREATE TABLE refined.circuits (
    circuit_id     INTEGER PRIMARY KEY,
    circuit_name   TEXT NOT NULL,
    country_code   TEXT,
    gp_events_held INTEGER
);

INSERT INTO refined.circuits (circuit_id, circuit_name, country_code, gp_events_held)
SELECT
    ROW_NUMBER() OVER (ORDER BY TRIM("Track")),
    TRIM("Track"),
    NULLIF(UPPER(TRIM("Country")), ''),
    CAST(TRIM("Times") AS INTEGER)
FROM raw.grand_prix_events_held
WHERE TRIM("Track") <> '';
