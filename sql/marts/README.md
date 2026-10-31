# Camada marts

Lê **somente** de `refined.*` e cria tabelas `marts.*` com indicadores prontos.
É a única camada que o dashboard pode ler, e nenhum cálculo é feito na tela.

Modelo de arquivo (`01_vitorias_por_construtor.sql`):

```sql
DROP TABLE IF EXISTS marts.vitorias_por_construtor;

CREATE TABLE marts.vitorias_por_construtor AS
SELECT
    c.constructor_name,
    COUNT(*) AS vitorias
FROM refined.results  AS r
JOIN refined.constructors AS c USING (constructor_id)
WHERE r.position = 1
GROUP BY c.constructor_name;
```

> Nomes apenas de exemplo, a definir depois de conhecer os dados.
