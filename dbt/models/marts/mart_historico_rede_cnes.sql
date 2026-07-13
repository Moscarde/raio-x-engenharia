-- Série histórica completa de estabelecimentos do CNES (12 competências de
-- 2025), com um flag de situação operacional derivado da presença/ausência
-- de cada codigo_cnes entre competências — o sinal de abertura/fechamento
-- que a demanda "Histórico de rede CNES" pede (ver ROADMAP.md).
-- Complementa dim_estabelecimento (que só expõe o estado mais recente).

with estabelecimentos as (

    select * from {{ ref('stg_cnes__estabelecimentos') }}

),

municipios as (

    select * from {{ ref('int_ibge__municipio_codigo6') }}

),

estabelecimentos_com_janela as (

    select
        e.*,
        min(e.competencia_date) over (partition by e.codigo_cnes) as primeira_competencia_observada,
        max(e.competencia_date) over (partition by e.codigo_cnes) as ultima_competencia_observada,
        max(e.competencia_date) over () as ultima_competencia_carregada

    from estabelecimentos e

),

estabelecimentos_com_situacao as (

    select
        *,
        -- "possivelmente_encerrado": o estabelecimento não aparece mais nas
        -- competências mais recentes já carregadas — sinal de fechamento
        -- ou de queda temporária do cadastro, não confirmação definitiva
        -- (o CNES não expõe motivo de encerramento no grupo "ST"). Válido
        -- só pra linha da última competência observada de cada
        -- estabelecimento; competências anteriores a essa ficam
        -- "historico".
        case
            when competencia_date < ultima_competencia_observada then 'historico'
            when ultima_competencia_observada = ultima_competencia_carregada then 'ativo'
            else 'possivelmente_encerrado'
        end as situacao_operacional

    from estabelecimentos_com_janela

)

select
    e.id_estabelecimento_competencia,
    e.codigo_cnes,
    m.id_municipio,
    e.competencia_date as competencia_cadastro,
    e.codigo_tipo_unidade,
    e.descricao_tipo_unidade,
    e.tipo_gestao,
    e.primeira_competencia_observada,
    e.ultima_competencia_observada,
    e.situacao_operacional

from estabelecimentos_com_situacao e
left join municipios m
    on e.cod_municipio_ibge6 = m.cod_municipio_ibge6
