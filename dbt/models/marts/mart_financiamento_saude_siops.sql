with rreo as (

    select * from {{ ref('stg_siops__rreo_anexo14') }}

)

select
    id_municipio,
    ano_exercicio,
    periodo_bimestre,
    codigo_conta,
    descricao_conta,
    coluna,
    valor

from rreo
