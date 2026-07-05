with estabelecimentos as (

    select * from {{ ref('stg_cnes__estabelecimentos') }}

)

select
    codigo_cnes,
    -- Código IBGE de 6 dígitos sem dígito verificador (mesmo padrão de
    -- SIA/SIH/SIM/SINASC). Resolver pra dim_municipio.id_municipio (7
    -- dígitos) fica pra int_saude__eventos_com_municipio, quando o
    -- primeiro fato que precisar disso for implementado (ver
    -- ROADMAP_DBT.md) — não antes.
    cod_municipio_ibge6,
    tipo_pessoa,
    nivel_dependencia,
    tipo_unidade,
    natureza_organizacao,
    codigo_natureza_juridica,
    descricao_natureza_juridica,
    atividade_ensino,
    tem_vinculo_sus,
    tipo_gestao,
    esfera_administrativa,
    competencia_date as competencia_cadastro

from estabelecimentos
