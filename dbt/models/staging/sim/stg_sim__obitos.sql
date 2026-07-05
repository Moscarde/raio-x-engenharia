with obitos as (

    select * from {{ source('raw_sim', 'obitos') }}

),

obitos_tipados as (

    select
        origem_informacao,
        codigo_cnes_estabelecimento,
        cod_municipio_ibge6_ocorrencia,
        cod_municipio_ibge6_residencia,
        to_date(data_obito, 'DDMMYYYY') as data_obito,
        to_date(data_nascimento, 'DDMMYYYY') as data_nascimento,

        -- IDADE é um código composto (fonte: dicionário de variáveis do
        -- SIM, PCDaS/Fiocruz, consultado em 2026-07-04): 1º dígito é a
        -- unidade, os 2 seguintes são a quantidade nessa unidade. "000" e
        -- "999" são sentinelas de "idade ignorada/não informada"
        -- (confirmado contra dado real: 167 óbitos do Rio/2024 com
        -- idade="999") — em ambos, idade_valor vira NULL também, não "99".
        -- Ver ROADMAP_DBT.md#seeds-de-para para a fonte completa.
        case
            when idade in ('000', '999') then 'nao_informado'
            when left(idade, 1) = '0' then 'minutos'
            when left(idade, 1) = '1' then 'horas'
            when left(idade, 1) = '2' then 'dias'
            when left(idade, 1) = '3' then 'meses'
            when left(idade, 1) = '4' then 'anos'
            when left(idade, 1) = '5' then 'anos_mais_de_100'
            else 'nao_informado'
        end as idade_unidade,
        case
            when idade in ('000', '999') then null
            else right(idade, 2)::int
        end as idade_valor,

        sexo,
        raca_cor,
        estado_civil,
        escolaridade,
        local_ocorrencia,
        causa_basica,
        circunstancia_obito,
        assistencia_medica,
        _loaded_at,
        _source_file,
        _reference_year

    from obitos

)

select * from obitos_tipados
