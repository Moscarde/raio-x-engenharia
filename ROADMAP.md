# Roadmap de fontes

Status dos collectors do projeto `raio-x-engenharia`. Rotas candidatas e
detalhes por fonte em [docs/fontes.md](docs/fontes.md). Estrutura de arquivos
a seguir em novos collectors: [docs/COLLECTOR_TEMPLATE.md](docs/COLLECTOR_TEMPLATE.md).

| Fonte | Status | Schema raw | Escopo (1 linha) |
| --- | --- | --- | --- |
| IBGE | ✅ collector pronto | `raw_ibge` | Municípios (hierarquia territorial) |
| CNES | planejado | `raw_cnes` | Estabelecimentos de saúde |
| SIA | planejado | `raw_sia` | Produção ambulatorial |
| SIH | planejado | `raw_sih` | Internações |
| SISAB | planejado | `raw_sisab` | Indicadores de atenção básica |
| FNS | planejado | `raw_fns` | Repasses/financiamento |
| SIOPS | planejado | `raw_siops` | Orçamento em saúde |
| SIM | planejado | `raw_sim` | Óbitos |
| SINASC | planejado | `raw_sinasc` | Nascidos vivos |

DAGs Airflow ficam para depois: primeiro todos os collectors, mantendo a
estrutura padronizada (ver template), depois orquestração.
