# Roadmap dbt

Planejamento da camada de transformação (`dbt/`) sobre as 9 tabelas raw já
carregadas (ver [ROADMAP.md](ROADMAP.md)). Convenções de nomeação e schemas
em [CLAUDE.md](CLAUDE.md#convenções-de-nomeação-dbt). Este arquivo é
planejamento — nenhum model foi criado ainda.

## Tabelas raw disponíveis (ponto de partida)

| Raw | Grão | Volume (Rio, escopo atual) |
| --- | --- | --- |
| `raw_ibge.municipios` | 1 linha por município (Brasil inteiro) | 5.571 |
| `raw_cnes.estabelecimentos` | 1 linha por estabelecimento (competência 2025-12) | 17.380 |
| `raw_sia.producao_ambulatorial` | 1 linha por procedimento produzido | ~56M (12 meses/2025) |
| `raw_sih.internacoes` | 1 linha por AIH (`numero_aih`) | 352.790 (2025) |
| `raw_sim.obitos` | 1 linha por óbito | 64.704 (2024) |
| `raw_sinasc.nascidos_vivos` | 1 linha por nascimento | 69.427 (2022) |
| `raw_fns.repasses` | 1 linha por lançamento financeiro | 23 (2025) |
| `raw_siops.rreo_anexo14` | 1 linha por conta do demonstrativo | 80 (2025, bimestre 6) |
| `raw_sisab.indicador_desempenho` | 1 linha por indicador x visão de equipe | 18 (2024Q3) |

## Camada staging (`stg_<fonte>__<entidade>`)

Responsabilidade: tipar campos (as fontes DBC chegam cruas como `TEXT`),
renomear só o que ainda não estiver claro, e aplicar o de-para de código
DATASUS → valor legível quando fizer sentido (ver limitações documentadas
em `docs/COLLECTOR_TEMPLATE.md`). Sem regra de negócio nem agregação.

| Model | Fonte | Observação de tipagem/de-para |
| --- | --- | --- |
| `stg_ibge__municipios` | `raw_ibge.municipios` | Já vem tipado (INTEGER/TEXT); staging é praticamente passthrough. |
| `stg_cnes__estabelecimentos` | `raw_cnes.estabelecimentos` | CAST de `competencia`/`data_atualizacao` (TEXT `AAAAMM`) para tipo de período; de-para de `tipo_unidade`, `natureza_juridica`, `natureza_organizacao` (hoje só código DATASUS) — precisa de seed. |
| `stg_sia__producao_ambulatorial` | `raw_sia.producao_ambulatorial` | CAST de `idade_paciente`, `quantidade_*`, `valor_*` (TEXT → NUMERIC/INT); `competencia` (TEXT `AAAAMM`) → DATE do 1º dia do mês. |
| `stg_sih__internacoes` | `raw_sih.internacoes` | CAST de `data_internacao`/`data_saida` (TEXT `AAAAMMDD`) → DATE; `dias_permanencia`/`valor_total` → INT/NUMERIC; `indicador_obito` → BOOLEAN. |
| `stg_sim__obitos` | `raw_sim.obitos` | CAST de `data_obito`/`data_nascimento` (TEXT `DDMMAAAA`, não `AAAAMMDD` — confirmar formato real) → DATE; **`idade`** usa o formato DATASUS de 3 dígitos (1º dígito = unidade: 0=minutos...5=anos; decodificar aqui, não deixar pra mart). |
| `stg_sinasc__nascidos_vivos` | `raw_sinasc.nascidos_vivos` | CAST de `data_nascimento` (TEXT) → DATE; `peso_gramas`, `apgar1`, `apgar5`, `numero_consultas_prenatal` → INT. |
| `stg_fns__repasses` | `raw_fns.repasses` | Já vem tipado (NUMERIC/DATE) — passthrough; renomear `tipo_operacao` C/D para rótulo (`credito`/`debito`) opcional. |
| `stg_siops__rreo_anexo14` | `raw_siops.rreo_anexo14` | Já vem tipado (NUMERIC) — passthrough. Formato é "long" (1 linha por conta); considerar pivot só na mart, não aqui. |
| `stg_sisab__indicador_desempenho` | `raw_sisab.indicador_desempenho` | Já vem tipado — passthrough; de-para de `codigo_tipo_indicador` (10/20/30/40/50/70) para o nome do indicador Previne Brasil precisa de seed (não está na API). |

## Seeds necessários (de-para)

Nenhum ainda existe em `dbt/seeds/`. Necessários para não deixar código
DATASUS cru na camada staging:

- `seed_cnes_tipo_unidade.csv`, `seed_cnes_natureza_juridica.csv` — de-para de código → descrição (fonte: tabelas de domínio públicas do CNES).
- `seed_sisab_tipo_indicador.csv` — de-para `codigo_tipo_indicador` → nome do indicador Previne Brasil (fonte: `Nota_tecnica_*_indicador_*.pdf` já linkados no dataset do DEMAS, ver ROADMAP.md).
- CID-10 (causa_basica do SIM) e CBO (códigos de ocupação do SIA/SIH) ficam de fora do MVP inicial — tabelas grandes (milhares de códigos), tratar como etapa futura se um mart precisar do nome legível.

## Camada intermediate (`int_<domínio>__<algo>`)

Só onde há junção ou regra de negócio real que mais de uma mart vai
reaproveitar — evitar criar intermediate só por criar (ver CLAUDE.md,
"evitar abstrações prematuras"):

| Model | Junta | Por quê intermediate (não direto na mart) |
| --- | --- | --- |
| `int_saude__eventos_com_municipio` | SIH + SIM + SINASC + SIA, cada um com seu `cod_municipio_ibge6_*` | Resolver o de-para código IBGE 6 dígitos → `dim_municipio` (7 dígitos) uma vez só, reaproveitado por 4 fatos diferentes. |
| `int_saude__financiamento_anual` | FNS + SIOPS, ambos por ano | Unidades de identificação de ente diferentes (CNPJ no FNS, `cod_ibge` no SIOPS) — resolver o de-para uma vez antes da mart consolidada. |

## Camada marts

| Model | Tipo | Grão | Fontes |
| --- | --- | --- | --- |
| `dim_municipio` | dim | 1 por município | `stg_ibge__municipios` |
| `dim_estabelecimento` | dim | 1 por `codigo_cnes` | `stg_cnes__estabelecimentos` |
| `fct_producao_ambulatorial` | fct | 1 por procedimento produzido | `stg_sia__producao_ambulatorial` + `int_saude__eventos_com_municipio` |
| `fct_internacoes` | fct | 1 por AIH | `stg_sih__internacoes` + `int_saude__eventos_com_municipio` |
| `fct_obitos` | fct | 1 por óbito | `stg_sim__obitos` + `int_saude__eventos_com_municipio` |
| `fct_nascidos_vivos` | fct | 1 por nascimento | `stg_sinasc__nascidos_vivos` + `int_saude__eventos_com_municipio` |
| `mart_financiamento_saude` | mart | 1 por ano/ente | `int_saude__financiamento_anual` |
| `mart_indicadores_aps` | mart | 1 por indicador/quadrimestre | `stg_sisab__indicador_desempenho` |

`mart_financiamento_saude` e `mart_indicadores_aps` ficam como mart (não
fct) porque não têm grão transacional — são indicadores/agregados já
calculados na origem, não eventos individuais.

## Testes dbt planejados

- `unique` + `not_null` na chave de grão de cada fct (`numero_aih`,
  `codigo_cnes`, etc.) e de cada dim (`id_municipio`).
- `relationships` de cada fct para `dim_municipio` (e `dim_estabelecimento`
  onde aplicável) — pega quebra de de-para código 6 dígitos → 7 dígitos
  cedo.
- `accepted_values` nos campos decodificados por seed (`tipo_unidade`,
  `codigo_tipo_indicador`), garantindo que todo código do raw tem
  correspondência no seed.

## Ordem de implementação sugerida

1. `dbt/` scaffold (`dbt_project.yml`, `profiles.yml`, schemas
   staging/intermediate/marts) + `stg_ibge__municipios` + `dim_municipio`
   — base de todos os joins por município.
2. `stg_cnes__estabelecimentos` + `dim_estabelecimento` + seeds de
   de-para do CNES.
3. `int_saude__eventos_com_municipio` (assim que o 2º fato precisar dele —
   não antes).
4. `stg_sih__internacoes` + `fct_internacoes` (fonte já 100% completa
   pra 2025, bom primeiro fato pra validar o padrão).
5. `stg_sia__producao_ambulatorial` + `fct_producao_ambulatorial` (maior
   volume — validar performance de materialização, ex. incremental por
   competência).
6. `stg_sim__obitos` + `fct_obitos`, `stg_sinasc__nascidos_vivos` +
   `fct_nascidos_vivos`.
7. `stg_fns__repasses` + `stg_siops__rreo_anexo14` +
   `int_saude__financiamento_anual` + `mart_financiamento_saude`.
8. `stg_sisab__indicador_desempenho` + seed de indicadores +
   `mart_indicadores_aps`.

DAGs Airflow chamando `dbt run`/`dbt test` ficam para depois de pelo menos
a etapa 4 existir (primeiro model + teste rodando local via `dbt run`,
antes de orquestrar).
