with indicadores as (

    select * from {{ source('raw_sisab', 'indicador_desempenho') }}

),

tipo_indicador as (

    select * from {{ ref('seed_sisab_tipo_indicador') }}

)

select
    i.uf,
    i.municipio,
    -- TEXT pra casar com cod_municipio_ibge6 (int_ibge__municipio_codigo6),
    -- que é sempre TEXT por vir de left(id_municipio::text, 6).
    i.codigo_municipio::text as codigo_municipio,
    i.quadrimestre,
    i.competencia,
    i.codigo_tipo_indicador,
    ti.numero_indicador,
    ti.descricao_indicador,
    i.visao_equipe,
    i.numerador,
    i.denominador_utilizador,
    i.denominador_identificado,
    i.denominador_estimado,
    i.percentual,
    i.percentual_quadrimestre,
    i.cadastro,
    i.base_externa,
    i.populacao,
    i._loaded_at,
    i._source_url

from indicadores i
left join tipo_indicador ti
    on i.codigo_tipo_indicador = ti.codigo_tipo_indicador
