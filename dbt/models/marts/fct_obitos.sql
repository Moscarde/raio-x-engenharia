with obitos as (

    select * from {{ ref('stg_sim__obitos') }}

),

municipios as (

    select * from {{ ref('int_ibge__municipio_codigo6') }}

)

select
    o.codigo_cnes_estabelecimento,
    mun_ocor.id_municipio as id_municipio_ocorrencia,
    mun_res.id_municipio as id_municipio_residencia,
    o.data_obito,
    o.data_nascimento,
    o.idade_unidade,
    o.idade_valor,
    o.sexo,
    o.raca_cor,
    o.estado_civil,
    o.escolaridade,
    o.local_ocorrencia,
    o.causa_basica,
    o.circunstancia_obito,
    o.assistencia_medica,
    o._reference_year

from obitos o
left join municipios mun_ocor
    on o.cod_municipio_ibge6_ocorrencia = mun_ocor.cod_municipio_ibge6
left join municipios mun_res
    on o.cod_municipio_ibge6_residencia = mun_res.cod_municipio_ibge6
