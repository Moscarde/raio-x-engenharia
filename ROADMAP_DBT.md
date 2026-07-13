# Roadmap dbt

Planejamento da camada de transformação (`dbt/`) sobre as 9 tabelas raw já
carregadas (ver [ROADMAP.md](ROADMAP.md)). Convenções de nomeação e schemas
em [CLAUDE.md](CLAUDE.md#convenções-de-nomeação-dbt).

## Status

- ✅ Etapa 1 — scaffold + `stg_ibge__municipios` + `dim_municipio`.
- ✅ Etapa 2 — `stg_cnes__estabelecimentos` + `dim_estabelecimento` +
  `seed_cnes_natureza_juridica`.
- ✅ Etapa 3 — `int_ibge__municipio_codigo6` (bridge 6↔7 dígitos).
- ✅ Etapa 4 — `stg_sih__internacoes` + `fct_internacoes`.
- ✅ Etapa 6 — `stg_sim__obitos` + `fct_obitos`,
  `stg_sinasc__nascidos_vivos` + `fct_nascidos_vivos`.
- ✅ Etapa 7 — `stg_fns__repasses` + `stg_siops__rreo_anexo14` +
  `mart_repasses_fns` + `mart_financiamento_saude_siops` (2 marts
  separados, não 1 — ver nota abaixo).
- ✅ Etapa 8 — `stg_sisab__indicador_desempenho` +
  `seed_sisab_tipo_indicador` + `mart_indicadores_aps`.
- ✅ Etapa 5 — `stg_sia__producao_ambulatorial` + `fct_producao_ambulatorial`,
  concluída em 2026-07-05 na máquina nova (ver "Handoff resolvido" abaixo).
- ✅ Etapa 9 (2026-07-12) — modelagem das demandas do frontend registradas
  em ROADMAP.md: `mart_cobertura_aps_municipio` (população IBGE + equipes
  CNES + cadastro vinculado SISAB), `mart_historico_rede_cnes` (auditoria
  de abertura/fechamento sobre a série histórica do CNES) e
  `mart_financiamento_saude_uniao` (FNS + Portal da Transparência
  consolidados). Ver seção "Etapa 9" abaixo para detalhes de grão e
  decisões de agregação.
- ✅ Etapa 10 (2026-07-13) — `mart_icsap_municipio`: percentual de
  Internações por Condições Sensíveis à Atenção Primária, via
  `seed_icsap_cid10` (Lista Brasileira, Portaria SAS/MS 221/2008) e
  `int_sih__diagnostico_icsap`. Ver seção "Etapa 10" abaixo.
- ✅ Etapa 11 (2026-07-13) — `mart_producao_grupo_municipio`: produção
  ambulatorial agregada por município, competência e grupo SIGTAP, via
  `seed_sigtap_grupo`. Ver seção "Etapa 11" abaixo.
- ✅ Etapa 12 (2026-07-13) — `mart_alertas_saude`: alertas priorizados por
  regra (SIOPS abaixo do mínimo constitucional, rede CNES com possível
  encerramento, financiamento líquido negativo), sem regra de meta de
  indicador. Ver seção "Etapa 12" abaixo.
- ✅ Etapa 13 (2026-07-13) — `mart_equipe_aps_detalhada`: detalhamento da
  APS em grão de equipe/unidade, sobre `raw_cnes.equipes_aps` (já tinha o
  grão certo, sem nova coleta). Ver seção "Etapa 13" abaixo.
- ✅ Etapa 14 (2026-07-13) — `stg_cnes__estabelecimentos_detalhados` +
  enriquecimento de `dim_estabelecimento` via DEMAS (nome, endereço,
  geolocalização, esfera administrativa decodificada). Ver seção
  "Etapa 14" abaixo.
- ✅ Etapa 15 (2026-07-13) — `mart_comparacao_municipios_rj`: universo de
  92 municípios do RJ (não só os 3 de referência) com população e porte
  de rede, via `run_populacao_estimada_rj.py` (SIDRA `N6[N3[33]]`) e
  `raw_cnes.rede_porte_municipio` (novo). Ver seção "Etapa 15" abaixo.
- ✅ Etapa 16 (2026-07-13) — `mart_indicadores_aps.status_meta`: parâmetro
  e meta oficiais do Previne Brasil (`seed_previne_brasil_meta`, 7
  indicadores) e status derivado ok/atencao/critico. Última demanda do
  frontend — todas as 11 estão atendidas. Ver seção "Etapa 16" abaixo.

Rodado de ponta a ponta (`dbt seed && dbt run && dbt test`), já com
`raw_cnes.estabelecimentos_detalhados` totalmente carregado (30.869 linhas):
**34 models, 7 seeds, 153 testes — 152 PASS + 1 WARN esperado** (relationship
`fct_producao_ambulatorial` → `dim_estabelecimento`, mesma razão do WARN já
existente em `fct_internacoes`: o CNES cobre só as competências de 2025, não
necessariamente todo `codigo_cnes` referenciado no ano inteiro do SIA).

## Ajustes de design feitos durante a implementação

Duas decisões do planejamento original mudaram ao encostar no dado real —
registradas aqui em vez de só no histórico do git, pra quem ler este
roadmap não achar que a tabela abaixo ("Camada intermediate"/"marts")
ainda reflete o que foi construído.

- **Sem "int_saude__eventos_com_municipio" único.** O plano original
  previa 1 intermediate unindo SIH+SIM+SINASC+SIA num model só. Na prática
  isso não faz sentido: cada fonte tem grão e colunas completamente
  diferentes (internação ≠ óbito ≠ nascimento), forçar união exigiria uma
  UNION com preenchimento de coluna genérica sem ganho real. O que
  realmente se repetia entre as 3 fontes era só a *resolução* do código
  IBGE de 6 dígitos pra `id_municipio` (7 dígitos) — isso virou
  `int_ibge__municipio_codigo6`, um bridge pequeno e reutilizável (join
  direto em cada fct), não um model que "junta os eventos".
- **`mart_financiamento_saude` virou 2 marts, não 1.** FNS é ledger
  transacional (R$, crédito/débito) e SIOPS é demonstrativo fiscal
  agregado (mistura contas em R$ e percentuais no mesmo formato "long").
  Somar as duas fontes numa tabela só misturaria unidades incompatíveis
  (não dá pra somar R$ com %). Ficaram `mart_repasses_fns` e
  `mart_financiamento_saude_siops`, cada um fiel à granularidade real da
  própria fonte.
- **`dim_estabelecimento` ganhou `id_municipio` em 2026-07-05.** O plano
  original adiava essa resolução pra "quando o primeiro fato precisar
  disso" (comentário no `.sql` antigo). Esse momento chegou de fora do
  dbt: o consumidor Evidence (`raio-x-dash-evidence-dev`), ao implementar
  o seletor de município em `pages/perfil-municipal.md`, precisou cruzar
  estabelecimentos por município e — na ausência do `id_municipio` na
  mart — replicou o `left(m.id_municipio::text, 6) = e.cod_municipio_ibge6`
  direto na página, duplicando lógica que já existia em
  `int_ibge__municipio_codigo6`. Resolvido aplicando o mesmo bridge já
  usado pelos fatos, sem inventar padrão novo: `dim_estabelecimento` agora
  expõe `id_municipio` (7 dígitos) e mantém `cod_municipio_ibge6` (6
  dígitos) para quem já dependia dele. Teste `not_null` + `relationships`
  contra `dim_municipio` sem `severity: warn` — diferente do warn em
  `codigo_cnes_estabelecimento` (que depende do snapshot mensal do CNES
  cobrir todo `codigo_cnes` referenciado em um ano inteiro de eventos),
  aqui o de-para é só truncamento de código contra `raw_ibge.municipios`
  (cobertura nacional), sem motivo esperado para falhar.
- **`dim_estabelecimento` ganhou filtro de competência mais recente em
  2026-07-12.** `raw_cnes.estabelecimentos` virou série histórica (chave
  composta `codigo_cnes` + `competencia`, 12 meses de 2025 em vez de só
  dez/2025 — demanda "Histórico de rede CNES", ver ROADMAP.md), então
  `stg_cnes__estabelecimentos` passou a ter várias linhas por
  estabelecimento. Sem ajuste, `dim_estabelecimento` quebraria o teste
  `unique` em `codigo_cnes`. Resolvido com
  `row_number() over (partition by codigo_cnes order by competencia_date
  desc)` filtrando pra linha mais recente — a dimensão mantém o contrato
  "1 por estabelecimento" pra `fct_internacoes`/`fct_producao_ambulatorial`,
  e cresceu de 18.828 para 21.010 linhas (estabelecimentos que só existiram
  em meses anteriores a dez/2025 agora aparecem com sua última competência
  conhecida, em vez de ficarem de fora). A série completa (não só a
  competência mais recente) segue disponível em `stg_cnes__estabelecimentos`
  e em `mart_historico_rede_cnes` (ver Etapa 9 abaixo). Teste de unicidade
  do model de staging migrou de `codigo_cnes` (não é mais chave sozinho)
  para uma chave surrogate `id_estabelecimento_competencia`.
- **Etapa 9 (2026-07-12) — 3 marts novos, grãos escolhidos por demanda,
  não por fonte.** Diferente das etapas anteriores (1 mart por fonte),
  estas 3 marts existem porque o frontend pediu uma pergunta específica,
  não porque uma fonte nova chegou:
  - `mart_cobertura_aps_municipio` combina 3 grãos bem diferentes
    (população: 1/município/ano; equipes CNES: 1/equipe; cadastro
    vinculado SISAB: 1/tipo de equipe x situação) na grão "1 por
    município" que o KPI de cobertura pede. Decisão de agregação testada
    contra dado real antes de fixar: dentre as 3 `situacao_equipe`
    (`válidas`/`homologadas`/`todas`) x 2 `pessoas_vinculadas_criterios_ponderacao`
    (com/sem peso) do cadastro vinculado, só `homologadas` sem ponderação
    produz um percentual de cobertura ESF plausível (<=100%) — as outras
    combinações inflam ou descontam o numerador de formas que não
    correspondem a "cobertura populacional simples". `quantidade_equipes_*`
    conta só equipes com `situacao_equipe = 'ativa'` (grupo "EP" não é
    historizado ainda, então "situação" aqui é só o estado na competência
    2025-12, não uma série).
  - `mart_historico_rede_cnes` usa 2 window functions
    (`min`/`max(competencia_date) over (partition by codigo_cnes)` e
    `max(...) over ()` sem partição) pra derivar `situacao_operacional`
    sem precisar de uma segunda passada ou de um model intermediate — a
    lógica cabe inteira numa CTE.
  - `mart_financiamento_saude_uniao` una FNS + Portal da Transparência
    (ao contrário da decisão original de manter FNS/SIOPS separados — aqui
    as duas fontes SÃO a mesma unidade, R$ por lançamento). Achado
    relevante ao comparar as 2 fontes lado a lado: o FNS reporta
    `valor_lancamento` sempre positivo com uma coluna `tipo_operacao`
    (C/D) separada indicando o sinal (confirmado contra dado real: débitos
    têm valor positivo também), enquanto o Portal da Transparência já
    embute o sinal no próprio `valor` (negativo = estorno). Sem normalizar
    os dois pro mesmo formato antes do `union all`, `sum(valor)` no mart
    combinado sub-contaria os débitos do FNS — por isso o model calcula
    `valor` líquido (`-valor_lancamento` quando `tipo_operacao = 'debito'`)
    antes de unir.
- **Etapa 10 (2026-07-13) — join por faixa em vez de de-para 1:1.**
  Diferente dos seeds anteriores (1 código = 1 descrição, join direto),
  `seed_icsap_cid10` mapeia FAIXAS de CID-10 pra grupo — join via
  `between cid_inicio and cid_fim`, não `=`. Isso exigiu normalizar
  `diagnostico_principal` (3 ou 4 caracteres, sem ponto, confirmado
  contra dado real) pro mesmo formato de 4 caracteres das faixas do seed
  antes do join (preenchendo com "0" à direita quando falta o dígito de
  subcategoria) — sem essa normalização, um diagnóstico de 3 caracteres
  como "I20" ficaria fora da faixa "I200-I209" por comparação de string
  (string mais curta ordena antes). A resolução vira um model
  intermediate (`int_sih__diagnostico_icsap`) em vez de um join direto no
  mart, porque o join por faixa é mais caro que um de-para 1:1 — resolver
  1 vez por código distinto (6.056 diagnósticos distintos observados) é
  mais barato que resolver por linha de internação (389.923 registros em
  `fct_internacoes`). Teste de unicidade em
  `int_sih__diagnostico_icsap.diagnostico_principal` funciona como
  verificação de que os 19 grupos da portaria são de fato disjuntos (um
  join por faixa mal disjunto duplicaria diagnósticos) — passou de
  primeira, sem overlap encontrado.
- **Etapa 11 (2026-07-13) — `mart_producao_grupo_municipio` como `table`
  full-refresh, não incremental como `fct_producao_ambulatorial`.** A
  fato de origem é incremental por `competencia_arquivo` justamente
  porque não cabe reprocessar as 99.9M+ linhas a cada carga (ver etapa 5);
  mas o mart agregado só precisa existir 1 vez atualizado — reagregar a
  fato inteira a cada `dbt run` (~2min21s medido) é aceitável pro volume
  atual e mais simples que replicar a lógica incremental por competência
  num mart derivado. Se o volume crescer o suficiente pra esse tempo
  virar um problema, a mesma estratégia da etapa 5
  (`sia_bootstrap_competencia_arquivo` + incremental por `_loaded_at`)
  pode ser copiada aqui — não foi necessário ainda. Grupo SIGTAP resolvido
  com `left(codigo_procedimento, 2)` (não precisou de model
  intermediate como o ICSAP: é um de-para 1:1 direto contra
  `seed_sigtap_grupo`, não um join por faixa).
- **Etapa 12 (2026-07-13) — `mart_alertas_saude` sem regra de meta.**
  Union de 3 CTEs de regra independentes, cada uma já na forma final
  (codigo_regra, severidade, id_municipio, periodo_referencia, evidencia)
  antes do `union all` — desenho deliberado pra facilitar adicionar uma 4ª
  regra depois sem tocar nas existentes. Nenhuma regra usa limiar de
  indicador (cobertura ESF, ICSAP etc.) porque isso dependeria de metas
  oficiais por indicador (demanda "Metas de APS", ainda não implementada);
  inventar um limiar sem fonte verificável violaria a mesma regra de
  proveniência dos seeds. `status` fica sempre `"ativo"` porque o mart é
  full-refresh sem histórico de execuções — não há como marcar um alerta
  antigo como "resolvido" sem guardar estado entre cargas.
- **Etapa 13 (2026-07-13) — `mart_equipe_aps_detalhada` sem coleta nova.**
  `raw_cnes.equipes_aps` (carregado na etapa 9) já tem `codigo_cnes` por
  equipe — o grão que a demanda "Detalhamento da APS" pedia já existia,
  só faltava um mart expondo. Indicador de desempenho por equipe
  específica ficou de fora: a única fonte de indicador coletada (SISAB
  `indicador_desempenho`) publica `visao_equipe` como tipo de equipe
  (eSF/eAP/etc.) agregado por município, não `id_equipe` — juntar 1:1
  exigiria inventar uma correspondência que a fonte não garante.
- **Etapa 14 (2026-07-13) — enriquecimento de `dim_estabelecimento` via
  DEMAS, LEFT JOIN simples (não window function).** Diferente da série
  histórica de `stg_cnes__estabelecimentos` (mesma competência do FTP/DBC,
  window function pra pegar a mais recente), o cadastro do DEMAS
  (`stg_cnes__estabelecimentos_detalhados`) é um snapshot vivo sem
  competência — reflete o momento da carga, sem histórico. Join por
  `codigo_cnes` simples é suficiente; campos ficam `NULL` quando o
  estabelecimento não está nesse cadastro complementar (sem teste
  `not_null` nesses campos, documentado na description do model). A API
  do DEMAS pagina fixo em 20 registros por página sem expor total
  (`limit=1000` retorna só 20) — Rio de Janeiro (~18 mil estabelecimentos)
  levou a maior parte do tempo de carga (~900 páginas).
- **Etapa 15 (2026-07-13) — `raw_ibge.populacao_estimada` virou
  compartilhada entre 2 demandas, exigiu filtro explícito num mart já
  existente.** `run_populacao_estimada_rj.py` expandiu a mesma tabela que
  `mart_cobertura_aps_municipio` já consumia (de 3 pra 92 linhas) — sem
  ajuste, esse mart ganharia 89 linhas extras (só população preenchida,
  o resto `NULL` via `left join`). Corrigido com uma CTE
  `municipios_referencia` (values literal com os 3 ids) e `inner join`
  antes do resto do model, pinando o escopo original independente do que
  a raw compartilhada tiver — mesmo princípio de "cada consumidor declara
  seu próprio escopo" que já apareceu na etapa 9 (não reescalar coleta
  em cascata sem necessidade). `mart_comparacao_municipios_rj` não repete
  esse problema porque é o próprio consumidor do universo expandido — não
  filtra nada.
