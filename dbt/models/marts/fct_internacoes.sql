with internacoes as (

    select * from {{ ref('stg_sih__internacoes') }}

),

municipios as (

    select * from {{ ref('int_ibge__municipio_codigo6') }}

)

select
    i.numero_aih,
    i.codigo_cnes_estabelecimento,
    mun_estab.id_municipio as id_municipio_estabelecimento,
    mun_pac.id_municipio as id_municipio_paciente,
    i.competencia_date,
    i.codigo_procedimento,
    i.codigo_cbo,
    i.idade_paciente,
    i.sexo_paciente,
    i.raca_cor_paciente,
    i.diagnostico_principal,
    i.valor_total,
    i.data_internacao,
    i.data_saida,
    i.dias_permanencia,
    i.houve_obito

from internacoes i
left join municipios mun_estab
    on i.cod_municipio_ibge6_estabelecimento = mun_estab.cod_municipio_ibge6
left join municipios mun_pac
    on i.cod_municipio_ibge6_paciente = mun_pac.cod_municipio_ibge6
