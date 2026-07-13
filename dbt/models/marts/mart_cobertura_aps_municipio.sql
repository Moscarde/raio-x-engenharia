-- Consolida 3 fontes de grãos bem diferentes (1 por município/ano, 1 por
-- equipe, 1 por tipo de equipe x situação) na grão "1 por município" que a
-- demanda do frontend pede (KPIs de cobertura APS e equipes ESF,
-- comparações per capita). Cada fonte preserva sua própria competência de
-- referência (populacao/CNES/SISAB não coincidem no tempo) — ver
-- ROADMAP.md "Cobertura APS e equipes ESF".

-- raw_ibge.populacao_estimada deixou de ser exclusiva dos 3 municípios de
-- referência (2026-07-13): run_populacao_estimada_rj.py passou a carregar
-- os 92 municípios do RJ inteiro, pra alimentar mart_comparacao_municipios_rj
-- ("Comparação entre pares", ver ROADMAP.md). Sem este filtro, este mart
-- ganharia 89 linhas extras com equipes/cobertura NULL (só população
-- preenchida) — o filtro pina o escopo original deste mart nos 3
-- municípios de referência, independente do que a tabela raw tiver.
with municipios_referencia as (

    select * from (values (3304557), (3303807), (3303500)) as t (id_municipio)

),

populacao as (

    select p.* from {{ ref('stg_ibge__populacao_estimada') }} p
    inner join municipios_referencia r on p.id_municipio = r.id_municipio

),

municipios as (

    select * from {{ ref('int_ibge__municipio_codigo6') }}

),

equipes as (

    select * from {{ ref('stg_cnes__equipes_aps') }}

),

equipes_agregadas as (

    select
        cod_municipio_ibge6,
        max(competencia) as competencia_equipes_cnes,
        count(*) filter (
            where sigla_equipe = 'eSF' and situacao_equipe = 'ativa'
        ) as quantidade_equipes_esf_ativas,
        count(*) filter (
            where situacao_equipe = 'ativa'
        ) as quantidade_equipes_aps_ativas_total

    from equipes
    group by cod_municipio_ibge6

),

cadastro_vinculado as (

    select * from {{ ref('stg_sisab__cadastro_vinculado') }}

),

cobertura_esf as (

    select
        codigo_municipio_ibge,
        max(competencia_referencia) as competencia_cadastro_vinculado,
        -- "homologadas" é o cadastro aprovado pra cofinanciamento (mesmo
        -- conceito usado pelo Previne Brasil); sem ponderação (bruto, não
        -- ajustado por critério de vulnerabilidade) porque o KPI aqui é
        -- cobertura populacional simples, não o cálculo de financiamento.
        -- Confirmado contra dado real: essa combinação é a única, entre as
        -- 3 situações e 2 critérios de ponderação disponíveis, que produz
        -- um percentual de cobertura plausível (<=100%) pro Rio de Janeiro.
        sum(pessoas_vinculadas_equipe_municipio) filter (
            where sigla_equipe = 'eSF'
              and situacao_equipe = 'homologadas'
              and pessoas_vinculadas_com_ponderacao = false
        ) as populacao_vinculada_esf_homologada

    from cadastro_vinculado
    group by codigo_municipio_ibge

)

select
    m.id_municipio,
    mun.nome_municipio,
    p.ano_referencia as ano_referencia_populacao,
    p.populacao_estimada,
    e.competencia_equipes_cnes,
    coalesce(e.quantidade_equipes_esf_ativas, 0) as quantidade_equipes_esf_ativas,
    coalesce(e.quantidade_equipes_aps_ativas_total, 0) as quantidade_equipes_aps_ativas_total,
    c.competencia_cadastro_vinculado,
    c.populacao_vinculada_esf_homologada,
    round(
        100.0 * c.populacao_vinculada_esf_homologada / nullif(p.populacao_estimada, 0),
        1
    ) as percentual_cobertura_esf

from populacao p
inner join municipios m
    on p.id_municipio = m.id_municipio
inner join {{ ref('dim_municipio') }} mun
    on p.id_municipio = mun.id_municipio
left join equipes_agregadas e
    on m.cod_municipio_ibge6 = e.cod_municipio_ibge6
left join cobertura_esf c
    on m.cod_municipio_ibge6 = c.codigo_municipio_ibge
