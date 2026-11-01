# 🏍️ MotoGP Analytics

Pipeline de dados do Mundial de Motovelocidade (1949–2022), do Kaggle até indicadores prontos,
organizado em três camadas com **Python** e **SQL**.

Projeto de final de módulo da pós-graduação em Engenharia de Dados e IA.

## Fonte de dados

- **Dataset:** [Moto GP World Championship (1949-2022)](https://www.kaggle.com/datasets/alrizacelk/moto-gp-world-championship19492022), autor alrizacelk
- **Licença:** CC0: Public Domain
- **Acesso:** baixado automaticamente pela API do Kaggle (`kagglehub`). Nenhum dado é versionado no repositório.

## Arquitetura

```
 Kaggle API
     │  extract.py
     ▼
 data/landing/*.csv          arquivos exatamente como vieram
     │  raw.py
     ▼
 ┌──────────┐   sql/refined   ┌──────────────┐   sql/marts   ┌────────────┐
 │  raw.db  │ ──────────────► │  refined.db  │ ────────────► │  marts.db  │ ──► dashboard
 └──────────┘                 └──────────────┘               └────────────┘
  cópia fiel                   limpo, tipado,                 indicadores
  tudo como texto              com chaves                     prontos
```

| Camada | O que contém | Regra |
|---|---|---|
| **raw** | Uma tabela por CSV, colunas e valores originais, tudo como texto | Nada é alterado |
| **refined** | Tabelas limpas, com tipos corretos e chaves para JOIN | Lê só da raw |
| **marts** | Indicadores agregados, prontos para consumo | Lê só da refined |

Cada camada é um arquivo SQLite separado, anexado com o nome da camada. As consultas escrevem
`raw.tabela`, `refined.tabela` e `marts.tabela`. Testes automáticos verificam que nenhuma
consulta altera a raw e que os marts não leem direto da raw.

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
│   ├── profile.py          # inspeção de qualquer camada
│   └── pipeline.py         # ponto de entrada (CLI)
├── sql/
│   ├── refined/            # transformações (01_*.sql, 02_*.sql, ...)
│   └── marts/              # indicadores
├── tests/                  # pytest com dados inventados, sem abrir o banco do projeto
├── .env.example
├── pyproject.toml          # dependências e configuração (uv)
└── uv.lock                 # versões exatas instaladas
```

## Como rodar

Pré-requisito: [uv](https://docs.astral.sh/uv/) instalado.

```bash
# 1. Instalar Python, dependências e o próprio projeto (cria o .venv sozinho)
uv sync

# 2. Credenciais do Kaggle
cp .env.example .env             # Windows: copy .env.example .env
# edite o .env com seu usuário e chave do Kaggle

# 3. Executar o pipeline completo
uv run python -m motogp.pipeline

# Reexecutar sem baixar de novo
uv run python -m motogp.pipeline --skip-download

# Inspecionar uma camada (tabelas, colunas e amostras)
uv run python -m motogp.profile            # raw
uv run python -m motogp.profile refined
uv run python -m motogp.profile marts
```

## Testes

```bash
uv run pytest
uv run ruff check .
```

Os testes usam um warehouse em memória e CSVs inventados. Eles nunca abrem `data/warehouse`
nem acessam a internet (o Kaggle é simulado).

## Modelo da camada refined

A tabela fato `race_wins` (uma linha por vitória) se liga às dimensões `riders` e
`constructors` por chave. Detalhes, limpezas e decisões em [`sql/refined/README.md`](sql/refined/README.md).

## Perguntas de negócio

_A definir depois da modelagem da camada refined._

## Resultados

_A preencher com os principais indicadores e conclusões._

## Autor

Bruno Galli