- **Etapa 16 (2026-07-13) — `status_meta` com só 2 limiares oficiais, sem
  inventar um terceiro nível.** A demanda pedia 3 status ("meta ok",
  "atenção", "crítico"), mas as notas técnicas do Previne Brasil só
  publicam 2 valores por indicador: PARÂMETRO (ideal) e META (pactuado,
  sempre ≤ parâmetro). Em vez de inventar um limiar intermediário pra
  fechar 3 faixas, os 2 valores oficiais já definem 3 faixas sozinhos:
  `>= parametro` (ok), `>= meta e < parametro` (atencao), `< meta`
  (critico) — nenhum número novo, só reaproveitar os 2 já publicados.
  `left join` (não `inner`) na seed porque nem toda linha de
  `stg_sisab__indicador_desempenho` necessariamente tem os 7 números de
  indicador cobertos pela seed (mesmo cuidado que outros joins com seed
  no projeto); `status_meta` fica `NULL` nesse caso, não gera erro no
  teste `accepted_values` (SQL trata `NULL NOT IN (...)` como `NULL`, não
  `TRUE`, então a linha não conta como falha).

## Tabelas raw disponíveis

| Raw | Grão | Volume (Rio, escopo atual) |
| --- | --- | --- |
| `raw_ibge.municipios` | 1 linha por município (Brasil inteiro) | 5.571 |
| `raw_cnes.estabelecimentos` | 1 linha por estabelecimento + competência (série histórica, 12 meses de 2025 desde 2026-07-12 — ver ROADMAP.md) | 228.936 |
| `raw_sia.producao_ambulatorial` | 1 linha por procedimento produzido | 99.927.543 (12 meses/2025, RJ inteiro — não só Rio) |
| `raw_sih.internacoes` | 1 linha por AIH (`numero_aih`) | 352.790 (2025) |
| `raw_sim.obitos` | 1 linha por óbito | 64.704 (2024) |
| `raw_sinasc.nascidos_vivos` | 1 linha por nascimento | 69.427 (2022) |
| `raw_fns.repasses` | 1 linha por lançamento financeiro | 23 (2025) |
| `raw_siops.rreo_anexo14` | 1 linha por conta do demonstrativo | 80 (2025, bimestre 6) |
| `raw_sisab.indicador_desempenho` | 1 linha por indicador x visão de equipe | 18 (2024Q3) |
| `raw_ibge.populacao_estimada` | 1 linha por município + ano | 3 (2025) |
| `raw_cnes.equipes_aps` | 1 linha por equipe de APS | 1.659 (competência 2025-12) |
| `raw_sisab.cadastro_vinculado` | 1 linha por tipo de equipe x situação x critério de ponderação | 54 (competência 202412) |
| `raw_portaltransparencia.recursos_recebidos_saude` | 1 linha por lançamento de recurso recebido | 29 (2025) |

