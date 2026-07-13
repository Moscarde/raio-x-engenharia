with estabelecimentos as (

    select * from {{ source('raw_cnes', 'estabelecimentos_detalhados') }}

),

estabelecimentos_tipados as (

    select
        codigo_cnes,
        nome_razao_social,
        nome_fantasia,
        codigo_tipo_unidade,
        codigo_cep,
        endereco,
        numero_endereco,
        bairro,
        numero_telefone,
        latitude,
        longitude,
        email,
        descricao_turno_atendimento,

        case faz_atendimento_ambulatorial_sus
            when 'SIM' then true
            when 'NAO' then false
        end as faz_atendimento_ambulatorial_sus,

        -- Já vem decodificada pela API DEMAS (ex. "MUNICIPAL"); nome
        -- distinto de esfera_administrativa (cru) em
        -- stg_cnes__estabelecimentos, de propósito — são 2 fontes
        -- diferentes, não escolhemos uma como "a certa".
        descricao_esfera_administrativa,
        codigo_motivo_desabilitacao,

        (possui_centro_cirurgico = 1) as possui_centro_cirurgico,
        (possui_centro_obstetrico = 1) as possui_centro_obstetrico,
        (possui_centro_neonatal = 1) as possui_centro_neonatal,
        (possui_atendimento_hospitalar = 1) as possui_atendimento_hospitalar,
        (possui_servico_apoio = 1) as possui_servico_apoio,
        (possui_atendimento_ambulatorial = 1) as possui_atendimento_ambulatorial,

        data_atualizacao,
        _loaded_at,
        _source_url

    from estabelecimentos

)

select * from estabelecimentos_tipados
