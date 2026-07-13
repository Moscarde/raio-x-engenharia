-- Percentual de Internações por Condições Sensíveis à Atenção Primária
-- (ICSAP) por município, ver ROADMAP.md "Internações ICSAP". Tabulado por
-- município de RESIDÊNCIA do paciente (id_municipio_paciente), não do
-- estabelecimento — mesmo critério de seleção da metodologia oficial
-- (Portaria SAS/MS 221/2008: "Tabulação dos dados por município de
-- residência do usuário").
--
-- Simplificação conhecida: o denominador aqui é o total de internações
-- (todas as AIH), não só "internações clínicas" como pede a metodologia
-- oficial completa (que exclui partos com desfecho natural — CID O80 a
-- O84 — e filtra por tipo de AIH = Normal, complexidade = Média e uma
-- lista específica de motivo de saída). raw_sih.internacoes não captura
-- tipo de AIH, complexidade nem motivo de saída (só os campos usados
-- pelas fct/dim existentes) — replicar a metodologia oficial completa
-- exigiria expandir o collector do SIH pra esses campos, não feito ainda.
-- `percentual_icsap` aqui é internações ICSAP / total de internações, uma
-- leitura mais simples e mais alta que a taxa oficial (que usa um
-- denominador menor).

with internacoes as (

    select * from {{ ref('fct_internacoes') }}

),

diagnosticos_icsap as (

    select * from {{ ref('int_sih__diagnostico_icsap') }}

),

internacoes_classificadas as (

    select
        i.id_municipio_paciente,
        -- Ano de data_internacao (data de admissão), não da competência de
        -- carga do SIH — internações de longa permanência processadas em
        -- 2025 podem ter admissão em anos anteriores (confirmado contra
        -- dado real: linhas com ano 2016/2021/2022/2023/2024 no Rio de
        -- Janeiro, mesmo fenômeno de "linha retroativa" já documentado
        -- para o SIA em ROADMAP.md). Não é erro do collector.
        date_part('year', i.data_internacao)::int as ano,
        d.is_icsap

    from internacoes i
    left join diagnosticos_icsap d
        on i.diagnostico_principal = d.diagnostico_principal
    where i.id_municipio_paciente is not null

)

select
    id_municipio_paciente as id_municipio,
    ano,
    count(*) as total_internacoes,
    count(*) filter (where is_icsap) as total_internacoes_icsap,
    round(100.0 * count(*) filter (where is_icsap) / count(*), 1) as percentual_icsap

from internacoes_classificadas
group by id_municipio_paciente, ano