## Camada staging (`stg_<fonte>__<entidade>`)

| Model | Fonte | O que foi feito |
| --- | --- | --- |
| `stg_ibge__municipios` | `raw_ibge.municipios` | ✅ Já vem tipado; passthrough. |
| `stg_cnes__estabelecimentos` | `raw_cnes.estabelecimentos` | ✅ `competencia` → DATE; `tipo_pessoa`, `nivel_dependencia`, `atividade_ensino`, `tipo_gestao`, `vinculo_sus` decodificados inline (verificados contra dado real, `accepted_values` passando); `natureza_juridica` via seed (22/25 códigos); `tipo_unidade` via seed desde 2026-07-05 (24/33 códigos, ver seção de seeds); `esfera_administrativa` fica cru (ver comentário no `.sql`). |
| `stg_sih__internacoes` | `raw_sih.internacoes` | ✅ `data_internacao`/`data_saida` (TEXT `AAAAMMDD`) → DATE; `dias_permanencia`/`valor_total` → INT/NUMERIC; `indicador_obito` → `houve_obito` BOOLEAN. |
| `stg_sim__obitos` | `raw_sim.obitos` | ✅ `data_obito`/`data_nascimento` (TEXT `DDMMAAAA`, confirmado — não `AAAAMMDD`) → DATE; `idade` decodificada em `idade_unidade` + `idade_valor` (código composto do SIM: 1º dígito = unidade; sentinelas "000" e "999" = idade não informada, confirmado contra dado real — 167 óbitos com "999"). |
| `stg_sinasc__nascidos_vivos` | `raw_sinasc.nascidos_vivos` | ✅ `data_nascimento` → DATE; `peso_gramas`, `numero_consultas_prenatal`, `idade_mae` → INT; `apgar1`/`apgar5` → INT com `nullif('')` (359/307 linhas vêm vazias — não medido, confirmado contra dado real, não é falha do collector). |
| `stg_fns__repasses` | `raw_fns.repasses` | ✅ Já vem tipado; `tipo_operacao` C/D → `credito`/`debito`. |
| `stg_siops__rreo_anexo14` | `raw_siops.rreo_anexo14` | ✅ Já vem tipado; passthrough (formato "long" mantido, pivot não valeu a pena pro volume atual — 80 linhas). |
| `stg_sisab__indicador_desempenho` | `raw_sisab.indicador_desempenho` | ✅ `codigo_tipo_indicador` decodificado via seed (`seed_sisab_tipo_indicador`) pro número e descrição oficial do indicador Previne Brasil. |
| `stg_sia__producao_ambulatorial` | `raw_sia.producao_ambulatorial` | ✅ Tipagem básica; `idade_paciente` com `nullif('999')` (sentinela oficial do layout SIA/PA para idade não informada). |
| `stg_ibge__populacao_estimada` | `raw_ibge.populacao_estimada` | ✅ Já vem tipado; passthrough. |
| `stg_cnes__equipes_aps` | `raw_cnes.equipes_aps` | ✅ `codigo_tipo_equipe` decodificado inline pra `sigla_equipe` (eSF/eCR/eAPP/eAP — mesma tipologia do DEMAS); `situacao_equipe` (ativa/desativada) derivada do sentinela `900001` em `competencia_desativacao`. |
| `stg_sisab__cadastro_vinculado` | `raw_sisab.cadastro_vinculado` | ✅ Já vem tipado; `pessoas_vinculadas_criterios_ponderacao` Sim/Não → BOOLEAN. |
| `stg_portaltransparencia__recursos_recebidos` | `raw_portaltransparencia.recursos_recebidos_saude` | ✅ `competencia` (INTEGER AAAAMM) → DATE; passthrough do resto. |

