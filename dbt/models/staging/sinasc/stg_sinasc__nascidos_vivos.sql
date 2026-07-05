with nascidos_vivos as (

    select * from {{ source('raw_sinasc', 'nascidos_vivos') }}

),

nascidos_vivos_tipados as (

    select
        origem_informacao,
        codigo_cnes_estabelecimento,
        cod_municipio_ibge6_nascimento,
        cod_municipio_ibge6_residencia,
        to_date(data_nascimento, 'DDMMYYYY') as data_nascimento,
        sexo,
        raca_cor,
        peso_gramas::int as peso_gramas,
        semanas_gestacao_faixa,
        tipo_parto,
        -- apgar1/apgar5 vêm vazios (não "0") em 359/307 linhas (Rio,
        -- 2022) — não medido/não informado, não é falha do collector.
        nullif(apgar1, '')::int as apgar1,
        nullif(apgar5, '')::int as apgar5,
        numero_consultas_prenatal::int as numero_consultas_prenatal,
        idade_mae::int as idade_mae,
        escolaridade_mae,
        _loaded_at,
        _source_file,
        _reference_year

    from nascidos_vivos

)

select * from nascidos_vivos_tipados
