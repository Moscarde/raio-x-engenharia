-- Universo de comparação/pareamento pra "Comparação entre pares" (ver
-- ROADMAP.md): 1 linha por município do RJ inteiro (92), não só os 3 de
-- referência. Só 2 atributos, os únicos que este projeto coleta em escala
-- estadual até agora: população (IBGE) e porte de rede (contagem de
-- estabelecimentos do CNES). Não inclui indicador de desempenho (SISAB,
-- ICSAP, financiamento) nem faixa/categoria de porte populacional — essas
-- fontes seguem coletadas só pros 3 municípios de referência; expandir
-- indicador por indicador pros 92 fica pra quando o frontend definir quais
-- indicadores o pareamento realmente precisa (evita coletar em escala sem
-- demanda concreta, ver CLAUDE.md "Evitar abstrações prematuras").

with populacao as (

    select * from {{ ref('stg_ibge__populacao_estimada') }}

),

municipio_codigo6 as (

    select * from {{ ref('int_ibge__municipio_codigo6') }}

),

rede as (

    select * from {{ ref('stg_cnes__rede_porte_municipio') }}

),

municipios_referencia as (

    select * from (values (3304557), (3303807), (3303500)) as t (id_municipio)

)

select
    p.id_municipio,
    p.nome_municipio,
    p.ano_referencia as ano_referencia_populacao,
    p.populacao_estimada,
    r.competencia as competencia_rede_cnes,
    r.quantidade_estabelecimentos as quantidade_estabelecimentos_saude,
    round(
        10000.0 * r.quantidade_estabelecimentos / nullif(p.populacao_estimada, 0),
        2
    ) as estabelecimentos_por_10k_habitantes,
    (ref.id_municipio is not null) as municipio_referencia

from populacao p
inner join municipio_codigo6 mc
    on p.id_municipio = mc.id_municipio
left join rede r
    on mc.cod_municipio_ibge6 = r.cod_municipio_ibge6
left join municipios_referencia ref
    on p.id_municipio = ref.id_municipio
