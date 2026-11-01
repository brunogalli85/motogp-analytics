# Camada refined

Lê **somente** de `raw.*` e cria tabelas `refined.*` com tipos corretos, nomes padronizados,
valores limpos e chaves. Os arquivos rodam em ordem alfabética.

## Modelo

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

| Arquivo | Tabela | Origem na raw | O que muda |
|---|---|---|---|
| 01 | `riders` | race_winners + finishing_positions | Um registro por piloto, com `rider_id`; país da vitória mais recente |
| 02 | `constructors` | race_winners + constructure_world_championship | Um registro por fabricante, com `constructor_id` |
| 03 | `circuits` | grand_prix_events_held | `Times` vira inteiro (`gp_events_held`) |
| 04 | `race_wins` | grand_prix_race_winners | Ligada a pilotos e fabricantes por chave; categoria sem ™; marca 500cc/MotoGP como categoria principal |
| 05 | `constructor_championships` | constructure_world_championship | Chave de fabricante; categoria limpa |
| 06 | `rider_career_stats` | riders_finishing_positions | Colunas renomeadas (`NumberofSecond` → `second_places`); números inteiros; vazio vira nulo |
| 07 | `podium_lockouts` | same_nation_podium_lockouts | Categoria limpa; coluna `Riders\` Nation` → `nation_code` |

## Limpezas aplicadas em todas as tabelas

- `TRIM` em textos (espaços sobrando criariam pilotos e fabricantes duplicados)
- Remoção do símbolo `™` das categorias (`MotoGP™` → `MotoGP`)
- Códigos de país em maiúsculas
- Texto vazio vira `NULL`
- Anos e contagens convertidos para `INTEGER`

## Decisão: campos em branco viram "Desconhecido"

Na origem, algumas vitórias têm o piloto ou o fabricante em branco. Na primeira versão
da refined, essas linhas sumiam no JOIN: a raw tinha **3083** vitórias e a refined, **3055**.

A correção usa a técnica de **membro desconhecido**: o nome em branco vira o piloto ou
fabricante `Desconhecido`, que existe nas dimensões. Assim:

- nenhuma vitória se perde, e os totais por temporada e categoria continuam corretos;
- os rankings de pilotos e fabricantes não são afetados, porque `Desconhecido` pode ser
  filtrado nos indicadores.

## Verificações de qualidade (`src/motogp/quality.py`)

Rodam automaticamente depois da refined:

| Verificação | Se falhar |
|---|---|
| Reconciliação: cada tabela da refined tem o mesmo número de linhas da sua origem na raw | **Erro**: o pipeline para e os marts não são gerados |
| Vitórias atribuídas a `Desconhecido` | Aviso no log, com a quantidade |
| Nomes repetidos em `riders_finishing_positions` | Aviso no log, com os nomes |

## Decisão: pilotos repetidos na carreira

`riders_finishing_positions` tem 4 pilotos que aparecem duas vezes (Edmund Czihak,
Lukas Tulovic, Nello Pagani e Stefan Prein). Para nada ser contado em dobro,
`rider_career_stats` tem **uma linha por piloto**:

1. linhas idênticas contam uma vez só;
2. linhas diferentes do mesmo piloto são somadas (estatísticas divididas na origem).

Por isso a reconciliação dessa tabela compara com o número de **pilotos distintos** da raw
(390), e não com o número de linhas (394).

## Decisão: `riders_info` fica só na raw

A tabela `raw.riders_info` não foi levada para a refined porque:

1. o nome do piloto está em outro formato (`AGOSTINI Giacomo`), sem chave confiável para ligar às demais;
2. os totais contradizem `riders_finishing_positions`. Exemplo: Valentino Rossi tem
   52 segundos lugares em uma tabela e 67 na outra.

Ela continua na raw, sem alteração, caso uma análise futura resolva a inconsistência.
