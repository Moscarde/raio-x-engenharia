-- Resolve cada diagnostico_principal distinto de fct_internacoes pro grupo
-- da Lista Brasileira de ICSAP (Portaria SAS/MS 221/2008, ver
-- seed_icsap_cid10 e ROADMAP_DBT.md), 1 linha por código — reaproveitado
-- por mart_icsap_municipio sem repetir o join por faixa em cada consumidor.

with diagnosticos as (

    select distinct diagnostico_principal
    from {{ ref('fct_internacoes') }}

),

diagnosticos_normalizados as (

    select
        diagnostico_principal,
        -- SIH grava o CID-10 sem ponto, com 3 (só categoria) ou 4
        -- caracteres (categoria + subcategoria) — confirmado contra dado
        -- real, únicos comprimentos observados em diagnostico_principal.
        -- Preenche com "0" à direita quando falta o dígito de
        -- subcategoria, pro join por faixa funcionar (seed_icsap_cid10 usa
        -- o mesmo preenchimento na ponta inicial de cada faixa).
        case
            when length(diagnostico_principal) = 3 then diagnostico_principal || '0'
            else diagnostico_principal
        end as diagnostico_normalizado

    from diagnosticos

),

icsap as (

    select * from {{ ref('seed_icsap_cid10') }}

)

select
    d.diagnostico_principal,
    i.grupo_icsap,
    i.descricao_grupo as descricao_grupo_icsap,
    (i.grupo_icsap is not null) as is_icsap

from diagnosticos_normalizados d
left join icsap i
    on d.diagnostico_normalizado between i.cid_inicio and i.cid_fim
