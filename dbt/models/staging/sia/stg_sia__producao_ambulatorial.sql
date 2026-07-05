with producao as (

    select * from {{ source('raw_sia', 'producao_ambulatorial') }}

),

producao_tipada as (

    select
        codigo_cnes_estabelecimento,
        cod_municipio_ibge6_estabelecimento,
        cod_municipio_ibge6_paciente,
        competencia,
        to_date(competencia, 'YYYYMM') as competencia_date,
        -- Competência do arquivo buscado (chave de partição do delete+insert
        -- em raw_sia, não a competência real da linha) — usada pelo
        -- fct_producao_ambulatorial para reprocessar só a partição alterada
        -- em vez da tabela inteira a cada dbt run (ver ROADMAP_DBT.md).
        competencia_arquivo,
        codigo_procedimento,
        codigo_cbo,
        carater_atendimento,
        -- "999" é o sentinela oficial do layout do SIA/PA pra idade não
        -- informada (confirmado contra dado real: 118.514 linhas em
        -- dez/2025); demais valores são idade em anos (0-127, inclui
        -- pacientes reais acima de 100 anos).
        nullif(idade_paciente, '999')::int as idade_paciente,
        sexo_paciente,
        raca_cor_paciente,
        quantidade_produzida::int as quantidade_produzida,
        quantidade_aprovada::int as quantidade_aprovada,
        valor_produzido::numeric as valor_produzido,
        valor_aprovado::numeric as valor_aprovado,
        origem_documento,
        _loaded_at,
        _source_file,
        _reference_year,
        _reference_month

    from producao

)

select * from producao_tipada
