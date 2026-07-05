# Roadmap de fontes

Status dos collectors do projeto `raio-x-engenharia`. Rotas candidatas e
detalhes por fonte em [docs/fontes.md](docs/fontes.md). Estrutura de arquivos
a seguir em novos collectors: [docs/COLLECTOR_TEMPLATE.md](docs/COLLECTOR_TEMPLATE.md).

| Fonte | Status | Schema raw | Escopo (1 linha) |
| --- | --- | --- | --- |
| IBGE | ✅ collector pronto | `raw_ibge` | Municípios (hierarquia territorial) |
| CNES | ✅ collector pronto | `raw_cnes` | Estabelecimentos de saúde |
| SIA | ✅ collector pronto | `raw_sia` | Produção ambulatorial (RJ inteiro, não só Rio) |
| SIH | ✅ collector pronto | `raw_sih` | Internações |
| SISAB | ✅ collector pronto | `raw_sisab` | Indicadores de atenção básica |
| FNS | ✅ collector pronto | `raw_fns` | Repasses/financiamento |
| SIOPS | ✅ collector pronto | `raw_siops` | Orçamento em saúde |
| SIM | ✅ collector pronto | `raw_sim` | Óbitos |
| SINASC | ✅ collector pronto | `raw_sinasc` | Nascidos vivos |

DAGs Airflow: uma DAG por fonte em `dags/raw_<fonte>.py`, cada uma só
chamando o `run()` do collector correspondente (`schedule=None`, disparo
manual — o escopo de cada collector ainda é fixo/hardcoded, não
parametrizado por data de execução). As 9 DAGs foram validadas de ponta a
ponta dentro do container real do Airflow (`docker exec ... airflow tasks
test`), não só localmente: IBGE, CNES, FNS, SIOPS, SISAB, SIH, SIM e SINASC
rodaram com sucesso; SIA não foi rodado dentro da DAG por levar ~1,5-2h,
mas a lógica do collector já foi validada fora do Airflow (ver observação
abaixo).

`docker-compose.override.yml` sobrescreve `POSTGRES_HOST`/`POSTGRES_PORT`
só no container do `scheduler` (LocalExecutor, onde as tasks rodam de
fato): o `.env` do projeto aponta para `localhost`, correto para rodar um
collector via `python -m ...` no host, mas errado de dentro da rede docker
do Airflow, onde o Postgres é alcançável pelo hostname de serviço
`postgres`. Exige `astro dev restart` para aplicar.

## Status de carga de dados (Rio de Janeiro, escopo MVP)

