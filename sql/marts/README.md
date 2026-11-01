# Camada marts

Lê **somente** de `refined.*` e cria tabelas `marts.*` com os indicadores prontos.
É a única camada que o dashboard pode ler: nenhum cálculo é feito na tela.

"Categoria principal" = 500cc (até 2001) e MotoGP (a partir de 2002).

| Arquivo | Tabela | Pergunta de negócio | Técnicas SQL |
|---|---|---|---|
| 01 | `constructor_wins_by_decade` | Quais fabricantes dominaram cada década na categoria principal? | JOIN, CTE, `SUM() OVER`, `RANK() OVER` |
| 02 | `champion_dominance` | O fabricante campeão venceu quantas % das corridas da temporada? | CTEs, JOIN, `LEFT JOIN` |
| 03 | `top_riders_premier` | Quem são os maiores vencedores da categoria principal? | JOIN, `DENSE_RANK() OVER`, `COUNT(DISTINCT)` |
| 04 | `wins_by_country_decade` | Quais países mais venceram em cada década? | CTE, `SUM() OVER`, `RANK() OVER` |
| 05 | `podium_lockouts_by_nation` | Quais países fecharam pódios inteiros, e quando? | Agregação por década |
| 06 | `kpi_summary` | Números gerais do campeonato (cartões do dashboard) | JOINs, agregação condicional |

## Regras de cálculo

- **Década** = `(season / 10) * 10` (1998 → 1990).
- **Percentuais** com uma casa decimal, calculados aqui, nunca no dashboard.
- **`Desconhecido`** (fabricante em branco na origem) entra no total de vitórias da
  década, para o percentual ser fiel, mas não aparece nos rankings.
- **Empates** dividem a posição (`RANK` / `DENSE_RANK`).
