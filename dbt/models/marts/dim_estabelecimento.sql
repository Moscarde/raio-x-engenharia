with estabelecimentos as (

    select * from {{ ref('stg_cnes__estabelecimentos') }}

),

-- stg_cnes__estabelecimentos agora carrega série histórica (1 linha por
-- codigo_cnes + competência, ver ROADMAP.md "Histórico de rede CNES"), mas
-- esta dimensão preserva o contrato "1 linha por estabelecimento" de quem
-- já consome — fica só a competência mais recente de cada um. A série
-- completa (abertura/fechamento, mudança de tipo ao longo do tempo) segue
-- disponível em stg_cnes__estabelecimentos para uma mart de auditoria/
-- histórico futura.
estabelecimento_mais_recente as (

    select
        *,
        row_number() over (
            partition by codigo_cnes order by competencia_date desc
        ) as ordem_competencia

    from estabelecimentos

),

municipios as (

    select * from {{ ref('int_ibge__municipio_codigo6') }}

),

-- Complementa com nome/endereço/geo do DEMAS (ver ROADMAP.md "Rede CNES
-- detalhada") — fonte diferente da série histórica acima (cadastro vivo,
-- sem competência), por isso um join simples por codigo_cnes, não window
-- function.
detalhes as (

    select * from {{ ref('stg_cnes__estabelecimentos_detalhados') }}

)

select
    e.codigo_cnes,
    -- id_municipio (7 dígitos) via bridge int_ibge__municipio_codigo6 —
    -- mesmo padrão já usado por fct_internacoes, fct_obitos,
    -- fct_nascidos_vivos, mart_indicadores_aps e
    -- fct_producao_ambulatorial (ver ROADMAP_DBT.md). cod_municipio_ibge6
    -- (6 dígitos) mantido também, para consumidores que já dependem dele.
    mun.id_municipio,
    e.cod_municipio_ibge6,
    e.tipo_pessoa,
    e.nivel_dependencia,
    e.codigo_tipo_unidade,
    e.descricao_tipo_unidade,
    e.natureza_organizacao,
    e.codigo_natureza_juridica,
    e.descricao_natureza_juridica,
    e.atividade_ensino,
    e.tem_vinculo_sus,
    e.tipo_gestao,
    e.esfera_administrativa,
    e.competencia_date as competencia_cadastro,

    -- Campos do DEMAS (stg_cnes__estabelecimentos_detalhados) — podem vir
    -- NULL quando o estabelecimento não está nesse cadastro (ex.: criado
    -- entre a carga de um e outro, ou fora do escopo da API); ver
    -- ROADMAP.md.
    d.nome_fantasia,
    d.endereco,
    d.numero_endereco,
    d.bairro,
    d.codigo_cep,
    d.latitude,
    d.longitude,
    d.descricao_esfera_administrativa,
    d.descricao_turno_atendimento,
    d.possui_centro_cirurgico,
    d.possui_centro_obstetrico,
    d.possui_centro_neonatal,
    d.possui_atendimento_hospitalar

from estabelecimento_mais_recente e
left join municipios mun
    on e.cod_municipio_ibge6 = mun.cod_municipio_ibge6
left join detalhes d
    on e.codigo_cnes = d.codigo_cnes
where e.ordem_competencia = 1
