with cadastro as (

    select * from {{ source('raw_sisab', 'cadastro_vinculado') }}

),

cadastro_tipado as (

    select
        competencia_referencia,
        sigla_unidade_federacao,
        -- TEXT pra casar com cod_municipio_ibge6 (int_ibge__municipio_codigo6),
        -- mesmo padrão de stg_sisab__indicador_desempenho.
        codigo_municipio_ibge::text as codigo_municipio_ibge,
        nome_municipio,
        estimativa_populacional_ibge,
        tipo_equipe,
        sigla_equipe,
        situacao_equipe,

        case pessoas_vinculadas_criterios_ponderacao
            when 'Sim' then true
            when 'Não' then false
        end as pessoas_vinculadas_com_ponderacao,

        pessoas_vinculadas_equipe_municipio,
        _loaded_at,
        _source_url

    from cadastro

)

select * from cadastro_tipado
