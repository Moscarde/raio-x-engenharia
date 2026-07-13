with rede as (

    select * from {{ source('raw_cnes', 'rede_porte_municipio') }}

)

select
    cod_municipio_ibge6,
    competencia,
    quantidade_estabelecimentos,
    _loaded_at,
    _source_file

from rede
