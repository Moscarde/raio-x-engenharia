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
- **SIH**: `pysus.sih(state="RJ", year=2025, month=12, group="RD")` retorna
  lista vazia mesmo o arquivo existindo no FTP com dados reais (confirmado:
  76169 linhas em `RDRJ2512.dbc` via download direto) — catálogo do pysus
  incompleto para esse grupo, mesma classe de problema do SIA. Por isso
  `include/collectors/sih/client.py` também fala direto com o FTP via
  `ftplib`, como o SIA. Diferente do SIA, o grupo "RD" (AIH Reduzida) tem 1
  arquivo por competência para RJ (sem partes a/b/c — confirmado, mas o
  client aceita sufixo pelo mesmo risco de volume). O campo de filtro por
  município é `MUNIC_MOV` (município do estabelecimento/hospital), não
  `MUNIC_RES` (município de residência do paciente, mantido só como
  dimensão) — confirmado contra amostra real: `MUNIC_MOV "330455"`
  concentra as internações do Rio. Diferente do SIA (produção agregada sem
  identificador único), cada linha do SIH/RD é uma AIH com número próprio
  (`N_AIH`), então a persistência usa upsert por chave natural
  (`include/collectors/sih/repository.py`, `upsert_internacoes`), não
  delete+insert por partição.
- **FNS**: fonte não é DATASUS/DBC — é a API pública de Transferências Fundo
  a Fundo (PostgREST em `https://api.transferegov.gestao.gov.br/fundoafundo/`,
  descoberta a partir da rota candidata em docs/fontes.md). Diferente do
  CNES/SIA/SIH, essa API aceita filtro por CNPJ e data diretamente na
  consulta (`eq.`/`gte.`/`lte.` do PostgREST), então o recorte pelo
  município de referência acontece em `include/collectors/fns/client.py`
  (na query), não no parser — o ano inteiro é buscado em 1 chamada, sem
  precisar iterar por mês. O ente é identificado por CNPJ, não por código
  IBGE (confirmado: CNPJ `42498733000148` = "MUNICIPIO DE RIO DE JANEIRO"
  na API); o de-para CNPJ -> id_municipio fica para staging/dbt. Volume real
  é baixo (23 lançamentos em 2025, confirmado rodando
  `run_repasses.py` de ponta a ponta contra o Postgres local, upsert
  idempotente em 2 execuções) porque a API cobre só os lançamentos do
  "Programa Ágil" (código 140), não o histórico completo de repasses SUS.
- **SIM** e **SINASC**: mesma classe de problema do catálogo do pysus (SIA/
  SIH) — `pysus.sim()` e `pysus.sinasc()` retornam DataFrame vazio para os
  grupos DO/DN mesmo com o arquivo existindo no FTP com dados reais
  (confirmado: 148156 linhas em `DORJ2024.dbc`, 180369 em `DNRJ2022.dbc`).
  Por isso os dois clients também falam direto com o FTP via `ftplib`.
  Diferente de SIA/SIH/CNES (competência mensal), SIM e SINASC são **anuais**:
  1 arquivo por UF/ano, com o ano em 4 dígitos no nome (`DORJ2024.dbc`,
  `DNRJ2022.dbc`), sem mês. Consolidação tem atraso: 2025 não estava
  publicado para nenhum dos dois no momento da implementação — SIM usa o
  último ano disponível (2024), SINASC usa o último ano disponível (2022,
  atraso maior que o SIM). O campo de filtro por município é `CODMUNOCOR`
  no SIM (município de ocorrência do óbito) e `CODMUNNASC` no SINASC
  (município de nascimento) — não `CODMUNRES` (residência do falecido/mãe,
  mantido só como dimensão), mesmo padrão do `MUNIC_MOV` do SIH (confirmado
  contra amostra real: `CODMUNOCOR "330455"` concentra os óbitos do Rio,
  `CODMUNNASC "330455"` concentra os nascimentos). Nenhum dos dois grupos
  tem identificador de registro estável entre arquivos de anos diferentes
  (o campo `CONTADOR` é só um contador sequencial local ao arquivo, único
  dentro de um ano mas sem garantia de unicidade entre anos), e cada
  arquivo anual não mistura registros de outros anos (confirmado: 100% das
  linhas de `DORJ2024.dbc` com `DTOBITO` em 2024, mesmo para
  `DNRJ2022.dbc`/`DTNASC`) — por isso a persistência usa delete+insert por
  partição (ano + município), como o SIA, não upsert por chave natural.
