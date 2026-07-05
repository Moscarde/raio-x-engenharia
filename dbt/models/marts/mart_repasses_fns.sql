-- Mart separado de mart_financiamento_saude_siops (não unificados num só
-- "financiamento_saude"): FNS é ledger transacional (crédito/débito em
-- R$) e SIOPS é demonstrativo fiscal agregado com contas em R$ e também
-- percentuais — somar as duas fontes numa mesma tabela misturaria
-- unidades incompatíveis. Ver ROADMAP_DBT.md.

with repasses as (

    select * from {{ ref('stg_fns__repasses') }}

),

municipios as (

    select * from {{ ref('seed_fns_ente_municipio') }}

)

select
    r.id_lancamento,
    m.id_municipio,
    r.cnpj_ente_solicitante,
    r.nome_ente_solicitante,
    r.tipo_operacao,
    r.descricao_lancamento,
    r.data_lancamento,
    r.valor_lancamento,
    date_part('year', r.data_lancamento)::int as ano

from repasses r
left join municipios m
    on r.cnpj_ente_solicitante = m.cnpj_ente
