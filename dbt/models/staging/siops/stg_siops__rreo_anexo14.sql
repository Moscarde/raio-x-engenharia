with rreo as (

    select * from {{ source('raw_siops', 'rreo_anexo14') }}

)

select
    ano_exercicio,
    tipo_demonstrativo,
    periodo_bimestre,
    periodicidade,
    instituicao,
    id_municipio,
    uf,
    populacao,
    anexo,
    esfera,
    rotulo,
    coluna,
    codigo_conta,
    descricao_conta,
    valor,
    _loaded_at,
    _source_url

from rreo