- **SIOPS**: única fonte cuja rota candidata original foi trocada por
  completo. O site legado `siops.datasus.gov.br` (rota original em
  docs/fontes.md) existe e tem formulário real (Ano/UF/Município/Período,
  município identificado pelo mesmo código IBGE de 6 dígitos das fontes
  DATASUS), mas seu relatório de cálculo do % de saúde
  (`carregarDadosLC141.php`) tem bug real confirmado: respostas de
  **300+ MB** de HTML e **valores "0,00"** para o Rio de Janeiro em todos
  os anos testados (2021, 2022, 2023, 2024). Uma segunda rota do mesmo
  site legado (`consvaloresmunicipio.php`, "Consulta por Unidade
  Executora") retorna dado real e bem formado, mas só até 2017 — de 2018
  em diante essa rota só expõe 1 "pasta" nicho ("Despesa com Saúde em
  Consórcio Público"), evidência de que a coleta granular de
  receita/despesa migrou para outro sistema por volta de 2018.
  `include/collectors/siops/client.py` não usa nenhuma dessas duas rotas:
  usa a API do **SICONFI** (Tesouro Nacional,
  `https://apidatalake.tesouro.gov.br/`), o substituto de fato — API REST
  JSON pública, sem autenticação, documentada
  (`apidatalake.tesouro.gov.br/docs/siconfi`), onde os entes hoje
  efetivamente transmitem o RREO. O endpoint `/rreo`, filtrado por
  `no_anexo=RREO-Anexo 14` (Demonstrativo Simplificado), inclui a linha
  `AplicacaoTotalDasDespesasComAcoesEServicosPublicosDeSaude` — o mesmo
  indicador de aplicação mínima da LC 141/2012 que o SIOPS legado deveria
  fornecer, com dado real e sem atraso (confirmado: Rio de Janeiro 2025,
  todos os 6 bimestres populados; bimestre 6 fechado com 16,98% aplicado
  em saúde, mínimo 15%, R$ 3,93 bi apurados). O ente é identificado por
  `cod_ibge`, código IBGE **completo** (7 dígitos) — igual
  `raw_ibge.municipios.id_municipio`, sem truncamento nem de-para
  necessário (diferente de DATASUS/6-dígitos e do CNPJ do FNS). Os valores
  do RREO são cumulativos "até o bimestre" dentro do exercício (não
  incrementais por bimestre), então basta buscar o 6º bimestre
  (fechamento do exercício) para ter o total do ano — diferente de
  SIA/SIH, que exigem somar os 12 meses. Sem identificador de linha
  estável (um bimestre pode ser retificado), a persistência usa
  delete+insert por partição (município + ano + bimestre), como SIA/SIM/
  SINASC.
- **SISAB**: como o SIOPS, a rota candidata original foi trocada por
  completo. O painel `sisab.saude.gov.br` (acesso restrito) e o FTP
  candidato `CMD/DadosSISAB` (diretório vazio) não tinham download direto
  viável. Implementado contra a **API de Dados Abertos do Ministério da
  Saúde (DEMAS)**, `apidadosabertos.saude.gov.br` — API REST JSON pública,
  sem autenticação, documentada via Swagger em
  `apidadosabertos.saude.gov.br/v1` (spec em `/static/swagger.json`).
  Endpoint `/atencao-primaria/indicador-desempenho-programa-previne-brasil`
  expõe os indicadores de desempenho do Programa Previne Brasil — o mesmo
  cálculo que o SISAB usa para o cofinanciamento federal da Atenção
  Primária — com filtro nativo por `codigo_municipio` (código IBGE de 6
  dígitos, mesmo padrão do CNES/SIA/SIH/SIM/SINASC) e `quadrimestre`
  (ex.: `"2024Q3"`). O Previne Brasil foi extinto pela Portaria GM/MS
  Nº 3.493/2024 e substituído por nova metodologia de financiamento; a
  série de dados para no 3º quadrimestre de 2024 (confirmado:
  2025Q1/Q2/Q3 retornam lista vazia para o Rio de Janeiro), por isso o
  escopo usa o último quadrimestre disponível em vez do "ano 2025" padrão.
  Cada combinação (`codigo_tipo_indicador`, `visao_equipe`) é única dentro
  de um município/quadrimestre (confirmado: 18 linhas = 6 tipos x 3
  visões, sem duplicata), mas sem um ID de linha estável entre execuções
  — por isso a persistência usa delete+insert por partição
  (município + quadrimestre), como SIA/SIM/SINASC/SIOPS.
