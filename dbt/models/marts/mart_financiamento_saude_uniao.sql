-- Diferente de mart_financiamento_saude_siops (mantido separado por boa
-- razão — SIOPS é demonstrativo fiscal agregado, unidades incompatíveis
-- com um ledger transacional, ver ROADMAP_DBT.md), FNS e Portal da
-- Transparência SÃO as duas a mesma unidade (R$ por lançamento/recurso
-- recebido), então unificar faz sentido aqui. As duas fontes representam
-- crédito/débito de formas diferentes na origem: o FNS reporta
-- valor_lancamento sempre positivo com um campo tipo_operacao (C/D)
-- separado (confirmado contra dado real: débitos têm valor positivo
-- também); o Portal da Transparência já reporta valor com sinal (negativo
-- = estorno/devolução). Normalizado aqui pra um único `valor` líquido com
-- sinal, débito/estorno sempre negativo — sem essa normalização, somar
-- `valor` das duas fontes junto sub-contaria os débitos do FNS. Ainda
-- assim, a soma das duas fontes NÃO é o total de recursos SUS do
-- município — são só os canais que essas duas APIs federais expõem (ver
-- ROADMAP.md "Financiamento municipal completo").

with repasses_fns as (

    select * from {{ ref('stg_fns__repasses') }}

),

recursos_portal_transparencia as (

    select * from {{ ref('stg_portaltransparencia__recursos_recebidos') }}

),

municipios as (

    select * from {{ ref('seed_fns_ente_municipio') }}

),

fns_normalizado as (

    select
        'fns_fundo_a_fundo' as fonte,
        m.id_municipio,
        r.data_lancamento as data_referencia,
        date_part('year', r.data_lancamento)::int as ano,
        r.tipo_operacao as tipo_lancamento,
        r.descricao_lancamento as descricao_origem,
        case r.tipo_operacao
            when 'debito' then -r.valor_lancamento
            else r.valor_lancamento
        end as valor

    from repasses_fns r
    left join municipios m
        on r.cnpj_ente_solicitante = m.cnpj_ente

),

portal_transparencia_normalizado as (

    select
        'portal_transparencia' as fonte,
        m.id_municipio,
        p.competencia_date as data_referencia,
        p._reference_year as ano,
        case
            when p.valor >= 0 then 'recurso'
            else 'estorno'
        end as tipo_lancamento,
        p.nome_orgao_superior || ' - ' || p.nome_ug as descricao_origem,
        p.valor

    from recursos_portal_transparencia p
    left join municipios m
        on p.cnpj_favorecido = m.cnpj_ente

)

select * from fns_normalizado
union all
select * from portal_transparencia_normalizado