## Seeds (de-para)

Regra de documentação de proveniência em
[CLAUDE.md#seeds-e-dicionários-externos-de-para](CLAUDE.md). Todo seed tem
entrada em `dbt/seeds/_seeds__models.yml` com fonte, data de consulta e
cobertura.

- ✅ `seed_cnes_natureza_juridica.csv` — fonte: Receita Federal, Tabela II
  (consultada 2026-07-04). 22 dos 25 códigos reais confirmados; 4000,
  2305, 2313 (~28% das linhas) ficam de fora, sem fonte verificável
  encontrada — join retorna `NULL` pra eles, de propósito.
- ✅ `seed_sisab_tipo_indicador.csv` — fonte: notas técnicas da
  SAPS/MS linkadas no dataset do DEMAS (consultadas 2026-07-04 via
  `pdftotext`). Os 6 códigos observados no dado real (10-50, 70) mais o 60
  (não observado, incluído por completude) confirmados um a um.
- ✅ `seed_fns_ente_municipio.csv` — fonte: API Fundo a Fundo do FNS,
  confirmada contra a própria API em 2026-07-04 (Rio de Janeiro) e
  2026-07-05 (Paraty, Nova Iguaçu). 3 de 3 (todos os entes no MVP).
- ✅ `seed_cnes_tipo_unidade.csv` — fonte: "CNES - Tabela de Tipo de
  Estabelecimento" (reprodução municipal — Jundiaí/SP — da tabela oficial
  do CNES/DATASUS, cada código citando a Portaria federal que o instituiu),
  consultada em 2026-07-05 via `pdftotext`. A extração de texto divergiu
  entre os modos `-layout` e `-raw` pros códigos 67/68 (ordem de leitura
  ambígua no stream do PDF) — resolvido renderizando a página em imagem
  (`pdftoppm`) e conferindo célula a célula visualmente antes de
  transcrever, não só grep pelo código. Cobertura: 24 dos 33 códigos
  distintos observados em raw_cnes.estabelecimentos (Rio de Janeiro,
  Paraty, Nova Iguaçu) confirmados contra a tabela, mais 6 códigos da
  tabela não observados no dado atual incluídos por completude (01, 32,
  64, 67, 71, 74). Os códigos 16, 77, 79, 80, 81, 82, 83, 84 e 85 — de
  portarias posteriores a 2011, fora do escopo do documento consultado —
  não têm fonte verificável encontrada e ficam de fora do seed (214 linhas
  de `dim_estabelecimento`, confirmado); join retorna `NULL` pra eles, de
  propósito. `tipo_unidade` em `stg_cnes__estabelecimentos` virou
  `codigo_tipo_unidade` + `descricao_tipo_unidade` (mesmo padrão de
  `natureza_juridica`). `esfera_administrativa` continua crua (fora de
  escopo desta etapa).
