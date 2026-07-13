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

O banco analítico é externo ao Astro e vem do `.env`: processos no host usam
`POSTGRES_HOST=localhost`, e o scheduler o troca pelo gateway Docker para
alcançar a porta publicada pelo serviço externo. Exige `astro dev restart`
para aplicar mudanças de ambiente.

## Status de carga de dados (escopo MVP: Rio de Janeiro + Paraty + Nova Iguaçu)

Consultado direto no Postgres local (`select count(*) ... group by
ano/competência` em cada schema raw). "Completo p/ 2025" avalia contra o
escopo padrão do MVP (docs/fontes.md#escopo-de-volume-para-o-mvp); fontes
anuais/periódicas com atraso real de publicação não têm 2025 disponível na
própria origem (não é falha da coleta, ver Observações pendentes).

Escopo ampliado em 2026-07-05 de 1 para 3 municípios (Rio de Janeiro,
Paraty, Nova Iguaçu) em todas as fontes exceto IBGE (nacional) e SIA
(estado RJ inteiro desde 2026-07-04 — já incluía os 3 antes da mudança).
Contagens abaixo já refletem os 3 municípios somados.

| Fonte | Ano/período carregado | Linhas no Postgres | Completo p/ 2025? |
| --- | --- | --- | --- |
| IBGE | cadastro corrente (sem recorte de ano) | 5.571 municípios | N/A — não é escopo anual |
| CNES | 2025-12 (1 competência; cadastro é snapshot, basta 1 mês) | 18.828 | ✅ sim |
| SIA | 2025, 12 competências (estado RJ inteiro, não só os 3 municípios) | 99.927.543 | ✅ sim |
| SIH | 2025, 12 competências | 389.923 | ✅ sim |
| FNS | 2025, ano completo (1 chamada de API por município) | 271 | ✅ sim |
| SIOPS | 2025, bimestre 6 (fechamento, valores cumulativos) | 191 | ✅ sim |
| SIM | 2024 (2025 não publicado no DATASUS) | 72.816 | ❌ estrutural — fonte sem 2025 ainda |
| SINASC | 2022 (2025 não publicado no DATASUS, maior atraso) | 75.783 | ❌ estrutural — fonte sem 2025 ainda |
| SISAB | 2024Q3 (Previne Brasil extinto em 2024) | 54 | ❌ estrutural — série descontinuada, nunca terá 2025 |

Quebra por município (raw, 2026-07-05):

| Fonte | Rio de Janeiro | Paraty | Nova Iguaçu |
| --- | --- | --- | --- |
| CNES | 17.380 | 60 | 1.388 |
| SIH | 352.790 | 3.152 | 33.981 |
| SIM | 64.704 | 253 | 7.859 |
| SINASC | 69.427 | 535 | 5.821 |
| SISAB | 18 | 18 | 18 |
| FNS | 23 | 12 | 236 |
| SIOPS | 80 | 54 | 57 |

## Demandas de dados do frontend

Demandas registradas pelo projeto `raio-x-front` para completar os dashboards
municipais. Elas fazem parte do escopo deste pipeline: cada demanda deve ser
atendida por uma nova coleta, pela ampliação de uma fonte já coletada, ou pela
modelagem dbt sobre dados já disponíveis. Para as demandas sem fonte definida,
este projeto deve identificar uma fonte pública oficial, registrar a decisão em
`docs/fontes.md` e implementar o collector, a rastreabilidade raw e os modelos
analíticos necessários para consumo do frontend.

| Demanda | Dado/modelo analítico necessário | Entrega hoje bloqueada no frontend |
| --- | --- | --- |
| Cobertura APS e equipes ESF | Indicadores municipais de cobertura APS, quantitativo e situação de equipes ESF e população total municipal de referência | ✅ `mart_cobertura_aps_municipio` (ver ROADMAP_DBT.md) |
| Metas de APS | Metas ou limiares oficiais por indicador e período, com regra de interpretação | ✅ `mart_indicadores_aps.status_meta` (ver ROADMAP_DBT.md) — só os 7 indicadores do Previne Brasil; demais fontes (ICSAP, cobertura ESF) sem meta oficial identificada |
| Internações ICSAP | Classificação de diagnósticos de internação em condição sensível à atenção primária | ✅ `mart_icsap_municipio` (ver ROADMAP_DBT.md) |
| Alertas priorizados | Mart de alertas com regra, severidade, entidade afetada, evidência, período e status | ✅ `mart_alertas_saude` (ver ROADMAP_DBT.md) |
| Histórico de rede CNES | Série histórica de estabelecimentos com situação operacional e competência de referência | ✅ `mart_historico_rede_cnes` (ver ROADMAP_DBT.md) |
| Detalhamento da APS | Indicadores em grão de equipe e unidade, quando aplicável | ✅ `mart_equipe_aps_detalhada` (ver ROADMAP_DBT.md); sem indicador de desempenho por equipe — ver seção abaixo |
| Produção por grupo | Mart de produção por município, competência e grupo de procedimento, com descrições legíveis dos grupos/procedimentos | ✅ `mart_producao_grupo_municipio` (ver ROADMAP_DBT.md) |
| Comparação entre pares | Atributos para definir pares municipais, incluindo população e porte de rede, e indicadores comparáveis para um universo suficiente de municípios | ✅ `mart_comparacao_municipios_rj` (ver ROADMAP_DBT.md) — só população e porte de rede; indicador de desempenho fica pros 3 municípios de referência |
| Séries temporais consistentes | Disponibilidade temporal harmonizada ou metadados claros de vigência e comparabilidade entre domínios | ✅ Tabela de vigência/comparabilidade documentada abaixo (não harmoniza os períodos — cada fonte publica o que tem — só torna a defasagem de cada uma explícita e centralizada) |
| Rede CNES detalhada | Identificação legível da unidade, atributos de rede e dicionários completos de códigos | ✅ `dim_estabelecimento` enriquecida via DEMAS (ver ROADMAP_DBT.md) |
| Financiamento municipal completo | Visão analítica de transferências e financiamento com escopo e semântica consolidados | ✅ `mart_financiamento_saude_uniao` (ver ROADMAP_DBT.md) |

Não fazem parte deste roadmap: implementação de relatórios com IA, exportação
em PDF/apresentação, interações de interface e decisões de arquitetura do
frontend. O frontend consome as relações analíticas publicadas por este
pipeline; limitações de cobertura e período devem permanecer documentadas nos
collectors e modelos correspondentes.

### Raw coletado para "Cobertura APS e equipes ESF" (2026-07-12)

Três novas entidades atendem esta demanda, cada uma preservando sua própria
competência e semântica no raw layer (sem forçar equivalência entre o estado
agregado do DEMAS e o estado derivado de equipe ativa do CNES):

| Entidade | Tabela raw | Fonte | Escopo carregado |
| --- | --- | --- | --- |
| População estimada do IBGE | `raw_ibge.populacao_estimada` | Agregado 6579 (SIDRA), variável 9324 — ver docs/fontes.md | 3 municípios de referência, ano 2025 (3 linhas) |
| Equipes de APS do CNES | `raw_cnes.equipes_aps` | Grupo "EP" do CNES (mesmo pysus/FTP do grupo "ST") — ver docs/COLLECTOR_TEMPLATE.md | 3 municípios, competência 2025-12, tipos eSF/eCR/eAPP/eAP (1.659 linhas: Rio 1.502, Nova Iguaçu 145, Paraty 12) |
| Cadastro vinculado do Previne Brasil (SISAB/DEMAS) | `raw_sisab.cadastro_vinculado` | Endpoint `/atencao-primaria/cadastro-vinculado-programa-previne-brasil` do DEMAS | 3 municípios, competência 202412 — última disponível, mesma extinção do Previne Brasil do `indicador_desempenho` (54 linhas) |

`run_populacao_estimada.py`, `run_equipes_aps.py` e `run_cadastro_vinculado.py`
já rodaram de ponta a ponta contra o Postgres local; o de cadastro vinculado
foi confirmado idempotente em 2 execuções seguidas (delete + insert por
partição município + competência, mesmo padrão do `indicador_desempenho`).
`estimativa_populacional_ibge` já vem embutida na resposta do cadastro
vinculado (6.729.894 para o Rio) e é levemente diferente da população do
agregado 6579 direto (6.730.729) — as duas fontes calculam a estimativa de
formas ligeiramente diferentes; manter as duas raws separadas em vez de
escolher uma preserva a rastreabilidade de qual cálculo cada consumidor usa.

Modelagem dbt (2026-07-12): `stg_ibge__populacao_estimada`,
`stg_cnes__equipes_aps` (sigla/situação de equipe decodificadas) e
`stg_sisab__cadastro_vinculado` alimentam `mart_cobertura_aps_municipio`
(1 linha por município, ver ROADMAP_DBT.md para os detalhes de grão e
decisões de agregação). Cobertura ESF calculada: Rio de Janeiro 82,7%,
Paraty 81,9%, Nova Iguaçu 42,9% (cadastro homologado, sem ponderação,
sobre a população vinculada à eSF / população estimada do IBGE).

Contexto: esta é a mesma feature de coleta de uma tentativa anterior (nesta
mesma máquina, commits `a6fca75..33fe3e9`, revertidos do `main` via reset
antes desta sessão) que também migrava o armazenamento raw para um lake. A
ideia de coleta (CNES grupo "EP", SISAB cadastro vinculado) foi recuperada e
reimplementada; a migração para lake foi descartada — arquitetura permanece
só Postgres, conforme CLAUDE.md.

### Raw histórico para "Histórico de rede CNES" (2026-07-12)

`raw_cnes.estabelecimentos` (grupo "ST") mudou de cadastro-snapshot (1 linha
por `codigo_cnes`, sobrescrita a cada carga) para série histórica (1 linha
por `codigo_cnes` + `competencia`, chave primária composta). O collector
agora carrega os 12 meses de 2025 em vez de só dez/2025 — mesmo padrão de
loop mensal do SIH (`run_estabelecimentos.py`, ~7-8s por competência, 90s
total). Migração de schema feita via `ALTER TABLE ... DROP CONSTRAINT ...
ADD PRIMARY KEY (codigo_cnes, competencia)` (sem perda das 18.828 linhas já
carregadas — trocou só a constraint, não os dados) e recarga completa dos
12 meses depois: **228.936 linhas**, rede variando de 18.225 estabelecimentos
em jan/2025 a 19.839 no pico (set/2025), voltando a 18.828 em dez/2025 — o
próprio sinal de abertura/fechamento que a demanda pede.

`dim_estabelecimento` (dbt) precisou de ajuste para não quebrar: como
`stg_cnes__estabelecimentos` passou a ter várias linhas por estabelecimento,
a dimensão agora filtra pela competência mais recente de cada `codigo_cnes`
(`row_number() over (partition by codigo_cnes order by competencia_date
desc)`), preservando o contrato "1 linha por estabelecimento" de quem já
consome (`fct_internacoes`, `fct_producao_ambulatorial`). Como efeito
colateral correto, `dim_estabelecimento` cresceu de 18.828 para **21.010**
linhas — estabelecimentos que existiram em algum mês de 2025 mas não em
dez/2025 (fechados durante o ano) agora aparecem com sua última competência
conhecida, em vez de desaparecerem da dimensão. O teste `unique` em
`stg_cnes__estabelecimentos` mudou de `codigo_cnes` (não é mais chave
sozinho) para uma chave surrogate `id_estabelecimento_competencia`
(`codigo_cnes || '-' || competencia`); a unicidade real de
`(codigo_cnes, competencia)` já é garantida pela PRIMARY KEY do Postgres no
raw, então não foi duplicada como teste dbt no source. `dbt test` completo
(76 testes): 75 PASS + 1 WARN esperado, mesmo de antes.

Modelagem dbt (2026-07-12): `mart_historico_rede_cnes` expõe a série
completa (228.936 linhas) com um flag `situacao_operacional` derivado por
janela (`row_number`/`max` sobre `competencia_date` particionado por
`codigo_cnes`) — `ativo` (18.828, presente na competência mais recente
carregada), `possivelmente_encerrado` (2.182, última competência observada
é anterior à mais recente carregada — sinal de fechamento, não confirmação
definitiva, o CNES não expõe motivo no grupo "ST") e `historico` (207.926,
competências anteriores à última observada de cada estabelecimento). Ver
ROADMAP_DBT.md.

### Raw coletado para "Financiamento municipal completo" (2026-07-12)

Nova fonte `include/collectors/portaltransparencia/`, contra a API de Dados
do Portal da Transparência (Governo Federal) — única fonte deste projeto
que exige autenticação (chave pessoal gratuita via cadastro de e-mail,
registrada por decisão explícita do usuário; ver docs/COLLECTOR_TEMPLATE.md
para os detalhes da rota e por que `codigoFavorecido` é o filtro certo, não
`codigoIBGE`). Chave em `PORTAL_TRANSPARENCIA_API_KEY` no `.env` local (não
commitada; ver `.env.example`).

`raw_portaltransparencia.recursos_recebidos_saude` complementa
`raw_fns.repasses` (que só cobre o recorte estreito do "Programa Ágil" do
Fundo a Fundo) trazendo recursos recebidos pelo CNPJ do ente municipal de
qualquer unidade vinculada ao Ministério da Saúde. `run_recursos_recebidos.py`
já rodou de ponta a ponta contra o Postgres local (3 municípios, ano 2025:
**29 linhas** — Rio 16, Paraty 12, Nova Iguaçu 1), idempotente em 2
execuções seguidas (delete+insert por partição CNPJ + ano).

Modelagem dbt (2026-07-12): `stg_portaltransparencia__recursos_recebidos` +
`mart_financiamento_saude_uniao` consolidam as duas fontes (300 linhas:
271 do FNS + 29 do Portal da Transparência). Diferente de
`mart_financiamento_saude_siops` (mantido separado por unidades
incompatíveis, ver ROADMAP_DBT.md), aqui as duas fontes são a mesma
unidade (R$ por lançamento) — unificadas com `valor` líquido de sinal
normalizado (o FNS reporta débito com valor sempre positivo + flag
separada; o Portal da Transparência já usa sinal negativo pra
estorno/devolução; sem normalizar, somar as duas fontes juntas
sub-contaria os débitos do FNS). Mesmo consolidado, o mart não é o total
de recursos SUS do município — é só os canais que essas duas APIs
federais expõem (documentado na `description` do model).

### Modelagem para "Internações ICSAP" (2026-07-13)

`seed_icsap_cid10` traduz a Lista Brasileira de Internações por Condições
Sensíveis à Atenção Primária (Portaria SAS/MS 221/2008, 19 grupos, 106
faixas de CID-10) — fonte oficial (bvsms.saude.gov.br) inacessível no
momento da implementação, reconstruída a partir de 2 reproduções
institucionais independentes que batem byte a byte entre si (ver
ROADMAP_DBT.md para as URLs e a regra de normalização de faixa). Sem
nenhum código inventado: quando a portaria cita só a categoria (3
caracteres, sem subcategoria), a faixa foi normalizada preenchendo início
com "0" e fim com "9".

`int_sih__diagnostico_icsap` resolve cada `diagnostico_principal` distinto
de `fct_internacoes` pro grupo ICSAP (ou `NULL` se não for sensível), e
`mart_icsap_municipio` agrega por município de residência do paciente + ano
(mesmo critério da metodologia oficial). Percentuais 2025 nos municípios de
referência: Rio de Janeiro 10,0%, Nova Iguaçu 12,1%, Paraty 17,6% —
plausíveis, mas o denominador é simplificado (todas as internações, não só
"internações clínicas" como a metodologia oficial completa exige, que
também filtraria por tipo de AIH/complexidade/motivo de saída e excluiria
partos CID O80-O84); `raw_sih.internacoes` não captura esses campos ainda,
então o percentual oficial exato não é replicável sem expandir o collector
do SIH — documentado como limitação conhecida na `description` do mart.

### Modelagem para "Produção por grupo" (2026-07-13)

`seed_sigtap_grupo` traduz os 9 grupos do SIGTAP (2 primeiros dígitos do
código de 10 dígitos em `codigo_procedimento`) para descrição legível —
fonte: wiki oficial do Ministério da Saúde
(wiki.saude.gov.br/sigtap/index.php/Grupo), cruzada contra o "Anexo I —
Estrutura da Tabela de Procedimentos" do COSEMS/SC (ver ROADMAP_DBT.md).
`mart_producao_grupo_municipio` agrega `fct_producao_ambulatorial`
(99.927.543 linhas) por município do estabelecimento + competência +
grupo, pré-calculando `quantidade_produzida`/`quantidade_aprovada`/
`valor_produzido`/`valor_aprovado` — build único de ~2min21s sobre a fato
inteira (`table`, não incremental; ver ROADMAP_DBT.md sobre por que não
seguiu o padrão incremental da fato). 6.117 linhas resultantes (municípios
do RJ inteiro × 12 competências × até 9 grupos).

### Vigência e comparabilidade temporal (2026-07-13)

Referência única de período coberto e defasagem de cada fonte, pra "Séries
temporais consistentes". Não harmoniza nada tecnicamente (cada mart segue
publicando o que a fonte tem) — só documenta num lugar só o que já estava
espalhado pelas seções acima e pelo COLLECTOR_TEMPLATE.md, pra evitar que
alguém compare 2 domínios como se tivessem o mesmo período só porque os
dois dizem "2025".