Consultado direto no Postgres local (`select count(*) ... group by
ano/competência` em cada schema raw). "Completo p/ 2025" avalia contra o
escopo padrão do MVP (docs/fontes.md#escopo-de-volume-para-o-mvp); fontes
anuais/periódicas com atraso real de publicação não têm 2025 disponível na
própria origem (não é falha da coleta, ver Observações pendentes).

| Fonte | Ano/período carregado | Linhas no Postgres | Completo p/ 2025? |
| --- | --- | --- | --- |
| IBGE | cadastro corrente (sem recorte de ano) | 5.571 municípios | N/A — não é escopo anual |
| CNES | 2025-12 (1 competência; cadastro é snapshot, basta 1 mês) | 17.380 | ✅ sim |
| SIA | 2025, 12 competências (estado RJ inteiro, não só Rio) | 99.927.543 | ✅ sim |
| SIH | 2025, 12 competências | 352.790 | ✅ sim |
| FNS | 2025, ano completo (1 chamada de API) | 23 | ✅ sim |
| SIOPS | 2025, bimestre 6 (fechamento, valores cumulativos) | 80 | ✅ sim |
| SIM | 2024 (2025 não publicado no DATASUS) | 64.704 | ❌ estrutural — fonte sem 2025 ainda |
| SINASC | 2022 (2025 não publicado no DATASUS, maior atraso) | 69.427 | ❌ estrutural — fonte sem 2025 ainda |
| SISAB | 2024Q3 (Previne Brasil extinto em 2024) | 18 | ❌ estrutural — série descontinuada, nunca terá 2025 |

## Observações pendentes

- **SIOPS**: a rota candidata original (site legado
  `siops.datasus.gov.br`) foi abandonada — seu relatório de cálculo do %
  de saúde (`carregarDadosLC141.php`) retorna respostas de 300+ MB com
  valores zerados para o Rio de Janeiro em 2021-2024 (bug real do sistema
  legado, não da nossa coleta). Implementado contra o substituto de fato:
  **SICONFI** (Tesouro Nacional, API REST pública sem autenticação em
  `apidatalake.tesouro.gov.br`), endpoint `/rreo`, anexo "RREO-Anexo 14"
  (Demonstrativo Simplificado, inclui a linha de aplicação mínima em saúde
  da LC 141/2012). Diferente de SIM/SINASC, **não há atraso**: 2025
  completo e disponível (todos os 6 bimestres). `run_rreo_anexo14.py` já
  rodou de ponta a ponta contra o Postgres local (Rio de Janeiro, 2025,
  bimestre 6 — fechamento do exercício: 80 linhas, 16,98% aplicado em
  saúde vs. mínimo de 15%, R$ 3,93 bi apurados), idempotente em 2
  execuções seguidas (delete + insert por partição município+ano+bimestre,
  sem chave natural de linha). Município identificado pelo código IBGE
  completo (`cod_ibge`, 7 dígitos, igual `raw_ibge.municipios.id_municipio`)
  — sem de-para necessário, diferente das fontes DATASUS (código truncado
  de 6 dígitos) e do FNS (CNPJ).
- **SIM** e **SINASC**: fontes anuais (não mensais), com atraso de
  consolidação — 2025 ainda não publicado no FTP do DATASUS para nenhum dos
  dois. Escopo usa o último ano realmente disponível: SIM ano 2024, SINASC
  ano 2022 (confirmado direto no FTP). `run_obitos.py` e
  `run_nascidos_vivos.py` já rodaram de ponta a ponta contra o Postgres
  local (SIM: 64.704 óbitos do Rio em 2024; SINASC: 69.427 nascimentos do
  Rio em 2022), ambos com idempotência confirmada em 2 execuções seguidas
  (delete + insert por partição ano+município, como o SIA — nenhum dos dois
  tem identificador de registro estável entre execuções).
- **SIH**: `run_internacoes.py` já rodou o ano completo de 2025 de ponta a
  ponta contra o Postgres local (12 competências, 355.141 linhas
  processadas, 352.790 `numero_aih` distintos gravados — a diferença de
  2.351 é AIH que aparece em mais de 1 competência/arquivo, corretamente
  absorvida pelo upsert em vez de virar duplicata). ~7-8s por competência
  (bem mais rápido que o SIA: o grupo RD é 1 arquivo por competência, sem
  múltiplas partes de 100+MB).
- **FNS**: `run_repasses.py` já rodou de ponta a ponta contra o Postgres
  local para 2025 (23 lançamentos, upsert confirmado idempotente em 2
  execuções seguidas). Volume baixo porque a API de Fundo a Fundo cobre só
  os lançamentos da conta bancária vinculada ao "Programa Ágil" (código 140)
  — não é o total histórico de repasses SUS ao município, é o recorte que a
  API pública realmente expõe.
- **SISAB**: a rota candidata original (`sisab.saude.gov.br`, painel
  restrito) e o FTP candidato (`CMD/Dados`, vazio) foram abandonados —
  nenhum dos dois tinha download simples. Implementado contra a **API de
  Dados Abertos do Ministério da Saúde (DEMAS)**,
  `apidadosabertos.saude.gov.br`, endpoint
  `/atencao-primaria/indicador-desempenho-programa-previne-brasil` — API
  REST JSON pública, sem autenticação, com filtro nativo por código IBGE
  do município. Expõe os indicadores de desempenho do Programa Previne
  Brasil (mesmo cálculo que o SISAB usa para financiamento da APS). O
  Previne Brasil foi extinto pela Portaria GM/MS Nº 3.493/2024 e
  substituído por nova metodologia — a série para no 3º quadrimestre de
  2024 (confirmado: 2025Q1/Q2/Q3 sem dado na API), então o escopo usa o
  último quadrimestre disponível (2024Q3) em vez do padrão "ano 2025".
  `run_indicador_desempenho.py` já rodou de ponta a ponta contra o
  Postgres local (Rio de Janeiro, 2024Q3: 18 linhas — 6 tipos de indicador
  x 3 visões de equipe), idempotente em 2 execuções seguidas (delete +
  insert por partição município+quadrimestre).
- **SIA**: mudança de escopo em 2026-07-04 — o collector passou a carregar
  o **estado (UF) inteiro**, não só o município de referência (Rio).
  Motivo: perfilamento real mostrou que `client.py` já decodifica
  (`to_dict`) o arquivo inteiro antes de qualquer filtro por município ser
  possível (formato DBC não permite leitura parcial); filtrar por
  município acontecia só depois, no parser, descartando ~38% das linhas
  já decodificadas sem nunca persisti-las (medido: Rio é 62% do estado,
  arquivo de nov/2025). Sem ganho de tempo real em manter o filtro, e
  fechava a porta pra outros municípios do RJ no futuro — decisão de
  guardar o estado inteiro (`parser.py`/`repository.py` atualizados,
  partição de delete+insert agora é só por competência, não mais
  competência+município). Volume sobe de ~56M para ~90M linhas/ano.
  Detalhes do perfilamento (tempo gasto em download/decompressão/leitura/
  conversão) ficaram só no histórico da conversa, não documentados em
  arquivo — a decisão e o resultado é o que importa daqui pra frente.

  Duas quedas de energia atrapalharam a carga completa nesta sessão: a
  1ª corrompeu dados parciais no Postgres (raw_sia ficou com contagens
  muito abaixo do esperado por competência — recuperado rodando de novo,
  delete+insert é idempotente); a 2ª aconteceu ainda filtrando por
  município, então a carga foi reiniciada do zero já com a mudança de
  escopo acima.

  Bug real encontrado em 2026-07-05 (pré-existente, não causado pela
  mudança de escopo): o delete+insert particionava pela competência REAL
  de cada linha (PA_CMP), não pelo mês do arquivo buscado. Um arquivo de
  uma competência pode conter linhas retroativas de competências bem
  anteriores (confirmado: arquivo de set/2025 trouxe linhas com
  competência real até out/2024); como os 12 meses são processados em
  sequência na mesma execução, um fetch posterior com qualquer linha
  retroativa apagava o mês inteiro já carregado e substituía só pelo
  pedaço retroativo — confirmado: depois de rodar jan-set/2025, jan/2025
  ficou com ~39 mil linhas em vez das ~7,5 milhões que o próprio fetch de
  janeiro relatou. Corrigido: partição agora é por `competencia_arquivo`
  (ano/mês do fetch), exclusiva por chamada, não mais pela competência
  real. Ver commit do fix.

  A mesma rodada também foi morta pelo **OOM killer** no meio do mês 9
  (confirmado via `dmesg`, não foi queda de energia desta vez) — a máquina
  já estava com pouca memória livre (~4,7GB) e o volume do estado inteiro
  (~9M linhas em alguns meses) mais que dobrou o pico de RAM comparado ao
  escopo só-Rio. Mitigado parcialmente: `run()` não segura mais as listas
  bruta e parseada ao mesmo tempo. Risco de OOM permanece real pra meses
  com volume retroativo grande; acompanhar `free -h` durante a carga.

  Tabela foi derrubada e recriada (schema novo com `competencia_arquivo`,
  dado anterior já estava incorreto de qualquer forma) antes de reiniciar
  a carga pela 4ª vez.

  ✅ **Carga completa concluída em 2026-07-05**: 12/12 competências,
  **99.927.543 linhas**, 8.906s (~2h28) — terminou normal, sem OOM desta
  vez (memória ficou crítica em vários pontos, chegou a 163Mi disponível,
  mas sobreviveu). Confirmado por competência (`competencia_arquivo`):
  jan=7.535.342, fev=7.494.257, mar=7.806.475, abr=8.241.360,
  mai=8.483.346, jun=7.515.423, jul=9.277.389, ago=8.729.858,
  set=9.216.984, out=8.998.937, nov=8.435.115, dez=8.193.057 — todas
  batendo com o log, nenhuma sobrescrita pelo bug de partição (corrigido
  acima). Rodar manualmente quando fizer sentido:
  `python -m include.collectors.sia.run_producao_ambulatorial`.
