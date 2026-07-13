with recursos as (

    select * from {{ source('raw_portaltransparencia', 'recursos_recebidos_saude') }}

),

recursos_tipados as (

    select
        competencia,
        -- Ano/mês em INTEGER (ex. 202508) -> DATE no dia 1, mesmo padrão
        -- de leitura de outras competências mensais do projeto.
        to_date(competencia::text, 'YYYYMM') as competencia_date,
        cnpj_favorecido,
        nome_favorecido,
        tipo_favorecido,
        municipio_favorecido,
        sigla_uf_favorecido,
        codigo_ug,
        nome_ug,
        codigo_orgao,
        nome_orgao,
        codigo_orgao_superior,
        nome_orgao_superior,
        -- Pode ser negativo (estorno/devolução) — ver comentário em
        -- include/collectors/portaltransparencia/parser.py.
        valor,
        _loaded_at,
        _source_url,
        _reference_year

    from recursos

)

select * from recursos_tipados
