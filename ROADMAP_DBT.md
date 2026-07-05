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

Rodado de ponta a ponta (`dbt seed && dbt run && dbt test`):
**19 models, 3 seeds, 71 testes — 70 PASS + 1 WARN esperado (relationship
`fct_producao_ambulatorial` → `dim_estabelecimento`, mesma razão do WARN já
existente em `fct_internacoes`: o CNES é um snapshot único de dez/2025, não
cobre todo `codigo_cnes` referenciado no ano inteiro do SIA).

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
| `stg_sia__producao_ambulatorial` | `raw_sia.producao_ambulatorial` | ✅ Tipagem básica; `idade_paciente` com `nullif('999')` (sentinela oficial do layout SIA/PA para idade não informada). |

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
| `int_ibge__municipio_codigo6` | ✅ Implementado | Bridge `id_municipio` (7 dígitos) ↔ `cod_municipio_ibge6` (6 dígitos, `left(id_municipio::text, 6)`). Reaproveitado por `fct_internacoes`, `fct_obitos`, `fct_nascidos_vivos`, `mart_indicadores_aps` e `fct_producao_ambulatorial`. |

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
| `fct_producao_ambulatorial` | fct | 1 por procedimento produzido | ✅ |

## Testes dbt (71 rodando)

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
