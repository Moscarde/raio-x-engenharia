with internacoes as (

    select * from {{ source('raw_sih', 'internacoes') }}

),

internacoes_tipadas as (

    select
        numero_aih,
        codigo_cnes_estabelecimento,
        cod_municipio_ibge6_estabelecimento,
        cod_municipio_ibge6_paciente,
        competencia,
        to_date(competencia, 'YYYYMM') as competencia_date,
        codigo_procedimento,
        codigo_cbo,
        idade_paciente,
        sexo_paciente,
        raca_cor_paciente,
        diagnostico_principal,
        valor_total::numeric as valor_total,
        to_date(data_internacao, 'YYYYMMDD') as data_internacao,
        to_date(data_saida, 'YYYYMMDD') as data_saida,
        dias_permanencia::int as dias_permanencia,
        (indicador_obito = '1') as houve_obito,
        _loaded_at,
        _source_file,
        _reference_year,
        _reference_month

    from internacoes

)

select * from internacoes_tipadas