- CID-10 (causa_basica do SIM) e CBO (códigos de ocupação do SIA/SIH)
  ficam de fora do MVP — tabelas grandes (milhares de códigos), etapa
  futura se um mart precisar do nome legível.
- ✅ `seed_icsap_cid10.csv` — fonte: Lista Brasileira de Internações por
  Condições Sensíveis à Atenção Primária (Portaria SAS/MS nº 221, de 17 de
  abril de 2008). Não é um dicionário geral de CID-10 (a nota acima sobre
  CID-10 continua valendo — SIM/causa_basica segue sem de-para); é uma
  classificação fechada de 19 grupos com faixas específicas de CID-10 pra
  um indicador (ver ROADMAP.md "Internações ICSAP"). Fonte primária
  (bvsms.saude.gov.br) inacessível no momento da consulta (2026-07-13);
  reconstruída a partir de 2 reproduções institucionais que citam a
  portaria diretamente e batem byte a byte entre si — SES/SC
  (cosemssc.org.br/wp-content/uploads/2022/02/5.pdf) e Telessaúde
  SC/SUS (repositorio.ufsc.br/bitstream/handle/123456789/192027).
  Cobertura: 19 de 19 grupos, todas as faixas publicadas na portaria.
- ✅ `seed_sigtap_grupo.csv` — fonte: wiki oficial do Ministério da Saúde
  (wiki.saude.gov.br/sigtap/index.php/Grupo), cruzada contra o "Anexo I —
  Estrutura da Tabela de Procedimentos Medicamentos OPM do SUS" do
  COSEMS/SC (cosemssc.org.br/wp-content/uploads/2025/03/tabela-do-sigtap.pdf),
  ambas consultadas em 2026-07-13. Domínio fechado de 1 dígito (grupo = 2
  primeiros dígitos do código de 10 do SIGTAP): 9 de 9 grupos cobertos,
  os mesmos 9 observados em `raw_sia.producao_ambulatorial`. Diferente da
  nota acima sobre CID-10/CBO: SIGTAP tem só 9 grupos no nível de
  agregação usado aqui (não é um dicionário de procedimento individual,
  esse sim teria milhares de códigos e continua fora do MVP).

