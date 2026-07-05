with estabelecimentos as (

    select * from {{ ref('stg_cnes__estabelecimentos') }}

),

municipios as (

    select * from {{ ref('int_ibge__municipio_codigo6') }}

)

select
    e.codigo_cnes,
    -- id_municipio (7 dígitos) via bridge int_ibge__municipio_codigo6 —
    -- mesmo padrão já usado por fct_internacoes, fct_obitos,
    -- fct_nascidos_vivos, mart_indicadores_aps e
    -- fct_producao_ambulatorial (ver ROADMAP_DBT.md). cod_municipio_ibge6
    -- (6 dígitos) mantido também, para consumidores que já dependem dele.
    mun.id_municipio,
    e.cod_municipio_ibge6,
    e.tipo_pessoa,
    e.nivel_dependencia,
    e.codigo_tipo_unidade,
    e.descricao_tipo_unidade,
    e.natureza_organizacao,
    e.codigo_natureza_juridica,
    e.descricao_natureza_juridica,
    e.atividade_ensino,
    e.tem_vinculo_sus,
    e.tipo_gestao,
    e.esfera_administrativa,
    e.competencia_date as competencia_cadastro

from estabelecimentos e
left join municipios mun
    on e.cod_municipio_ibge6 = mun.cod_municipio_ibge6
