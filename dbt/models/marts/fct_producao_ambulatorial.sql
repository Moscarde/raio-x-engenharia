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

-- A primeira materialização não pode ler as 99.9M+ linhas de uma vez: já
-- travou 2x numa máquina anterior por estourar o disco com WAL de uma
-- transação única (ver ROADMAP_DBT.md, handoff da etapa 5). A var
-- `sia_bootstrap_competencia_arquivo` permite popular 1 competência por vez
-- (12 chamadas de `dbt run`, uma por mês) — enquanto ela estiver setada, o
-- filtro por competência prevalece mesmo depois que a tabela já existir
-- (is_incremental() vira true a partir da 2ª chamada). Sem a var, o model
-- volta ao comportamento incremental normal por `_loaded_at`, usado nas
-- cargas seguintes do SIA depois que o backfill inicial terminar.

with producao as (

    select * from {{ ref('stg_sia__producao_ambulatorial') }}

    {% if var('sia_bootstrap_competencia_arquivo', none) is not none %}
    where competencia_arquivo = '{{ var("sia_bootstrap_competencia_arquivo") }}'
    {% elif is_incremental() %}
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
