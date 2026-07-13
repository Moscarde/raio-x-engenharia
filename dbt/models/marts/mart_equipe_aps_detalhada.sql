-- Detalhamento da APS em grão de equipe/unidade (ver ROADMAP.md
-- "Detalhamento da APS"). Não agrega nada: 1 linha por equipe, com a
-- unidade (CNES) e o município resolvidos, para permitir listagem/radar
-- por equipe/unidade em vez do agregado municipal de
-- mart_cobertura_aps_municipio.
--
-- Deliberadamente NÃO inclui indicadores de desempenho por equipe: a única
-- fonte de indicador de desempenho coletada (SISAB indicador_desempenho,
-- ver stg_sisab__indicador_desempenho) tem `visao_equipe` como o TIPO de
-- equipe (eSF/eAP/etc.) agregado por município, não a equipe individual
-- (`id_equipe`) — não dá pra juntar 1:1 sem inventar uma correspondência
-- equipe-a-equipe que a fonte não garante. "Desempenho localizado" por
-- equipe específica fica de fora até existir uma fonte que publique nesse
-- grão.

with equipes as (

    select * from {{ ref('stg_cnes__equipes_aps') }}

),

estabelecimentos as (

    select * from {{ ref('dim_estabelecimento') }}

),

-- Bridge 6→7 dígitos (mesmo padrão de mart_cobertura_aps_municipio):
-- stg_cnes__equipes_aps só tem o código IBGE de 6 dígitos.
municipio_codigo6 as (

    select * from {{ ref('int_ibge__municipio_codigo6') }}

),

municipios as (

    select * from {{ ref('dim_municipio') }}

)

select
    eq.id_equipe,
    eq.sigla_equipe,
    eq.nome_equipe,
    eq.situacao_equipe,
    eq.competencia,
    eq.codigo_cnes,
    est.descricao_tipo_unidade,
    est.nome_fantasia as nome_unidade,
    est.endereco,
    est.bairro,
    mun.id_municipio,
    mun.nome_municipio,
    eq.id_area,
    eq.nome_area,
    eq.id_segmento,
    eq.descricao_segmento,
    eq.tipo_segmento

from equipes eq
left join estabelecimentos est
    on eq.codigo_cnes = est.codigo_cnes
inner join municipio_codigo6 mc
    on eq.cod_municipio_ibge6 = mc.cod_municipio_ibge6
inner join municipios mun
    on mc.id_municipio = mun.id_municipio
