# Template de collector

Checklist para implementar uma nova fonte, replicando o padrão de
`include/collectors/ibge/` (implementação de referência). Ver rotas
candidatas por fonte em [docs/fontes.md](fontes.md).

## Estrutura de arquivos

Cada fonte é um submódulo em `include/collectors/<fonte>/`, com um arquivo por
responsabilidade:

| Arquivo | Responsabilidade | Referência IBGE |
| --- | --- | --- |
| `client.py` | Busca dado bruto na fonte (API/FTP/download), sem parsing. | `include/collectors/ibge/client.py` — `fetch_municipios()` |
| `parser.py` | Normaliza registro bruto para as colunas da tabela raw; valida campos obrigatórios e levanta `ValueError` claro quando faltarem. | `include/collectors/ibge/parser.py` — `parse_municipio()` / `parse_municipios()` |
| `db.py` | Conexão com Postgres a partir de variáveis de ambiente (`POSTGRES_*`). | `include/collectors/ibge/db.py` — `get_connection()` |
| `repository.py` | DDL do schema/tabela raw (`CREATE SCHEMA/TABLE IF NOT EXISTS`) e upsert em lote pela chave natural. | `include/collectors/ibge/repository.py` — `ensure_schema()` / `upsert_municipios()` |
| `run_<entidade>.py` | Entrypoint manual (`python -m include.collectors.<fonte>.run_<entidade>`), roda fora do Airflow. | `include/collectors/ibge/run_municipios.py` |

Nenhum desses arquivos importa Airflow. A DAG (quando existir) só chama a
função pública de `run_<entidade>.py`.

## Testes

- Ficam em `tests/collectors/<fonte>/`, sem depender de Airflow.
- Cobrem: parsing de dados brutos, montagem de registros normalizados,
  validação de campos obrigatórios, e o client (mockando I/O externo com
  classes fake nomeadas, ex. `FakeRespostaIBGE` em
  `tests/collectors/ibge/test_client.py`).
- Rodam com `pytest` puro — sem Airflow instalado no `.venv`. Isso funciona
  porque `pytest.ini` define `testpaths = tests/collectors` e
  `pythonpath = .`. `astro dev pytest` continua cobrindo `tests/` inteiro
  (inclusive `tests/dags/`) porque passa esse caminho explicitamente,
  ignorando `testpaths`.

## Dependências

- `requirements.txt`: dependências de execução do collector (ex. `requests`,
  `psycopg[binary]`, `python-dotenv`). Usadas tanto na imagem Astro/Airflow
  quanto no `.venv` local — não adicionar aqui nada que só sirva para
  desenvolvimento local.
- `requirements-dev.txt`: só ferramentas de dev/teste (`pytest`, `ruff`,
  `black`). Nunca entram na imagem Airflow.

## Escopo de volume

Fontes de grande volume (CNES, SIA, SIH, SISAB, SIM, SINASC) devem, na
primeira implementação, restringir a coleta a um município de referência
(Rio de Janeiro, id_municipio 3304557) e ao ano de 2025. Ver detalhes em
[docs/fontes.md](fontes.md#escopo-de-volume-para-o-mvp).

## Limitações conhecidas da fonte

Quirks reais de dados descobertos ao testar contra a fonte de verdade (não
bugs do collector) devem ser documentados com comentário no ponto do código
onde são tratados, e resumidos aqui:

- **IBGE**: 1 município (id 5101837, Boa Esperança do Norte/MT, criado em
  2024) não tem `microrregiao`/`mesorregiao` cadastradas na API. O parser
  resolve UF/regiao via `regiao-imediata.regiao-intermediaria.UF` nesse caso
  e grava `id_microrregiao`/`nome_microrregiao`/`id_mesorregiao`/
  `nome_mesorregiao` como `NULL`. Ver
  `include/collectors/ibge/parser.py` (`_resolve_territorio`).