## Camada intermediate (`int_<domínio>__<algo>`)

| Model | Status | O que faz |
| --- | --- | --- |
| `int_ibge__municipio_codigo6` | ✅ Implementado | Bridge `id_municipio` (7 dígitos) ↔ `cod_municipio_ibge6` (6 dígitos, `left(id_municipio::text, 6)`). Reaproveitado por `fct_internacoes`, `fct_obitos`, `fct_nascidos_vivos`, `mart_indicadores_aps`, `fct_producao_ambulatorial` e (desde 2026-07-05) `dim_estabelecimento`. |
| `int_sih__diagnostico_icsap` | ✅ Implementado (2026-07-13) | Resolve cada `diagnostico_principal` distinto de `fct_internacoes` pro grupo ICSAP via join por faixa contra `seed_icsap_cid10`. Reaproveitado por `mart_icsap_municipio`. |

## Camada marts

| Model | Tipo | Grão | Status |
| --- | --- | --- | --- |
| `dim_municipio` | dim | 1 por município | ✅ |
| `dim_estabelecimento` | dim | 1 por `codigo_cnes` (competência mais recente; série completa em `stg_cnes__estabelecimentos`, ver nota 2026-07-12) | ✅ (`id_municipio` via bridge desde 2026-07-05, ver nota abaixo) |
| `fct_internacoes` | fct | 1 por AIH | ✅ |
| `fct_obitos` | fct | 1 por óbito | ✅ |
| `fct_nascidos_vivos` | fct | 1 por nascimento | ✅ |
| `mart_repasses_fns` | mart | 1 por lançamento | ✅ |
| `mart_financiamento_saude_siops` | mart | 1 por conta/coluna do RREO | ✅ |
| `mart_indicadores_aps` | mart | 1 por indicador/visão de equipe | ✅ |
| `fct_producao_ambulatorial` | fct | 1 por procedimento produzido | ✅ |
| `mart_cobertura_aps_municipio` | mart | 1 por município | ✅ (2026-07-12) |
| `mart_icsap_municipio` | mart | 1 por município (residência) + ano | ✅ (2026-07-13) |
| `mart_producao_grupo_municipio` | mart | 1 por município (estabelecimento) + competência + grupo SIGTAP | ✅ (2026-07-13) |
| `mart_historico_rede_cnes` | mart | 1 por `codigo_cnes` + competência | ✅ (2026-07-12) |
| `mart_financiamento_saude_uniao` | mart | 1 por lançamento (FNS + Portal da Transparência) | ✅ (2026-07-12) |

