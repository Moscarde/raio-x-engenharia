{{
    config(
        materialized='incremental',
        unique_key='competencia_arquivo',
        incremental_strategy='delete+insert',
        on_schema_change='sync_all_columns'
    )
}}

-- Incremental por competencia_arquivo, não table full-refresh: a fonte tem
-- 99.9M+ linhas/ano e cresce a cada carga do SIA (ver ROADMAP_DBT.md,
-- etapa 5). `unique_key` aqui é a partição (competência do arquivo
-- buscado), não uma chave de linha única — mesma semântica do
-- delete+insert já usado em raw_sia (CLAUDE.md#idempotência): a cada dbt
-- run, só as partições com `_loaded_at` mais recente que o já
-- materializado são apagadas e reinseridas.

with producao as (

    select * from {{ ref('stg_sia__producao_ambulatorial') }}

    {% if is_incremental() %}
    where _loaded_at > (select max(_loaded_at) from {{ this }})
    {% endif %}

),

municipios as (

    select * from {{ ref('int_ibge__municipio_codigo6') }}

)

select
    p.codigo_cnes_estabelecimento,
    mun_estab.id_municipio as id_municipio_estabelecimento,
    mun_pac.id_municipio as id_municipio_paciente,
    p.competencia_date,
    p.competencia_arquivo,
    p.codigo_procedimento,
    p.codigo_cbo,
    p.carater_atendimento,
    p.idade_paciente,
    p.sexo_paciente,
    p.raca_cor_paciente,
    p.quantidade_produzida,
    p.quantidade_aprovada,
    p.valor_produzido,
    p.valor_aprovado,
    p.origem_documento,
    p._loaded_at

from producao p
left join municipios mun_estab
    on p.cod_municipio_ibge6_estabelecimento = mun_estab.cod_municipio_ibge6
left join municipios mun_pac
    on p.cod_municipio_ibge6_paciente = mun_pac.cod_municipio_ibge6
