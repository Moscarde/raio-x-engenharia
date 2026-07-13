with populacao_origem as (

    select * from {{ source('raw_ibge', 'populacao_estimada') }}

),

populacao_tipada as (

    select
        id_municipio,
        nome_municipio,
        ano_referencia,
        populacao_estimada,
        _loaded_at,
        _source_url

    from populacao_origem

)

select * from populacao_tipada