## Testes dbt (124 rodando)

- `unique` + `not_null` na chave de grão de cada fct/dim/seed.
- `relationships` de cada fct/mart para `dim_municipio` (e
  `dim_estabelecimento` onde aplicável — em `fct_internacoes`, com
  `severity: warn` em vez de `error`, porque nem toda internação do ano
  precisa ter o estabelecimento presente no snapshot único do CNES de
  dez/2025).
- `accepted_values` nos campos decodificados inline (CNES) e em
  `idade_unidade` (SIM) — pegou 2 bugs reais durante a implementação (ver
  histórico do commit): o sentinela SIM "999" não estava na lista aceita,
  e 2 colunas do SINASC (`apgar1`/`apgar5`) vinham vazias em vez de `NULL`
  e quebravam o CAST.

## Ordem de implementação (todas as etapas concluídas)

1. ✅ scaffold + `stg_ibge__municipios` + `dim_municipio`.
2. ✅ `stg_cnes__estabelecimentos` + `dim_estabelecimento` + seed de
   natureza jurídica.
3. ✅ `int_ibge__municipio_codigo6`.
4. ✅ `stg_sih__internacoes` + `fct_internacoes`.
5. ✅ `stg_sia__producao_ambulatorial` + `fct_producao_ambulatorial` —
   concluída em 2026-07-05, numa máquina nova (setup do zero: venv,
   `astro dev start`, collectors, dbt), que recebeu o handoff da máquina
   anterior. Resolução dos pontos em aberto do handoff:
   - **`_loaded_at` varia por competência**, confirmado direto no código
     (`repository.py`: `substituir_producao_ambulatorial` gera um novo
     `datetime.now()` a cada chamada, uma por mês) — não precisou de query
     para confirmar.
   - **Índice criado**: `ix_producao_ambulatorial_competencia_arquivo` em
     `raw_sia.producao_ambulatorial(competencia_arquivo)`, adicionado em
     `ensure_schema()` (`include/collectors/sia/repository.py`) — usado
     tanto pelo delete+insert do collector quanto pelos chunks do dbt.
   - **Var de bootstrap implementada**: `sia_bootstrap_competencia_arquivo`
     em `fct_producao_ambulatorial.sql`. Quando setada, filtra
     `stg_sia__producao_ambulatorial` por aquela competência
     independentemente de `is_incremental()` (ao contrário da ideia
     original do handoff de ativar só quando `not is_incremental()` — setar
     sempre que a var existir é mais simples e previsível: cada uma das 12
     chamadas de `dbt run` fica restrita a 1 partição, sem depender de
     estado). Sem a var, volta ao filtro incremental normal por
     `_loaded_at`, usado nas cargas seguintes do SIA.
   - **Execução**: 12 chamadas de `dbt run --select fct_producao_ambulatorial
     --vars '{sia_bootstrap_competencia_arquivo: <AAAAMM>}'`, uma por mês,
     ~30-55s cada (~9,5 min no total) — sem o estouro de WAL que travou a
     máquina antiga; espaço em disco ficou estável (~130GB livres o tempo
     todo, máquina com 236GB no total).
   - **Row count confirmado**: `fct_producao_ambulatorial` bate exatamente
     com `raw_sia.producao_ambulatorial` — **99.927.543 linhas**.
   - `dbt test` completo (71 testes): **70 PASS + 1 WARN esperado**
     (`relationships_fct_producao_ambulatorial...dim_estabelecimento`,
     mesma razão do WARN já existente em `fct_internacoes` — CNES é
     snapshot único de dez/2025, não cobre todo `codigo_cnes` do ano
     inteiro do SIA).
   - Os 2 arquivos de scratch mencionados no handoff (`.scratch_date.txt`,
     `.scratch_pgstat.txt`) não existiam nesta máquina (clone limpo do
     git) — nada a apagar.