| Mart/fonte | Período coberto | Defasagem/atraso | Escopo geográfico | Comparável direto com "ano 2025" de outra fonte? |
| --- | --- | --- | --- | --- |
| `dim_municipio` (IBGE) | Cadastro corrente, sem ano | N/A — não é série | Brasil inteiro | N/A |
| `mart_cobertura_aps_municipio` | População: ano 2025. Equipes CNES: competência 2025-12. Cadastro vinculado SISAB: competência 202412 | 3 datas de referência diferentes dentro do mesmo mart (ver comentário no `.sql`) | 3 municípios de referência | Não — as 3 colunas do mesmo mart já não são do mesmo instante entre si |
| `dim_estabelecimento` | Grupo "ST": competência mais recente carregada (2025-12). DEMAS (nome/endereço): cadastro vivo, sem competência, reflete o momento da carga | Sem atraso conhecido pro "ST"; DEMAS pode já estar desatualizado em relação ao "ST" se um dos dois for recarregado sem o outro | 3 municípios de referência | Representa "hoje", não um ano fechado — não comparável com séries anuais |
| `mart_historico_rede_cnes` | 12 competências, jan-dez/2025 | Nenhuma — mesmo ano de referência do MVP | 3 municípios de referência | Sim |
| `fct_internacoes` / `mart_icsap_municipio` | 12 competências de carga = 2025, mas `data_internacao` (usada pro `ano` de `mart_icsap_municipio`) tem linhas com anos anteriores (2016-2024) — internação de longa permanência processada em 2025 (ver comentário no `.sql`) | Nenhuma na carga; "linha retroativa" é característica do dado, não atraso de publicação | 3 municípios de referência (por residência do paciente) | Majoritariamente sim (a maioria das linhas é 2025), mas não 100% |
| `fct_obitos` (SIM) | Ano 2024 | 2025 não publicado no FTP do DATASUS no momento da implementação | 3 municípios de referência | Não — 1 ano atrás de internações/produção/financiamento |
| `fct_nascidos_vivos` (SINASC) | Ano 2022 | 2025 (e 2023, 2024) não publicados — maior atraso de todas as fontes | 3 municípios de referência | Não — 3 anos atrás |
| `fct_producao_ambulatorial` / `mart_producao_grupo_municipio` (SIA) | 12 competências, jan-dez/2025 | Nenhuma | **Estado do RJ inteiro**, não só os 3 municípios de referência (decisão de escopo, ver ROADMAP_DBT.md etapa 5) | Sim no tempo, mas não no espaço — agregado direto por município compara maçã com laranja se comparado sem filtrar município |
| `mart_repasses_fns` | Ano 2025 | Nenhuma | 3 municípios de referência (por CNPJ) | Sim |
| `mart_financiamento_saude_siops` | Ano 2025, bimestre 6 (fechamento) | Nenhuma — valor já é cumulativo até o bimestre | 3 municípios de referência | Sim |
| `mart_financiamento_saude_uniao` | FNS: ano 2025. Portal da Transparência: ano 2025 | Nenhuma | 3 municípios de referência | Sim |
| `mart_indicadores_aps` (SISAB indicador_desempenho) | 2024Q3 | Série **descontinuada** (Previne Brasil extinto pela Portaria GM/MS 3.493/2024) — nunca terá 2025, não é atraso temporário | 3 municípios de referência | Não — e não vai ficar comparável no futuro sem uma fonte nova pro indicador |

