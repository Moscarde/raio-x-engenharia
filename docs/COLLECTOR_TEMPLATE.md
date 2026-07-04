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

- Ficam em `tests/collectors/<fonte>/`, sem depender de Airflow. Inclua um
  `__init__.py` vazio nessa pasta — sem ele, dois collectors com arquivos de
  mesmo nome (ex. `test_client.py` no IBGE e no CNES) colidem na coleta do
  pytest (import mode `prepend` exige basenames únicos sem `__init__.py`).
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
- **CNES**: o grupo "ST" (Estabelecimentos) é distribuído por UF inteira, um
  arquivo DBC por competência (`ST{UF}{AAMM}.dbc`, ex. `STRJ2512.dbc`), sem
  recorte por município — o filtro pelo município de referência do MVP
  acontece no parser, não no client. O campo `CODUFMUN` é o código IBGE do
  município truncado em 6 dígitos (sem o dígito verificador; confirmado
  contra amostra real: `CODUFMUN "330455"` para Rio de Janeiro,
  `id_municipio 3304557` em `raw_ibge.municipios`). CNES é cadastro
  (snapshot mensal do que está ativo na competência), não série de eventos:
  uma única competência já retrata o período, sem precisar buscar todos os
  meses do ano. O grupo "ST" não tem campos de nome/razão social do
  estabelecimento — só códigos (tipo de unidade, natureza jurídica etc.); o
  de-para para valores legíveis fica para staging/dbt, não para o raw layer.
  Ver `include/collectors/cnes/parser.py`.
- **SIA**: o grupo "PA" (Produção Ambulatorial) distribui uma competência de
  UF grande (ex. RJ) em múltiplos arquivos DBC (`PA{UF}{AAMM}a.dbc`,
  `...b.dbc`, `...c.dbc`...) quando o volume excede o limite de um único
  arquivo — confirmado contra amostra real (dez/2025 do RJ: 2 partes,
  174MB+143MB). O catálogo público do `pysus` (usado via `pysus.sia()`)
  indexa só 1 parte por competência quando há múltiplas, descartando as
  demais **silenciosamente** — dado incompleto sem nenhum erro. Por isso
  `include/collectors/sia/client.py` não usa `pysus.sia()`: fala direto com
  o FTP do DATASUS (`ftplib`, biblioteca padrão) para listar e baixar todas
  as partes, e reaproveita só os decodificadores internos do pysus
  (`pyreaddbc.dbc2dbf` + `pysus.data.dbf_reader.read_dbf_fast` — este último
  é ~3x mais rápido que `dbfread` puro-Python quando restrito às colunas
  necessárias; medido: ~150s/milhão de linhas vs. ~450s/milhão). O campo
  `PA_UFMUN` é o mesmo código IBGE de 6 dígitos truncado do CNES.
  Adicionalmente, uma competência de arquivo pode conter linhas cujo
  `PA_CMP` (competência real do atendimento) é **anterior** ao mês do
  arquivo — produção processada com atraso (confirmado: o arquivo de
  dez/2025 trouxe linhas com competência 202509/202510/202511 além de
  202512). Por isso a partição de `delete + insert`
  (`include/collectors/sia/repository.py`,
  `substituir_producao_ambulatorial`) usa a competência real de cada linha,
  não o mês do arquivo buscado — senão uma recarga de um mês posterior não
  apagaria a versão antiga de linhas retroativas, arriscando duplicata.
