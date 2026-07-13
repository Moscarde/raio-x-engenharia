with estabelecimentos as (

    select * from {{ source('raw_cnes', 'estabelecimentos') }}

),

natureza_juridica as (

    select * from {{ ref('seed_cnes_natureza_juridica') }}

),

tipo_unidade as (

    select * from {{ ref('seed_cnes_tipo_unidade') }}

),

estabelecimentos_tipados as (

    select
        -- Chave do model: codigo_cnes sozinho não é mais único desde que
        -- o raw passou a ter 1 linha por competência (ver ROADMAP.md
        -- "Histórico de rede CNES") — grão agora é estabelecimento +
        -- competência.
        e.codigo_cnes || '-' || e.competencia as id_estabelecimento_competencia,
        e.codigo_cnes,
        e.cod_municipio_ibge6,

        case e.tipo_pessoa
            when '1' then 'fisica'
            when '3' then 'juridica'
        end as tipo_pessoa,

        case e.nivel_dependencia
            when '1' then 'individual'
            when '3' then 'mantida'
        end as nivel_dependencia,

        e.tipo_unidade as codigo_tipo_unidade,
        tu.descricao_tipo_unidade,

        -- Sempre vazio nesta competência (confirmado direto no DBC via
        -- pysus, não é bug do collector) — ver docs/COLLECTOR_TEMPLATE.md.
        nullif(e.natureza_organizacao, '') as natureza_organizacao,

        e.natureza_juridica as codigo_natureza_juridica,
        nj.descricao_natureza_juridica,

        case e.atividade_ensino
            when '01' then 'unidade_universitaria'
            when '02' then 'unidade_escola_superior_isolada'
            when '03' then 'unidade_auxiliar_de_ensino'
            when '04' then 'sem_atividade_de_ensino'
            when '05' then 'hospital_de_ensino'
            else 'nao_informado'
        end as atividade_ensino,

        case e.vinculo_sus
            when '1' then true
            when '0' then false
        end as tem_vinculo_sus,

        case e.tipo_gestao
            when 'M' then 'municipal'
            when 'E' then 'estadual'
            when 'D' then 'dupla'
            when 'S' then 'sem_gestao'
            else 'nao_informado'
        end as tipo_gestao,

        -- esfera_administrativa: o dicionário oficial (PCDaS/Fiocruz)
        -- descreve domínio numérico 01-Federal/02-Estadual/03-Municipal/
        -- 04-Privada/99, mas o dado real desta competência traz os mesmos
        -- códigos de tipo_gestao (M/E) — confirmado direto no arquivo DBC
        -- via pysus, não é bug do collector. Mantido cru até confirmar se
        -- é específico desta competência ou do layout atual do CNES.
        e.esfera_administrativa,

        e.competencia,
        to_date(e.competencia, 'YYYYMM') as competencia_date,
        e.data_atualizacao,
        e._loaded_at,
        e._source_file,
        e._reference_year,
        e._reference_month

    from estabelecimentos e
    left join natureza_juridica nj
        on e.natureza_juridica = nj.codigo_natureza_juridica
    left join tipo_unidade tu
        on e.tipo_unidade = tu.codigo_tipo_unidade

)

select * from estabelecimentos_tipados
