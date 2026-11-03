# Spec 01: Camada raw

| Item | Valor |
|---|---|
| Camada | raw (dado bruto) |
| Arquivo físico | `data/warehouse/raw.db` |
| Código | `src/motogp/extract.py`, `src/motogp/raw.py` |
| Testes | `tests/test_extract.py`, `tests/test_raw.py`, `tests/test_db.py` |
| Lê de | API do Kaggle, dataset `alrizacelk/moto-gp-world-championship19492022` |
| É lida por | camada refined |

## 1. Objetivo

Guardar uma cópia **fiel** dos arquivos da fonte, para que toda transformação possa ser
refeita e auditada a partir do dado original. Nada é limpo, convertido ou removido aqui.

## 2. Extração

1. Baixar o dataset pela API do Kaggle com `kagglehub.dataset_download`.
2. Autenticar com o token do Kaggle lido do `.env` (`KAGGLE_API_TOKEN`). O token nunca fica no código.
3. Copiar todos os `.csv` (inclusive de subpastas) para `data/landing/`.
4. Falhas de rede, autenticação ou dataset inexistente geram `ExtractError` com mensagem clara,
   e o pipeline termina com código de saída 1.
5. A opção `--skip-download` reaproveita os CSVs já presentes em `data/landing/`.

## 3. Regras da camada

| Regra | Como é garantida |
|---|---|
| Uma tabela por arquivo CSV | `load_raw` percorre todos os CSVs |
| Nome da tabela = nome do arquivo em snake_case (`Riders Info.csv` → `riders_info`) | `table_name_for` |
| Nomes de colunas **iguais aos do arquivo**, inclusive espaços e símbolos | Identificadores entre aspas |
| **Todos os valores gravados como texto**, exatamente como estão no CSV | Colunas `TEXT`, leitura com o módulo `csv` |
| Vazio continua vazio, `"N/A"` continua `"N/A"`, `"007"` continua `"007"`, espaços sobrando continuam | Nenhuma transformação de valor |
| Arquivo em UTF-8 ou latin-1 | Tenta UTF-8 e, se falhar, latin-1 (com aviso no log) |
| Rodar de novo não duplica dados | `DROP TABLE` + `CREATE TABLE` a cada carga |
| Carga atômica por tabela | Transação: grava tudo ou nada |
| Nenhuma outra camada escreve na raw | Teste `test_nenhuma_consulta_altera_a_raw` lê todos os `.sql` |

## 4. Tabelas geradas

| Tabela | Linhas | Colunas (como na fonte) |
|---|---|---|
| `grand_prix_race_winners` | 3083 | Circuit, Class, Constructor, Country, Rider, Season |
| `constructure_world_championship` | 284 | Season, Constructor, Class |
| `riders_finishing_positions` | 394 | Rider, Victories, NumberofSecond, NumberofThird, Numberof4th, Numberof5th, Numberof6th, Country |
| `riders_info` | 368 | Riders All Time in All Classes, Victories, 2nd places, 3rd places, Pole positions from '74 to 2022, Race fastest lap to 2022, World Championships |
| `grand_prix_events_held` | 72 | Times, Track, Country |
| `same_nation_podium_lockouts` | 264 | Season, Track, Riders\` Nation, Class |

## 5. Problemas conhecidos da fonte (mantidos sem alteração)

A raw preserva estes problemas de propósito. Eles são tratados na refined:

- categorias com o símbolo ™ (`MotoGP™`);
- 28 vitórias com o fabricante em branco;
- 4 pilotos repetidos em `riders_finishing_positions`;
- coluna com acento grave no nome (`Riders` Nation`);
- `riders_info` com nomes em outro formato (`AGOSTINI Giacomo`) e números como `"35.0"`;
- temporadas incompletas (ex.: 2004 com 9 de 16 corridas; 2022 com 4 de 20).

## 6. Critérios de aceite

- [x] Cada CSV da fonte vira uma tabela em `raw.db`
- [x] Nomes de colunas e valores idênticos ao arquivo, todos como texto
- [x] Duas execuções seguidas resultam no mesmo número de linhas
- [x] Testes rodam com CSVs inventados, sem internet (Kaggle simulado) e sem abrir o banco do projeto