Padrão geral: SIM e SINASC têm atraso real de publicação (deve diminuir
com o tempo); SISAB (ambas as entidades) é descontinuação definitiva, não
atraso; SIA tem escopo geográfico mais largo que as demais fontes
municipais. Nenhuma dessas 3 situações é bug de coleta — são
características documentadas da própria fonte oficial.

### Modelagem para "Alertas priorizados" (2026-07-13)

`mart_alertas_saude` cobre 3 regras sobre marts já existentes, deliberadamente
sem nenhuma regra de meta/limiar de indicador — essas dependem da demanda
"Metas de APS" (ainda não implementada) e inventar um limiar sem fonte
verificável violaria a mesma regra de proveniência usada pros seeds
(CLAUDE.md#seeds-e-dicionários-externos-de-para). As 3 regras usam ou um
limiar legal já codificado ou um sinal estrutural sem limiar nenhum:

| Regra (`codigo_regra`) | Severidade | Fonte | Resultado real (carga atual) |
| --- | --- | --- | --- |
| `siops_abaixo_minimo_constitucional` | alta | `mart_financiamento_saude_siops`: "% Aplicado Até o Bimestre" vs "% Mínimo a Aplicar no Exercício" (LC 141/2012, ~15% pra municípios) | 0 alertas — os 3 municípios cumprem o mínimo (Nova Iguaçu 15,55%, Paraty 15,9%, Rio 16,98%) |
| `rede_cnes_possivel_encerramento` | media | `mart_historico_rede_cnes`: `situacao_operacional = 'possivelmente_encerrado'`, contado por município | 3 alertas — Rio (2.157 estabelecimentos), Nova Iguaçu (24), Paraty (1) |
| `financiamento_liquido_negativo` | media | `mart_financiamento_saude_uniao`: soma de `valor` por município + ano, quando negativa | 1 alerta — Rio, saldo líquido de -R$ 60.774,46 em 2025 |

`id_alerta` é uma chave surrogate (`md5(codigo_regra || id_municipio ||
periodo_referencia)`). `status` é sempre `"ativo"`: o mart é full-refresh sem
histórico de execuções persistido, então não há como saber se um alerta de
uma carga anterior foi "resolvido" — rastrear isso ao longo do tempo exigiria
guardar histórico de execuções, não implementado ainda. `dbt test` do mart:
8/8 PASS.

### Modelagem para "Detalhamento da APS" (2026-07-13)

`raw_cnes.equipes_aps` já tinha o grão que a demanda pede — `codigo_cnes`
(unidade) por equipe já vinha no cadastro CNES, sem necessidade de nova
coleta. `mart_equipe_aps_detalhada` expõe 1 linha por equipe (1.659 linhas),
com a unidade resolvida via `dim_estabelecimento` (nome, endereço, bairro)
e o município via `dim_municipio`, mais área/segmento de atuação da equipe.

Fica de fora, deliberadamente: indicador de desempenho por equipe
específica. A única fonte de indicador coletada (SISAB
`indicador_desempenho`, `mart_indicadores_aps`) publica `visao_equipe` como
o **tipo** de equipe (eSF/eAP/etc.) agregado por município — não a equipe
individual (`id_equipe`) — então não há como juntar 1:1 sem inventar uma
correspondência equipe-a-equipe que a fonte não garante. "Desempenho
localizado" por equipe específica depende de uma fonte que publique nesse
grão, ainda não identificada. `dbt test`: 11/11 PASS + 1 WARN esperado
(mesmo de sempre, `fct_producao_ambulatorial` → `dim_estabelecimento`).

### Raw e modelagem para "Rede CNES detalhada" (2026-07-13)

Novo collector `run_estabelecimentos_detalhados.py` traz o cadastro
complementar do DEMAS (nome fantasia, endereço, geolocalização, esfera
administrativa decodificada) pros 3 municípios de referência —
`raw_cnes.estabelecimentos_detalhados`, **30.869 linhas** (Rio 29.155,
Nova Iguaçu 1.627, Paraty 87). Cadastro vivo, sem competência (upsert por
`codigo_cnes`, sobrescreve o estado mais recente a cada carga) — diferente
da série histórica do grupo "ST", que preserva 1 linha por competência.
API pagina fixo em 20 registros por página sem expor total; Rio de Janeiro
sozinho levou ~15,4min pra paginar (~1.460 páginas).

`dim_estabelecimento` (dbt) ganhou um LEFT JOIN simples com
`stg_cnes__estabelecimentos_detalhados` (por `codigo_cnes`, sem window
function — cadastro vivo, não série): nome_fantasia, endereço, bairro,
CEP, latitude/longitude, esfera administrativa decodificada, turno de
atendimento e flags de centro cirúrgico/obstétrico/neonatal/atendimento
hospitalar. Campos ficam `NULL` quando o estabelecimento não está nesse
cadastro complementar (sem teste `not_null` nesses campos). `dbt test`:
147 PASS + 1 WARN esperado (mesmo de sempre).

### Modelagem para "Comparação entre pares" (2026-07-13)

Escopo confirmado com o usuário: universo de comparação é o **RJ inteiro
(92 municípios)**, não o Brasil todo — mantém o projeto num único estado,
volume moderado. Duas coletas novas, ambas reaproveitando infraestrutura
já existente (nenhuma fonte nova):

| Atributo | Raw | Como foi coletado |
| --- | --- | --- |
| População estimada | `raw_ibge.populacao_estimada` (mesma tabela da "Cobertura APS", agora com 92 linhas em vez de 3) | `run_populacao_estimada_rj.py` — sintaxe de localidade aninhada do SIDRA (`N6[N3[33]]` = todos os municípios do estado 33/RJ), 1 chamada HTTP só, confirmada contra a API real (92 municípios) |
| Porte de rede | `raw_cnes.rede_porte_municipio` (nova tabela, contagem de estabelecimentos por município) | `run_rede_porte_municipio.py` — reaproveita `fetch_estabelecimentos` (grupo "ST", já baixa o estado inteiro), só agrega por `CODUFMUN` sem filtrar; delete + insert por competência |

`mart_comparacao_municipios_rj` expõe 1 linha por município (92), com
`municipio_referencia` marcando quais são os 3 do MVP. Fica de fora,
deliberadamente: indicador de desempenho (SISAB, ICSAP, financiamento) e
qualquer classificação de porte populacional — essas fontes seguem
coletadas só pros 3 municípios de referência, e uma categoria de porte
inventada sem fonte oficial violaria a mesma regra de proveniência dos
seeds (CLAUDE.md#seeds-e-dicionários-externos-de-para). Expandir indicador
por indicador pros 92 fica pra quando o frontend definir quais
indicadores o pareamento realmente precisa.

**Efeito colateral tratado**: `raw_ibge.populacao_estimada` deixou de ser
exclusiva dos 3 municípios de referência — sem ajuste, `mart_cobertura_aps_municipio`
ganharia 89 linhas extras (só população preenchida, equipes/cobertura
`NULL`). Corrigido com um filtro explícito nesse mart, pinando seu escopo
original nos 3 municípios de referência independente do que a tabela raw
compartilhada tiver (ver comentário no `.sql`).

### Modelagem para "Metas de APS" (2026-07-13)

Última demanda do frontend, implementada por último por decisão explícita
do usuário (evita inventar limiar antes de esgotar as fontes oficiais
disponíveis — mesmo cuidado já registrado no comentário de
`mart_alertas_saude.sql`).

`seed_previne_brasil_meta` traz PARÂMETRO (valor ideal) e META (valor
pactuado) oficiais dos 7 indicadores do Previne Brasil, extraídos
diretamente da seção "FICHA DE QUALIFICAÇÃO DO INDICADOR" de cada uma das
7 notas técnicas da SAPS/MS (mesma fonte já usada por
`seed_sisab_tipo_indicador`) — ver `_seeds__models.yml` para a tabela
completa por indicador. `mart_indicadores_aps` ganhou `status_meta`
derivado só desses 2 limiares oficiais (sem inventar um terceiro): `ok`
quando o percentual do quadrimestre atinge o parâmetro (valor ideal),
`atencao` quando fica abaixo do parâmetro mas atinge a meta pactuada, e
`critico` quando fica abaixo até da meta pactuada. Resultado real (54
linhas, 3 municípios × até 7 indicadores × período disponível): 0 "ok", 15
"atencao", 39 "critico" — nenhum indicador atinge o parâmetro ideal em
nenhum dos 3 municípios, consistente com o cenário nacional descrito nas
próprias notas técnicas (ex.: indicador 5 tem parâmetro=meta=95%, os
outros 6 têm meta bem abaixo do parâmetro exatamente por reconhecer essa
dificuldade).

Fica de fora, deliberadamente: metas para ICSAP, cobertura ESF ou
qualquer indicador fora do Previne Brasil — nenhuma fonte oficial
equivalente foi identificada para essas, e o mesmo cuidado de não inventar
limiar (CLAUDE.md#seeds-e-dicionários-externos-de-para) se aplica aqui.
`dbt test` completo (153 testes): 152 PASS + 1 WARN esperado (mesmo de
sempre).

Com esta demanda, todas as 11 demandas de dados do frontend registradas
neste ROADMAP estão atendidas.

## Observações pendentes

- **Expansão para Paraty e Nova Iguaçu (2026-07-05)**: escopo do MVP saiu
  de 1 município (Rio de Janeiro) para 3, em todas as fontes exceto IBGE
  (nacional, sem filtro) e SIA (já cobria o estado inteiro desde
  2026-07-04). Cada fonte identifica município por um sistema de código
  diferente (ver tabela em docs/fontes.md#escopo-de-volume-para-o-mvp);
  os códigos de Paraty/Nova Iguaçu para CNES/SIH/SIM/SINASC/SISAB (IBGE 6
  dígitos) e SIOPS (IBGE 7 dígitos) já eram conhecidos via
  `raw_ibge.municipios`. O CNPJ de cada um pro FNS não era óbvio — não tem
  de-para público direto de município para CNPJ do Fundo Municipal de
  Saúde — então foi descoberto consultando a própria API do FNS por nome
  do ente (`nome_ente_solicitante_gestao_financeira=ilike.*PARATI*` /
  `*IGUACU*`) e confirmando que o CNPJ encontrado retorna lançamentos reais
  em 2025: Paraty `29172475000147`, Nova Iguaçu `29138278000101`.
  Mudanças: `parser.py` de cada fonte trocou a constante singular
  `MUNICIPIO_REFERENCIA_*` por uma tupla `MUNICIPIOS_REFERENCIA_*` (3
  códigos); CNES e SIH (upsert por chave natural) só precisaram alargar o
  filtro; SIM e SINASC (delete+insert por partição ano+município) tiveram
  o `DELETE` migrado para `= ANY(%(municipios)s)`, processando os 3 num
  lote só; SISAB, FNS e SIOPS (1 chamada de API por município) passaram a
  iterar a tupla em `run()`, cada um mantendo sua partição/upsert por
  município como já fazia para 1. `seed_fns_ente_municipio.csv` (de-para
  CNPJ → id_municipio, ver ROADMAP_DBT.md) ganhou as 2 linhas novas — sem
  isso, `mart_repasses_fns` teria `id_municipio` NULL para os lançamentos
  dos 2 municípios novos (pegou pelo teste `not_null` do dbt, que falhou
  antes do seed ser atualizado). Todas as contagens do Rio de Janeiro
  ficaram intactas depois da mudança (confirmado por município antes e
  depois); 182 testes de collector (`pytest tests/collectors`) e 71 testes
  dbt continuam passando (70 PASS + 1 WARN esperado, mesma razão de
  sempre).

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

  **Handoff concluído em 2026-07-05, máquina nova**: ambiente montado do
  zero (Fedora, sem pyenv/uv — python3.14 do sistema não suporta
  `pysus==2.6.1`, que exige <3.14; instalado `python3.12` via `dnf` pra
  criar o venv), `astro dev start` subiu limpo, `docker-compose.override.yml`
  aplicado automaticamente na 1ª subida. As 9 fontes foram recarregadas do
  zero contra o Postgres novo, todas batendo com as contagens documentadas
  acima. Máquina bem mais rápida (236GB disco/19GB RAM): SIA completo em
  **3.194s (~53min)**, contra ~2h28 na máquina anterior — mesmas
  99.927.543 linhas, sem OOM (memória ficou apertada, chegou a usar swap,
  mas não travou). Etapa 5 do dbt (bloqueada no handoff anterior por
  estouro de disco) foi resolvida nesta máquina — ver ROADMAP_DBT.md.
