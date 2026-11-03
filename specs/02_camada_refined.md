# Spec 02: Camada refined

| Item | Valor |
|---|---|
| Camada | refined (dado transformado) |
| Arquivo físico | `data/warehouse/refined.db` |
| Código | `sql/refined/01_*.sql` a `07_*.sql`, executados por `src/motogp/transform.py` |
| Qualidade | `src/motogp/quality.py` |
| Testes | `tests/test_refined.py`, `tests/test_quality.py`, `tests/test_transform.py` |
| Lê de | **somente** `raw.*` |
| É lida por | camada marts |

## 1. Objetivo

Transformar o dado bruto em tabelas **limpas, tipadas e ligadas por chaves**, num modelo
dimensional com uma tabela fato de vitórias e dimensões de pilotos e fabricantes.

## 2. Modelo

```
        riders ─────────┐                 ┌───────── constructors
     (rider_id)         │                 │        (constructor_id)
          │             ▼                 ▼               │
          │        ┌─────────────────────────┐            │
          │        │        race_wins        │            │
          │        │  1 linha por vitória    │            │
          │        └─────────────────────────┘            │
          ▼                                               ▼
 rider_career_stats                          constructor_championships

 circuits · podium_lockouts  (tabelas de apoio)
```

## 3. Tabelas

### 3.1 `riders` (dimensão), arquivo 01

| Coluna | Tipo | Regra |
|---|---|---|
| `rider_id` | INTEGER PK | Sequencial por nome |
| `rider_name` | TEXT, NOT NULL, UNIQUE | `TRIM`; vazio vira `Desconhecido` |
| `country_code` | TEXT | País da vitória mais recente, em maiúsculas; nulo para `Desconhecido` |

Origem: nomes de `grand_prix_race_winners` + `riders_finishing_positions`.

### 3.2 `constructors` (dimensão), arquivo 02

| Coluna | Tipo | Regra |
|---|---|---|
| `constructor_id` | INTEGER PK | Sequencial por nome |
| `constructor_name` | TEXT, NOT NULL, UNIQUE | `TRIM`; vazio vira `Desconhecido` |

Origem: `grand_prix_race_winners` + `constructure_world_championship`.

### 3.3 `circuits` (apoio), arquivo 03

| Coluna | Tipo | Regra |
|---|---|---|
| `circuit_id` | INTEGER PK | Sequencial por nome |
| `circuit_name` | TEXT | `TRIM` |
| `country_code` | TEXT | Maiúsculas; vazio vira nulo |
| `gp_events_held` | INTEGER | `Times` convertido |

### 3.4 `race_wins` (fato), arquivo 04

| Coluna | Tipo | Regra |
|---|---|---|
| `race_win_id` | INTEGER PK | Sequencial |
| `season` | INTEGER | `Season` convertido |
| `class_name` | TEXT | Sem o símbolo ™ |
| `is_premier_class` | INTEGER (0/1) | 1 para `MotoGP` e `500cc` |
| `circuit_name` | TEXT | `TRIM`; vazio vira nulo |
| `rider_id` | INTEGER FK → riders | JOIN pelo nome |
| `constructor_id` | INTEGER FK → constructors | JOIN pelo nome |
| `rider_country_code` | TEXT | Nacionalidade registrada na vitória |

### 3.5 `constructor_championships`, arquivo 05

`season` INTEGER, `class_name` TEXT (sem ™), `is_premier_class` INTEGER,
`constructor_id` INTEGER FK → constructors.

### 3.6 `rider_career_stats`, arquivo 06

| Coluna | Tipo | Regra |
|---|---|---|
| `rider_id` | INTEGER PK, FK → riders | **Uma linha por piloto** |
| `victories` … `sixth_places` | INTEGER | Colunas renomeadas (`NumberofSecond` → `second_places`); vazio vira nulo |

Pilotos repetidos na origem: linhas idênticas contam uma vez (`DISTINCT`); linhas diferentes são somadas.

### 3.7 `podium_lockouts`, arquivo 07

`season` INTEGER, `class_name` TEXT (sem ™), `is_premier_class` INTEGER,
`circuit_name` TEXT, `nation_code` TEXT (da coluna `Riders` Nation`).

## 4. Regras gerais de limpeza

| Regra | Motivo |
|---|---|
| `TRIM` em todo texto | Espaços sobrando criariam pilotos e fabricantes duplicados |
| Remover `™` das categorias | Agrupamentos por categoria não bateriam |
| Códigos de país em maiúsculas | `it` e `IT` seriam países diferentes |
| Texto vazio → `NULL` | Vazio não é valor |
| Anos e contagens → `INTEGER` | Permite somar, ordenar e comparar |
| Cada arquivo começa com `DROP TABLE IF EXISTS` | Pode rodar de novo sem erro |

## 5. Decisões de modelagem

| Decisão | Motivo |
|---|---|
| **Membro `Desconhecido`** para piloto ou fabricante em branco | Sem ele, 28 vitórias sumiam no JOIN (raw 3083 × refined 3055) |
| **Consolidar pilotos repetidos** em `rider_career_stats` | Edmund Czihak, Lukas Tulovic, Nello Pagani e Stefan Prein seriam contados em dobro |
| **`riders_info` fica só na raw** | Nome em outro formato, sem chave confiável, e totais que contradizem `riders_finishing_positions` (ex.: Rossi com 52 e 67 segundos lugares) |
| **Categoria principal** = `MotoGP` + `500cc` | Mesma categoria com nomes diferentes ao longo da história |

## 6. Verificações de qualidade (rodam após a refined)

| Verificação | Esperado | Se falhar |
|---|---|---|
| `grand_prix_race_winners` → `race_wins` | mesmo nº de linhas (3083) | **ERRO**: pipeline para, marts não são gerados |
| `constructure_world_championship` → `constructor_championships` | mesmo nº de linhas (284) | **ERRO** |
| `riders_finishing_positions` → `rider_career_stats` | nº de pilotos distintos (390) | **ERRO** |
| `same_nation_podium_lockouts` → `podium_lockouts` | mesmo nº de linhas (264) | **ERRO** |
| Vitórias atribuídas a `Desconhecido` | registrar quantidade | Aviso no log |
| Nomes repetidos na carreira | registrar nomes | Aviso no log |

## 7. Critérios de aceite

- [x] Nenhum arquivo de `sql/refined` lê dos marts ou altera a raw (testes de regras)
- [x] Toda chave estrangeira existe na sua dimensão (teste de integridade)
- [x] Reconciliação raw × refined sem perdas
- [x] Testes com raw inventada usando os nomes de colunas reais, incluindo ™, espaços, vazios e repetidos
