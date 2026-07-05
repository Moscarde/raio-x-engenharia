with repasses as (

    select * from {{ source('raw_fns', 'repasses') }}

),

repasses_tipados as (

    select
        id_lancamento,
        cnpj_ente_solicitante,
        nome_ente_solicitante,
        codigo_programa_agil,

        case tipo_operacao
            when 'C' then 'credito'
            when 'D' then 'debito'
        end as tipo_operacao,

        descricao_tipo_operacao,
        descricao_lancamento,
        data_lancamento,
        data_evento_lancamento,
        numero_referencia_unica,
        tipo_favorecido,
        descricao_tipo_favorecido,
        nome_favorecido,
        valor_lancamento,
        id_categoria_despesa,
        quantidade_subtransacoes,
        _loaded_at,
        _source_url,
        _reference_year

    from repasses

)

select * from repasses_tipados
