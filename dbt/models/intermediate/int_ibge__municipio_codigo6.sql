-- Bridge entre o código IBGE de 6 dígitos sem dígito verificador (usado
-- por SIA/SIH/SIM/SINASC/SISAB — CODUFMUN/MUNIC_MOV/CODMUNOCOR/CODMUNNASC/
-- codigo_municipio, todos confirmados contra dado real como o mesmo
-- truncamento) e o id_municipio completo (7 dígitos) do dim_municipio.
-- Reaproveitado por fct_internacoes, fct_obitos e fct_nascidos_vivos (e,
-- futuramente, fct_producao_ambulatorial) — resolver aqui uma vez evita
-- repetir o `left(..., 6)` em cada fato.

with municipios as (

    select * from {{ ref('dim_municipio') }}

)

select
    id_municipio,
    left(id_municipio::text, 6) as cod_municipio_ibge6,
    nome_municipio

from municipios
