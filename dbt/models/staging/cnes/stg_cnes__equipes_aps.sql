with equipes as (

    select * from {{ source('raw_cnes', 'equipes_aps') }}

),

equipes_tipadas as (

    select
        id_equipe,
        codigo_cnes,
        cod_municipio_ibge6,

        codigo_tipo_equipe,
        -- Mesma tipologia usada pelo endpoint DEMAS de cadastro vinculado
        -- (stg_sisab__cadastro_vinculado.sigla_equipe) — confirmado contra
        -- amostra real do CNES: só os 4 tipos filtrados no collector
        -- aparecem aqui (ver TIPOS_EQUIPE_APS em
        -- include/collectors/cnes/parser.py).
        case codigo_tipo_equipe
            when '70' then 'eSF'
            when '73' then 'eCR'
            when '74' then 'eAPP'
            when '76' then 'eAP'
        end as sigla_equipe,

        nome_equipe,
        competencia_ativacao,
        competencia_desativacao,

        -- Sentinela "900001" = equipe segue ativa (confirmado contra dado
        -- real, ver docs/COLLECTOR_TEMPLATE.md). "situação" aqui é só
        -- ativa/desativada na competência carregada (2025-12) — não há
        -- série histórica de equipes ainda, diferente de estabelecimentos.
        case competencia_desativacao
            when '900001' then 'ativa'
            else 'desativada'
        end as situacao_equipe,

        motivo_desativacao,
        competencia,
        id_area,
        nome_area,
        id_segmento,
        descricao_segmento,
        tipo_segmento,
        _loaded_at,
        _source_file,
        _reference_year,
        _reference_month

    from equipes

)

select * from equipes_tipadas
