with indicadores as (

    select * from {{ ref('stg_sisab__indicador_desempenho') }}

),

municipios as (

    select * from {{ ref('int_ibge__municipio_codigo6') }}

)

select
    m.id_municipio,
    i.quadrimestre,
    i.competencia,
    i.numero_indicador,
    i.descricao_indicador,
    i.visao_equipe,
    i.numerador,
    i.denominador_utilizador,
    i.percentual,
    i.percentual_quadrimestre,
    i.populacao

from indicadores i
left join municipios m
    on i.codigo_municipio = m.cod_municipio_ibge6
