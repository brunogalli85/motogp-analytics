# Spec 03: Camada marts

| Item | Valor |
|---|---|
| Camada | marts (indicadores) |
| Arquivo físico | `data/warehouse/marts.db` |
| Código | `sql/marts/01_*.sql` a `06_*.sql`, executados por `src/motogp/transform.py` |
| Testes | `tests/test_marts.py`, `tests/test_regras_camadas.py` |
| Lê de | **somente** `refined.*` |
| É lida por | dashboard (`dashboard/app.py` via `src/motogp/dashboard_data.py`) |

## 1. Objetivo

Entregar indicadores **prontos para consumo**, respondendo às perguntas de negócio do projeto.
Todo cálculo (somas, percentuais, rankings) acontece aqui, para que o dashboard só exiba.

## 2. Convenções

| Convenção | Regra |
|---|---|
| Categoria principal | `is_premier_class = 1` (500cc e MotoGP) |
| Década | `(season / 10) * 10` → 1998 vira 1990 |
| Percentuais | `ROUND(..., 1)`, em pontos percentuais (54.2 = 54,2%) |
| Rankings | `RANK` ou `DENSE_RANK`; empates dividem a posição |
| `Desconhecido` | Entra nos totais (para o percentual ser fiel), mas não aparece nos rankings |
| Reexecução | Cada arquivo começa com `DROP TABLE IF EXISTS` |

## 3. Tabelas e perguntas de negócio

### 3.1 `constructor_wins_by_decade`, arquivo 01
**Pergunta:** quais fabricantes dominaram cada década na categoria principal?

| Coluna | Descrição |
|---|---|
| `decade` | Década |
| `constructor_name` | Fabricante |
| `wins` | Vitórias do fabricante na década |
| `decade_total_wins` | Total de vitórias da década (inclui `Desconhecido`) |
| `share_pct` | `wins / decade_total_wins` em % |
| `rank_in_decade` | Posição na década |

Técnicas: JOIN, CTE, `SUM() OVER (PARTITION BY)`, `RANK() OVER`.

### 3.2 `champion_dominance`, arquivo 02
**Pergunta:** o fabricante campeão do mundo venceu quantas % das corridas da temporada?

| Coluna | Descrição |
|---|---|
| `season` | Temporada |
| `champion_constructor` | Campeão de construtores |
| `champion_wins` | Vitórias do campeão (0 se não venceu) |
| `season_races` | Corridas da categoria principal no dataset |
| `champion_win_pct` | `champion_wins / season_races` em % |

Técnicas: CTEs, JOIN, `LEFT JOIN`, `COALESCE`.

### 3.3 `top_riders_premier`, arquivo 03
**Pergunta:** quem são os maiores vencedores da categoria principal?

| Coluna | Descrição |
|---|---|
| `rank_position` | Posição (`DENSE_RANK`) |
| `rider_name`, `country_code` | Piloto e país |
| `wins` | Vitórias na categoria principal |
| `winning_seasons` | Temporadas diferentes com vitória |
| `first_win_season`, `last_win_season` | Primeira e última vitória |

### 3.4 `wins_by_country_decade`, arquivo 04
**Pergunta:** quais países mais venceram em cada década (todas as categorias)?

| Coluna | Descrição |
|---|---|
| `decade`, `country_code` | Década e país (`N/D` se vazio) |
| `wins` | Vitórias em todas as categorias |
| `premier_class_wins` | Das quais na categoria principal |
| `share_pct` | % das vitórias da década |
| `rank_in_decade` | Posição na década |

### 3.5 `podium_lockouts_by_nation`, arquivo 05
**Pergunta:** quais países fecharam pódios inteiros só com seus pilotos, e quando?

Colunas: `decade`, `nation_code`, `lockouts`, `premier_class_lockouts`.

### 3.6 `kpi_summary`, arquivo 06
**Uso:** cartões do dashboard. Uma única linha com `first_season`, `last_season`,
`total_race_wins`, `premier_class_wins`, `distinct_winning_riders`,
`distinct_winning_constructors` e `distinct_winning_countries` (sem `Desconhecido`).

## 4. Regras de consumo (dashboard)

| Regra | Como é garantida |
|---|---|
| Dashboard lê **só** os marts | Conexão abre apenas `marts.db`, sem anexar outras camadas (teste) |
| Dashboard não altera dados | Conexão em modo somente leitura `?mode=ro` (teste) |
| Só tabelas previstas | Lista `MARTS_TABLES`; outro nome gera erro (teste) |
| Nenhum cálculo na tela | Tela apenas filtra linhas (década, top N) e desenha; código não cita `raw.` nem `refined.` (teste) |

## 5. Limitações herdadas da fonte

Temporadas incompletas no dataset (ex.: 1960 com 3 de 7 corridas, 1997 com 6 de 15,
2004 com 9 de 16, 2022 com 4 de 20) afetam os indicadores:

- totais por piloto ficam abaixo dos oficiais (Rossi: 84 no dataset, 89 oficiais);
- `champion_win_pct` de temporadas incompletas usa poucas corridas como base;
- a década de 2020 tem só 2020, 2021 e o início de 2022.

A limitação é documentada no README e avisada no topo do dashboard.

## 6. Critérios de aceite

- [x] Nenhum arquivo de `sql/marts` lê da raw ou altera a raw (testes de regras)
- [x] Cada indicador testado com uma raw inventada pequena, de resultado conferível de cabeça
- [x] `Desconhecido` fora dos rankings, mas dentro dos totais
- [x] Categorias menores fora dos indicadores da categoria principal
- [x] Marts podem rodar de novo sem duplicar linhas
