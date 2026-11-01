# 🏍️ MotoGP Analytics

Pipeline de dados do Mundial de Motovelocidade (1949–2022), do Kaggle até um dashboard,
organizado em três camadas com **Python** e **SQL**.

Projeto de final de módulo da pós-graduação em Engenharia de Dados e IA.

## Fonte de dados

- **Dataset:** [Moto GP World Championship (1949-2022)](https://www.kaggle.com/datasets/alrizacelk/moto-gp-world-championship19492022), autor alrizacelk
- **Licença:**  CC0: Public Domain
- **Acesso:** baixado automaticamente pela API do Kaggle (`kagglehub`). Nenhum dado é versionado no repositório.

## Arquitetura

```
 Kaggle API
     │  extract.py
     ▼
 data/landing/*.csv          arquivos exatamente como vieram
     │  raw.py
     ▼
 ┌──────────┐  sql/refined  ┌──────────────┐  sql/marts  ┌────────────┐
 │  raw.db  │ ────────────► │  refined.db  │ ──────────► │  marts.db  │ ──► dashboard (Streamlit)
 └──────────┘       │       └──────────────┘             └────────────┘
  cópia fiel        │        limpo, tipado,               indicadores      somente leitura,
  tudo como texto   │        com chaves                   prontos          sem cálculos
                    ▼
              quality.py: reconciliação raw × refined (para o pipeline se faltar linha)
```

| Camada | O que contém | Regra |
|---|---|---|
| **raw** | Uma tabela por CSV, colunas e valores originais, tudo como texto | Nada é alterado |
| **refined** | Dimensões e fato com tipos corretos e chaves para JOIN | Lê só da raw |
| **marts** | Indicadores agregados, prontos para consumo | Lê só da refined |
| **dashboard** | Gráficos e tabelas | Lê só dos marts, em modo somente leitura, sem cálculos |

Cada camada é um arquivo SQLite separado. Testes automáticos garantem que nenhuma consulta
altera a raw, que os marts não leem direto da raw e que o dashboard não enxerga outras camadas.

## Modelo da camada refined

A tabela fato `race_wins` (uma linha por vitória) se liga por chave às dimensões `riders`
e `constructors`. Limpezas, decisões e tratamento de dados ruins em
[`sql/refined/README.md`](sql/refined/README.md). Indicadores em [`sql/marts/README.md`](sql/marts/README.md).

## Estrutura

```
motogp-analytics/
├── src/motogp/
│   ├── config.py           # configurações lidas do .env
│   ├── logging_config.py   # logging padronizado
│   ├── db.py               # conexão com as 3 camadas
│   ├── extract.py          # download via API do Kaggle
│   ├── raw.py              # camada raw (cópia fiel)
│   ├── transform.py        # executa o SQL de refined e marts
│   ├── quality.py          # verificações de qualidade entre camadas
│   ├── pipeline.py         # ponto de entrada (CLI)
│   ├── profile.py          # inspeção de qualquer camada
│   ├── query.py            # consultas SQL somente leitura
│   └── dashboard_data.py   # leitura dos marts para o dashboard
├── sql/
│   ├── refined/            # transformações
│   ├── marts/              # indicadores
│   ├── diagnostico/        # verificações da qualidade da fonte
│   └── analises/           # consultas de resultados
├── dashboard/app.py        # dashboard Streamlit
├── tests/                  # pytest com dados inventados
├── .env.example
├── pyproject.toml
└── uv.lock
```

## Como rodar

Pré-requisito: [uv](https://docs.astral.sh/uv/) instalado.

```bash
# 1. Instalar dependências
uv sync

# 2. Credenciais do Kaggle
cp .env.example .env             # Windows: copy .env.example .env
# edite o .env com o seu token do Kaggle

# 3. Executar o pipeline completo (Kaggle -> raw -> refined -> marts)
uv run python -m motogp.pipeline

# 4. Abrir o dashboard
uv run streamlit run dashboard/app.py
```

Outros comandos:

```bash
uv run python -m motogp.pipeline --skip-download     # reexecuta sem baixar de novo
uv run python -m motogp.profile refined              # inspeciona uma camada
uv run python -m motogp.query sql/analises/resultados_readme.sql   # roda uma consulta
```

## Testes

```bash
uv run pytest
```

Os testes usam bancos em memória ou em pastas temporárias com dados inventados. Eles nunca
abrem o banco do projeto nem acessam a internet (o Kaggle é simulado). Cobrem extração,
camada raw, SQL da refined e dos marts, verificações de qualidade, a ferramenta de consulta
e o acesso do dashboard aos dados.

## Qualidade dos dados

Problemas encontrados na fonte e como foram tratados:

| Problema | Tratamento |
|---|---|
| Categorias com o símbolo ™ (`MotoGP™`) | Removido na refined |
| 28 vitórias com fabricante em branco | Fabricante `Desconhecido`; nenhuma vitória se perde |
| 4 pilotos repetidos em `riders_finishing_positions` | Consolidados em uma linha por piloto |
| `riders_info` com nomes em outro formato e totais divergentes | Mantida só na raw, documentada |
| Temporadas incompletas (abaixo) | Limitação documentada e avisada no dashboard |

### Limitação: temporadas incompletas

Medido com `sql/diagnostico/02_corridas_por_temporada.sql`, comparando com o calendário
oficial da categoria principal:

| Temporada | Corridas no dataset | Corridas reais |
|---|---|---|
| 2004 | 9 | 16 |
| 2014 | 13 | 18 |
| 2017 | 13 | 18 |
| 2022 | 4 | 20 (dataset coletado no início da temporada) |

Também faltam 1 ou 2 corridas em 2015 e 2016. Os indicadores revelaram lacunas mais antigas:
**1960** aparece com 3 corridas (o calendário teve 7) e **1997** com 6 (teve 15).

Por isso, alguns totais ficam abaixo dos oficiais (exemplo: Valentino Rossi aparece com
84 vitórias na categoria principal, contra 89 oficiais). A camada raw não inventa dados:
a limitação é registrada, não escondida.

## Perguntas de negócio

1. Quais fabricantes dominaram cada década na categoria principal?
2. O fabricante campeão venceu quantas % das corridas da temporada?
3. Quem são os maiores vencedores da categoria principal?
4. Quais países mais venceram em cada década?
5. Quais países fecharam pódios inteiros só com seus pilotos, e quando?

## Resultados

**Visão geral:** 3.083 vitórias de 1949 a 2022 em todas as categorias, 871 na categoria
principal, conquistadas por 388 pilotos, 88 fabricantes e 28 países.

### 1. Fabricantes: três eras de domínio

| Década | Líder | Vitórias | % da década |
|---|---|---|---|
| 1940 | AJS | 3 | 50,0% |
| 1950 | Gilera | 28 | 42,4% |
| 1960 | MV Agusta | 45 | 54,2% |
| 1970 | MV Agusta | 45 | 42,5% |
| 1980 | Yamaha | 51 | 41,5% |
| 1990 | Honda | 66 | 53,2% |
| 2000 | Honda | 69 | 43,1% |
| 2010 | Honda | 94 | 56,3% |
| 2020* | Yamaha | 13 | 36,1% |

A categoria principal passou por três eras: as fábricas **europeias** até os anos 1970
(Gilera e MV Agusta), a transição para **Yamaha** nos anos 1980 e o domínio da **Honda** por
três décadas seguidas, com o pico nos anos 2010 (56,3% das vitórias).
\*A década de 2020 tem só 2020, 2021 e o início de 2022, e não permite conclusão.

### 2. Domínio do campeão de construtores

Temporadas em que o campeão venceu mais corridas: **MV Agusta** venceu 100% em 1959 (7 de 7)
e 1968 (10 de 10), e a **Honda** chegou a 93,8% em 2003 (15 de 16) e 92,3% em 1998 e 2014.
Os 100% de 1960 e 1997 aparecem com poucas corridas por causa das lacunas da fonte; o domínio
existiu (a Honda venceu todas as 15 corridas de 1997), mas o número no dataset é incompleto.

### 3. Maiores vencedores da categoria principal

| # | Piloto | País | Vitórias | Período |
|---|---|---|---|---|
| 1 | Valentino Rossi | IT | 84 | 2000–2017 |
| 2 | Giacomo Agostini | IT | 67 | 1966–1976 |
| 3 | Marc Márquez | ES | 56 | 2013–2021 |
| 4 | Jorge Lorenzo | ES | 44 | 2008–2018 |
| 5 | Mick Doohan | AU | 42 | 1990–1998 |

Rossi lidera e tem o período vencedor mais longo do top 5: 18 temporadas, de 2000 a 2017.
Os valores ficam abaixo dos oficiais por causa das temporadas incompletas (ver Limitação).

### 4. Países: do Reino Unido à Espanha

| Década | País líder | % das vitórias (todas as categorias) |
|---|---|---|
| 1940–1960 | Reino Unido | de 55,6% a 36,8% |
| 1970 | Itália | 32,1% |
| 1980 | Espanha | 22,7% |
| 1990–2000 | Itália | 35,0% e 35,7% |
| 2010–2020 | Espanha | 54,2% e 34,7% |

O Reino Unido dominou as três primeiras décadas. Itália e Espanha se alternaram depois, e a
Espanha teve o maior domínio de um país em uma década: 54,2% das vitórias nos anos 2010.

### 5. Pódios de uma só nacionalidade

**Itália (92)**, **Espanha (64)** e **Reino Unido (59)** são os países que mais fecharam
pódios inteiros, seguidos por Estados Unidos (24) e Japão (17). Os três primeiros são
também os que lideraram as vitórias por década.

## Autor

Bruno Galli
