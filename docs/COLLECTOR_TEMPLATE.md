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

Exceção: **SIA** carrega o estado (UF) inteiro desde 2026-07-04, não só o
município de referência — o cliente já decodifica o arquivo inteiro antes
de qualquer filtro ser possível, então persistir tudo reaproveita esse
custo de CPU já pago em vez de descartar a maior parte das linhas
decodificadas. Ver ROADMAP.md.

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
  (snapshot mensal do que está ativo na competência) — cada competência
  isolada já retrata o período, mas desde 2026-07-12 o collector carrega os
  12 meses de 2025 (não mais só 1), porque a demanda "Histórico de rede
  CNES" (ver ROADMAP.md) precisa da série ao longo do tempo, não só do
  estado mais recente: `raw_cnes.estabelecimentos` tem chave primária
  composta `(codigo_cnes, competencia)`, então cada mês vira 1 linha nova
  por estabelecimento em vez de sobrescrever a anterior. `dim_estabelecimento`
  (dbt) filtra pela competência mais recente de cada `codigo_cnes` pra
  manter "1 linha por estabelecimento" pra quem já consome a dimensão; a
  série completa fica em `stg_cnes__estabelecimentos`. O grupo "ST" não tem
  campos de nome/razão social do estabelecimento — só códigos (tipo de
  unidade, natureza jurídica etc.); o de-para para valores legíveis fica
  para staging/dbt, não para o raw layer. Ver
  `include/collectors/cnes/parser.py`.
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
  `run_repasses.py` de ponta a ponta contra o PostgreSQL externo configurado,
  upsert
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
- **Portal da Transparência (financiamento municipal completo)**: única
  fonte deste projeto que exige autenticação — chave pessoal
  (`chave-api-dados`), obtida gratuitamente registrando um e-mail em
  `api.portaldatransparencia.gov.br/api-de-dados/cadastrar-email`. A rota
  antiga documentada para "transferências a municípios"
  (`/api-de-dados/transferencias`) responde `403` nesta versão da API —
  descontinuada (confirmado: outros endpoints com a mesma chave respondem
  `200` normalmente, então não é problema de autenticação). O substituto de
  fato é `/api-de-dados/despesas/recursos-recebidos` ("Recebimento de
  recursos por favorecido"), filtrado por `codigoFavorecido` (CNPJ do
  próprio ente municipal, os mesmos 3 CNPJs já usados pelo collector FNS) e
  `orgaoSuperior=36000` (Ministério da Saúde) — **não** pelo parâmetro
  `codigoIBGE`, que filtra pelo município de residência do favorecido, não
  pela entidade que recebeu o recurso (confirmado contra a API real:
  `codigoIBGE=3304557` sozinho retorna lista vazia para o Rio de Janeiro;
  `codigoFavorecido=42498733000148` retorna registros reais). Complementa
  `raw_fns.repasses`, que só cobre o recorte estreito do "Programa Ágil" do
  Fundo a Fundo: esta fonte traz recursos recebidos de qualquer unidade
  vinculada ao Ministério da Saúde (INCA, Fiocruz, hospitais federalizados
  etc.), não só o Fundo a Fundo. `valor` pode ser negativo (estorno/
  devolução de recurso, confirmado contra dado real). Sem identificador de
  linha estável — persistência usa delete+insert por partição (CNPJ do
  favorecido + ano), como SIA/SIM/SINASC/SIOPS/SISAB. Paginação de 15 itens
  por página, sem total exposto pela API — o client pagina até uma página
  vir vazia. `run_recursos_recebidos.py` já rodou de ponta a ponta contra o
  Postgres local (3 municípios, ano 2025: 29 linhas — Rio 16, Paraty 12,
  Nova Iguaçu 1), idempotente em 2 execuções seguidas.
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
- **IBGE / população estimada**: agregado 6579 do SIDRA (API `/v3/agregados`,
  distinta da API `/v1/localidades` usada para o cadastro de municípios),
  variável 9324. Cobre o Brasil inteiro, mas o filtro por município já
  acontece na própria consulta (parâmetro `localidades=N6[...]`, aceita
  vários municípios numa única chamada), diferente das fontes DATASUS que
  exigem filtrar depois de baixar o arquivo inteiro. Só 1 valor por ano
  (referência 1º de julho); chave natural é município + ano, não
  competência mensal. `run_populacao_estimada.py` já rodou de ponta a
  ponta contra o Postgres local (3 municípios, ano 2025: 6.730.729
  habitantes no Rio de Janeiro).
- **CNES / equipes de APS (grupo "EP")**: mesmo arquivo DBC por competência
  do grupo "ST" (`EP{UF}{AAMM}.dbc`, ex. `EPRJ2512.dbc`), buscado também via
  `pysus.cnes(group="EP")`. Cada linha é 1 equipe vinculada a um
  estabelecimento (`IDEQUIPE`, estável entre competências — permite
  acompanhar ativação/desativação da mesma equipe ao longo do tempo,
  diferente do `codigo_cnes` do "ST" que é chave de estabelecimento, não de
  equipe). `TIPO_EQP` cobre todos os tipos de equipe (eSF, eSB/odonto,
  NASF etc.), não só APS — o parser filtra para os tipos que compõem o
  cofinanciamento do Previne Brasil (`70`=eSF, `73`=eCR, `74`=eAPP,
  `76`=eAP, mesma tipologia do endpoint DEMAS de cadastro vinculado abaixo),
  descartando eSB/odonto (`71`/`72`) e os demais. `DT_DESAT` usa o
  sentinela `"900001"` quando a equipe segue ativa (confirmado contra dado
  real, mesmo padrão de sentinela de "não informado"/"ainda vigente" já
  visto no SIM). `run_equipes_aps.py` já rodou de ponta a ponta contra o
  Postgres local (3 municípios, competência 2025-12: 1.659 equipes de APS —
  Rio 1.502, Nova Iguaçu 145, Paraty 12).
- **SISAB / DEMAS cadastro vinculado**: endpoint
  `/atencao-primaria/cadastro-vinculado-programa-previne-brasil` da mesma
  API DEMAS do indicador de desempenho, mas com contrato de dados
  diferente — parâmetros `codigo_municipio_ibge` + `competencia_referencia`
  (mensal, não quadrimestral) e paginação via `limit`/`offset` (implementada
  por segurança; nenhum município do MVP se aproxima do limite de 1000,
  confirmado: 24 linhas para o Rio de Janeiro). Cada linha é uma combinação
  (tipo de equipe, situação) com a população vinculada — dá cobertura de
  APS por tipo de equipe (eSF/eAP/eAPP/eCR) e situação
  (`válidas`/`homologadas`/`todas`), além de trazer `estimativa_populacional_ibge`
  já embutida (não precisa de join com `raw_ibge.populacao_estimada` para
  essa finalidade, embora as duas fontes calculem a estimativa de forma
  levemente diferente — 6.729.894 vs. 6.730.729 para o Rio, ambas mantidas
  sem escolher uma "oficial"). Mesma extinção do Previne Brasil documentada
  acima: a série também para em dez/2024 (confirmado: 202501-202512 sem
  dado para o Rio de Janeiro), então usa competência 202412 em vez do
  padrão "ano 2025". `run_cadastro_vinculado.py` já rodou de ponta a ponta
  contra o Postgres local (3 municípios, competência 202412: 54 linhas),
  idempotente em 2 execuções seguidas (delete+insert por partição
  município + competência, como o indicador de desempenho).
