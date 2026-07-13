-- status_meta é derivado só de limiares oficiais do Previne Brasil
-- (seed_previne_brasil_meta: parâmetro = valor ideal, meta = valor
-- pactuado, ambos das notas técnicas SAPS/MS) — ver ROADMAP.md "Metas de
-- APS". Nenhum limiar é inventado: os 3 níveis usam só parametro_percentual
-- e meta_percentual, que sempre satisfazem parametro >= meta na fonte.

with indicadores as (

    select * from {{ ref('stg_sisab__indicador_desempenho') }}

),

municipios as (

    select * from {{ ref('int_ibge__municipio_codigo6') }}

),

metas as (

    select * from {{ ref('seed_previne_brasil_meta') }}

)

select
    m.id_municipio,
    i.quadrimestre,
    i.competencia,
    i.numero_indicador,
    i.descricao_indicador,
    i.visao_equipe,
    i.numerador,
    i.denominador_utilizador,
    i.percentual,
    i.percentual_quadrimestre,
    i.populacao,
    mt.parametro_percentual,
    mt.meta_percentual,
    case
        when i.percentual_quadrimestre >= mt.parametro_percentual then 'ok'
        when i.percentual_quadrimestre >= mt.meta_percentual then 'atencao'
        when i.percentual_quadrimestre is not null then 'critico'
    end as status_meta

from indicadores i
left join municipios m
    on i.codigo_municipio = m.cod_municipio_ibge6
left join metas mt
    on i.numero_indicador = mt.numero_indicador