6. ✅ `stg_sim__obitos` + `fct_obitos`, `stg_sinasc__nascidos_vivos` +
   `fct_nascidos_vivos`.
7. ✅ `stg_fns__repasses` + `stg_siops__rreo_anexo14` +
   `mart_repasses_fns` + `mart_financiamento_saude_siops`.
8. ✅ `stg_sisab__indicador_desempenho` + seed de indicadores +
   `mart_indicadores_aps`.

Todas as 8 fontes têm pelo menos 1 model rodando local — orquestração via
DAGs Airflow chamando `dbt run`/`dbt test` é o próximo passo em aberto.

## DAG dbt (implementada em 2026-07-05)

`dags/dbt_transform.py` — 3 tasks (`dbt_seed >> dbt_run >> dbt_test`),
disparo manual (`schedule=None`), mesmo padrão das DAGs de coleta.
Validada de ponta a ponta dentro do container real do Airflow (`docker
exec ... airflow tasks test dbt_transform <task>` para as 3 tasks).

Decisões tomadas (resolvendo os pontos que ficaram em aberto):

- **Isolamento de dependências**: nem `astronomer-cosmos` nem
  `PythonVirtualenvOperator` — usa `@task.bash` (decorator nativo do
  `airflow.sdk`) chamando um venv dedicado (`.dbt_venv/`, fora do repo via
  `.gitignore`) criado com `uv` (já presente na imagem `astrocrpublic`,
  confirmado — não precisou instalar nada a mais). Cada task garante o
  venv antes de rodar (`test -x .dbt_venv/bin/dbt || uv venv ... && uv pip
  install dbt-core dbt-postgres`) — criado só na 1ª execução (~5s via uv),
  reaproveitado depois. Mais simples que cosmos (sem dependência nova) e
  mais rápido que recriar venv a cada run (padrão do
  `PythonVirtualenvOperator`).
- **Granularidade**: 1 DAG com 3 tasks (seed/run/test), sem 1 task por
  model — como previsto.
- **Caminhos absolutos obrigatórios**: `@task.bash` roda o comando num cwd
  próprio (tmpdir do `SubprocessHook`), não em `/usr/local/airflow` —
  descoberto ao testar (`Error: Invalid value for '--project-dir': Path
  'dbt' does not exist`). `DBT_PROJECT_DIR`/`DBT_PROFILES_DIR`/
  `DBT_VENV_DIR` usam `/usr/local/airflow/...` fixo, não caminho relativo.
- **Gatilho**: manual, sem `TriggerDagRunOperator` acoplando às DAGs de
  coleta — como previsto, escopo delas ainda é fixo/hardcoded.
- **SIA sem tratamento especial**: confirmado que um `dbt run` normal roda
  como no-op (`INSERT 0 0`) quando não há `_loaded_at` novo; a var de
  bootstrap do backfill (etapa 5) não entra na DAG.
- **`profiles.yml`**: nenhum ajuste necessário, `env_var('POSTGRES_*')` já
  resolve para o hostname `postgres` dentro do container (via
  `docker-compose.override.yml`).
