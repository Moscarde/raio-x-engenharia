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
- ⬜ Etapa 5 — `stg_sia__producao_ambulatorial` + `fct_producao_ambulatorial`.
  Não bloqueada mais: a carga completa de 2025 do SIA terminou em
  2026-07-05 (99.927.543 linhas, estado RJ inteiro, ver ROADMAP.md) — só
  não foi implementada ainda. Escopo do SIA mudou em 2026-07-04 — agora
  carrega o **estado (UF) inteiro**, não só o Rio (ver ROADMAP.md e
  docs/fontes.md#escopo-de-volume-para-o-mvp); `fct_producao_ambulatorial`
  quando implementada não deve filtrar por município por padrão (ou deve
  expor o filtro como parâmetro da query/mart, não do model).

Rodado de ponta a ponta a cada etapa (`dbt seed && dbt run && dbt test`):
**17 models, 3 seeds, 65 testes, tudo passando.**

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

## Tabelas raw disponíveis

| Raw | Grão | Volume (Rio, escopo atual) |
| --- | --- | --- |
| `raw_ibge.municipios` | 1 linha por município (Brasil inteiro) | 5.571 |
| `raw_cnes.estabelecimentos` | 1 linha por estabelecimento (competência 2025-12) | 17.380 |
| `raw_sia.producao_ambulatorial` | 1 linha por procedimento produzido | 99.927.543 (12 meses/2025, RJ inteiro — não só Rio) |
| `raw_sih.internacoes` | 1 linha por AIH (`numero_aih`) | 352.790 (2025) |
| `raw_sim.obitos` | 1 linha por óbito | 64.704 (2024) |
| `raw_sinasc.nascidos_vivos` | 1 linha por nascimento | 69.427 (2022) |
| `raw_fns.repasses` | 1 linha por lançamento financeiro | 23 (2025) |
| `raw_siops.rreo_anexo14` | 1 linha por conta do demonstrativo | 80 (2025, bimestre 6) |
| `raw_sisab.indicador_desempenho` | 1 linha por indicador x visão de equipe | 18 (2024Q3) |

## Camada staging (`stg_<fonte>__<entidade>`)

| Model | Fonte | O que foi feito |
| --- | --- | --- |
| `stg_ibge__municipios` | `raw_ibge.municipios` | ✅ Já vem tipado; passthrough. |
| `stg_cnes__estabelecimentos` | `raw_cnes.estabelecimentos` | ✅ `competencia` → DATE; `tipo_pessoa`, `nivel_dependencia`, `atividade_ensino`, `tipo_gestao`, `vinculo_sus` decodificados inline (verificados contra dado real, `accepted_values` passando); `natureza_juridica` via seed (22/25 códigos); `tipo_unidade` e `esfera_administrativa` ficam crus (ver seção de seeds e o comentário no `.sql`). |
| `stg_sih__internacoes` | `raw_sih.internacoes` | ✅ `data_internacao`/`data_saida` (TEXT `AAAAMMDD`) → DATE; `dias_permanencia`/`valor_total` → INT/NUMERIC; `indicador_obito` → `houve_obito` BOOLEAN. |
| `stg_sim__obitos` | `raw_sim.obitos` | ✅ `data_obito`/`data_nascimento` (TEXT `DDMMAAAA`, confirmado — não `AAAAMMDD`) → DATE; `idade` decodificada em `idade_unidade` + `idade_valor` (código composto do SIM: 1º dígito = unidade; sentinelas "000" e "999" = idade não informada, confirmado contra dado real — 167 óbitos com "999"). |
| `stg_sinasc__nascidos_vivos` | `raw_sinasc.nascidos_vivos` | ✅ `data_nascimento` → DATE; `peso_gramas`, `numero_consultas_prenatal`, `idade_mae` → INT; `apgar1`/`apgar5` → INT com `nullif('')` (359/307 linhas vêm vazias — não medido, confirmado contra dado real, não é falha do collector). |
| `stg_fns__repasses` | `raw_fns.repasses` | ✅ Já vem tipado; `tipo_operacao` C/D → `credito`/`debito`. |
| `stg_siops__rreo_anexo14` | `raw_siops.rreo_anexo14` | ✅ Já vem tipado; passthrough (formato "long" mantido, pivot não valeu a pena pro volume atual — 80 linhas). |
| `stg_sisab__indicador_desempenho` | `raw_sisab.indicador_desempenho` | ✅ `codigo_tipo_indicador` decodificado via seed (`seed_sisab_tipo_indicador`) pro número e descrição oficial do indicador Previne Brasil. |
| `stg_sia__producao_ambulatorial` | `raw_sia.producao_ambulatorial` | ⬜ Pendente (etapa 5, bloqueada pela carga do SIA). |

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
  confirmada contra a própria API em 2026-07-04. 1 de 1 (único ente no
  MVP).
- ⬜ `seed_cnes_tipo_unidade.csv` — pendente. 31 códigos distintos na
  competência 2025-12; nenhuma fonte oficial machine-readable encontrada
  ainda. `tipo_unidade` fica cru em `stg_cnes__estabelecimentos`.
- CID-10 (causa_basica do SIM) e CBO (códigos de ocupação do SIA/SIH)
  ficam de fora do MVP — tabelas grandes (milhares de códigos), etapa
  futura se um mart precisar do nome legível.

## Camada intermediate (`int_<domínio>__<algo>`)

| Model | Status | O que faz |
| --- | --- | --- |
| `int_ibge__municipio_codigo6` | ✅ Implementado | Bridge `id_municipio` (7 dígitos) ↔ `cod_municipio_ibge6` (6 dígitos, `left(id_municipio::text, 6)`). Reaproveitado por `fct_internacoes`, `fct_obitos`, `fct_nascidos_vivos`, `mart_indicadores_aps` e (quando a etapa 5 sair) `fct_producao_ambulatorial`. |

## Camada marts

| Model | Tipo | Grão | Status |
| --- | --- | --- | --- |
| `dim_municipio` | dim | 1 por município | ✅ |
| `dim_estabelecimento` | dim | 1 por `codigo_cnes` | ✅ |
| `fct_internacoes` | fct | 1 por AIH | ✅ |
| `fct_obitos` | fct | 1 por óbito | ✅ |
| `fct_nascidos_vivos` | fct | 1 por nascimento | ✅ |
| `mart_repasses_fns` | mart | 1 por lançamento | ✅ |
| `mart_financiamento_saude_siops` | mart | 1 por conta/coluna do RREO | ✅ |
| `mart_indicadores_aps` | mart | 1 por indicador/visão de equipe | ✅ |
| `fct_producao_ambulatorial` | fct | 1 por procedimento produzido | ⬜ etapa 5 |

## Testes dbt (65 rodando)

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

## Ordem de implementação (só falta a 5)

1. ✅ scaffold + `stg_ibge__municipios` + `dim_municipio`.
2. ✅ `stg_cnes__estabelecimentos` + `dim_estabelecimento` + seed de
   natureza jurídica.
3. ✅ `int_ibge__municipio_codigo6`.
4. ✅ `stg_sih__internacoes` + `fct_internacoes`.
5. ⬜ `stg_sia__producao_ambulatorial` + `fct_producao_ambulatorial` —
   carga completa 2025 do SIA já terminou (99.927.543 linhas, RJ inteiro);
   model e schema.yml já escritos (incremental por `competencia_arquivo`,
   `delete+insert`), mas nunca terminou de rodar. **Handoff 2026-07-05:**
   desenvolvimento migrado pra outra máquina; o que falta refazer/verificar
   lá antes de seguir:
   - Build travou 2x na primeira materialização: o model lê os 99.9M+
     registros inteiros numa única transação (sem filtro de bootstrap),
     gerou WAL suficiente pra encher o disco raiz da máquina antiga (108GB,
     chegou a 27MB livres) e o processo `dbt run` morreu sem log de erro.
     Não tentar `dbt run` direto na tabela inteira sem checar espaço em
     disco livre antes (regra de bolso: raw da fonte × ~1.5-2 pra WAL/heap
     da tabela nova).
   - Estratégia recomendada (não implementada ainda): popular a tabela em
     chunks por `competencia_arquivo` — dá log de progresso natural (1
     linha por competência) em vez de esperar 2h+ no escuro sem saber se
     travou. Precisa de 2 coisas antes de funcionar bem:
     1. Índice em `raw_sia.producao_ambulatorial(competencia_arquivo)` —
        sem ele, cada chunk faz full scan nos 99.9M registros (pior que
        1 leitura só).
     2. Confirmar se `_loaded_at` varia por competência ou é o mesmo
        timestamp pro batch inteiro (não confirmado — query de
        `group by competencia_arquivo, min/max(_loaded_at)` nunca
        terminou). Se for o mesmo timestamp pra tudo, o filtro
        `is_incremental()` atual (`_loaded_at > max(_loaded_at)`) não
        pega os chunks seguintes sozinho — precisa de uma var de bootstrap
        temporária (ex. `var('bootstrap_competencia')`, ativa só quando
        `not is_incremental()`) pra popular 1 competência por vez.
   - `dbt test` em `stg_sia__producao_ambulatorial` e
     `fct_producao_ambulatorial` nunca rodou (bloqueado pelo build).
   - Row count e timing reais de `fct_producao_ambulatorial` ainda não
     confirmados nesta tabela do roadmap — atualizar quando o build
     terminar.
   - Sobraram 2 arquivos de scratch soltos na raiz do repo de uma sessão
     anterior (`​.scratch_date.txt`, `.scratch_pgstat.txt`, ambos vazios) —
     não fazem parte do projeto, podem ser apagados.
6. ✅ `stg_sim__obitos` + `fct_obitos`, `stg_sinasc__nascidos_vivos` +
   `fct_nascidos_vivos`.
7. ✅ `stg_fns__repasses` + `stg_siops__rreo_anexo14` +
   `mart_repasses_fns` + `mart_financiamento_saude_siops`.
8. ✅ `stg_sisab__indicador_desempenho` + seed de indicadores +
   `mart_indicadores_aps`.

DAGs Airflow chamando `dbt run`/`dbt test` ficam para depois da etapa 5
(todas as fontes com pelo menos 1 model rodando local, antes de
orquestrar).
