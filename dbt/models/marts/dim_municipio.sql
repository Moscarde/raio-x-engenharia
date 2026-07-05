with municipios as (

    select * from {{ ref('stg_ibge__municipios') }}

)

select
    id_municipio,
    nome_municipio,
    id_microrregiao,
    nome_microrregiao,
    id_mesorregiao,
    nome_mesorregiao,
    id_uf,
    sigla_uf,
    nome_uf,
    id_regiao,
    sigla_regiao,
    nome_regiao

from municipios
