-- Alertas priorizados por regra, sobre marts já existentes (ver
-- ROADMAP.md "Alertas priorizados"). Deliberadamente NÃO inclui regras
-- baseadas em metas/limiares de indicador (ex.: "cobertura ESF abaixo de
-- X%", "ICSAP acima de Y%") — essas dependem de metas oficiais por
-- indicador (demanda "Metas de APS", ainda não implementada) e inventar
-- um limiar sem fonte verificável violaria a mesma regra de proveniência
-- usada pros seeds (CLAUDE.md#seeds-e-dicionários-externos-de-para).
-- As 3 regras aqui usam ou um limiar legal já codificado (LC 141/2012) ou
-- um sinal estrutural que não depende de limiar nenhum (encerramento de
-- unidade, saldo financeiro negativo).
--
-- `status` é sempre "ativo": este mart é full-refresh sem estado
-- persistido entre execuções, então não há como saber se um alerta de uma
-- carga anterior foi "resolvido" — toda linha presente é um alerta válido
-- no momento da carga atual. Rastrear status ao longo do tempo exigiria
-- guardar histórico de execuções, não implementado ainda.

with municipios as (

    select * from {{ ref('dim_municipio') }}

),

siops as (

    select * from {{ ref('mart_financiamento_saude_siops') }}

),

siops_aplicado_vs_minimo as (

    select
        aplicado.id_municipio,
        aplicado.ano_exercicio,
        aplicado.periodo_bimestre,
        aplicado.valor as percentual_aplicado,
        minimo.valor as percentual_minimo

    from siops aplicado
    inner join siops minimo
        on aplicado.id_municipio = minimo.id_municipio
        and aplicado.ano_exercicio = minimo.ano_exercicio
        and aplicado.periodo_bimestre = minimo.periodo_bimestre
        and aplicado.descricao_conta = minimo.descricao_conta
    where aplicado.descricao_conta = 'Despesas com Ações e Serviços Públicos de Saúde Executadas com Recursos de Impostos'
      and aplicado.coluna = '% Aplicado Até o Bimestre'
      and minimo.coluna = '% Mínimo a Aplicar no Exercício'

),

alerta_siops_abaixo_minimo as (

    select
        'siops_abaixo_minimo_constitucional' as codigo_regra,
        'Aplicação em saúde abaixo do mínimo constitucional (LC 141/2012)' as descricao_regra,
        'alta' as severidade,
        'municipio' as tipo_entidade,
        id_municipio,
        ano_exercicio::text || '-B' || periodo_bimestre::text as periodo_referencia,
        'Aplicado ' || percentual_aplicado::text || '% no exercício, abaixo do mínimo de '
            || percentual_minimo::text || '%' as evidencia

    from siops_aplicado_vs_minimo
    where percentual_aplicado < percentual_minimo

),

rede_cnes as (

    select * from {{ ref('mart_historico_rede_cnes') }}

),

alerta_rede_possivel_encerramento as (

    select
        'rede_cnes_possivel_encerramento' as codigo_regra,
        'Estabelecimentos ausentes das competências mais recentes do CNES (possível encerramento)' as descricao_regra,
        'media' as severidade,
        'municipio' as tipo_entidade,
        id_municipio,
        '2025' as periodo_referencia,
        count(distinct codigo_cnes)::text
            || ' estabelecimento(s) presentes em competências de 2025 mas ausentes da mais recente carregada'
            as evidencia

    from rede_cnes
    where situacao_operacional = 'possivelmente_encerrado'
    group by id_municipio

),

financiamento as (

    select * from {{ ref('mart_financiamento_saude_uniao') }}

),

alerta_financiamento_liquido_negativo as (

    select
        'financiamento_liquido_negativo' as codigo_regra,
        'Saldo líquido negativo em financiamento federal de saúde (estornos superam recursos recebidos)' as descricao_regra,
        'media' as severidade,
        'municipio' as tipo_entidade,
        id_municipio,
        ano::text as periodo_referencia,
        'Saldo líquido de R$ ' || round(sum(valor), 2)::text
            || ' em ' || ano::text as evidencia

    from financiamento
    group by id_municipio, ano
    having sum(valor) < 0

),

alertas as (

    select * from alerta_siops_abaixo_minimo
    union all
    select * from alerta_rede_possivel_encerramento
    union all
    select * from alerta_financiamento_liquido_negativo

)

select
    md5(a.codigo_regra || '-' || a.id_municipio::text || '-' || a.periodo_referencia) as id_alerta,
    a.codigo_regra,
    a.descricao_regra,
    a.severidade,
    a.tipo_entidade,
    a.id_municipio,
    m.nome_municipio,
    a.periodo_referencia,
    a.evidencia,
    'ativo' as status

from alertas a
left join municipios m
    on a.id_municipio = m.id_municipio
