# Camada refined

Lê **somente** de `raw.*` e cria tabelas `refined.*`: tipos corretos, nomes padronizados,
valores limpos, chaves primárias e estrangeiras.

Os arquivos rodam em ordem alfabética. Modelo de arquivo (`01_riders.sql`):

```sql
DROP TABLE IF EXISTS refined.riders;

CREATE TABLE refined.riders AS
SELECT
    CAST(TRIM("Rider Id") AS INTEGER) AS rider_id,
    TRIM("Rider Name")                AS rider_name,
    NULLIF(TRIM("Country"), '')       AS country
FROM raw.riders_info;
```

> Os nomes de tabelas e colunas acima são apenas exemplo. Os reais saem do
> `python -m motogp.profile`.
