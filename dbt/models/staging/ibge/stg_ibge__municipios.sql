with municipios_origem as (

    select * from {{ source('raw_ibge', 'municipios') }}

),

municipios_tipados as (

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
        nome_regiao,
        _loaded_at,
        _source_url

    from municipios_origem

)

select * from municipios_tipados
