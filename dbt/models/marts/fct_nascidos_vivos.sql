with nascidos_vivos as (

    select * from {{ ref('stg_sinasc__nascidos_vivos') }}

),

municipios as (

    select * from {{ ref('int_ibge__municipio_codigo6') }}

)

select
    n.codigo_cnes_estabelecimento,
    mun_nasc.id_municipio as id_municipio_nascimento,
    mun_res.id_municipio as id_municipio_residencia,
    n.data_nascimento,
    n.sexo,
    n.raca_cor,
    n.peso_gramas,
    n.semanas_gestacao_faixa,
    n.tipo_parto,
    n.apgar1,
    n.apgar5,
    n.numero_consultas_prenatal,
    n.idade_mae,
    n.escolaridade_mae,
    n._reference_year

from nascidos_vivos n
left join municipios mun_nasc
    on n.cod_municipio_ibge6_nascimento = mun_nasc.cod_municipio_ibge6
left join municipios mun_res
    on n.cod_municipio_ibge6_residencia = mun_res.cod_municipio_ibge6
