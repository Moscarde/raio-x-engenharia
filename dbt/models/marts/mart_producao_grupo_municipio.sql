-- Produção ambulatorial agregada por município (do estabelecimento),
-- competência e grupo SIGTAP — pré-agregado pra não exigir somar a fato
-- detalhada (99.9M+ linhas) em tempo de request. Ver ROADMAP.md "Produção
-- por grupo".

with producao as (

    select * from {{ ref('fct_producao_ambulatorial') }}

),

grupos as (

    select * from {{ ref('seed_sigtap_grupo') }}

),

producao_com_grupo as (

    select
        p.id_municipio_estabelecimento,
        p.competencia_date,
        -- 2 primeiros dígitos do código de 10 dígitos do SIGTAP
        -- (GG.SS.FF.PPPP) — confirmado contra dado real, único formato
        -- observado em codigo_procedimento (sempre 10 caracteres).
        left(p.codigo_procedimento, 2) as codigo_grupo,
        p.quantidade_produzida,
        p.quantidade_aprovada,
        p.valor_produzido,
        p.valor_aprovado

    from producao p
    where p.id_municipio_estabelecimento is not null

)

select
    p.id_municipio_estabelecimento as id_municipio,
    p.competencia_date,
    p.codigo_grupo,
    g.descricao_grupo,
    count(*) as quantidade_registros,
    sum(p.quantidade_produzida) as quantidade_produzida,
    sum(p.quantidade_aprovada) as quantidade_aprovada,
    sum(p.valor_produzido) as valor_produzido,
    sum(p.valor_aprovado) as valor_aprovado

from producao_com_grupo p
left join grupos g
    on p.codigo_grupo = g.codigo_grupo
group by
    p.id_municipio_estabelecimento,
    p.competencia_date,
    p.codigo_grupo,
    g.descricao_grupo
