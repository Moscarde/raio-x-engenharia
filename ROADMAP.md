# Roadmap de fontes

Status dos collectors do projeto `raio-x-engenharia`. Rotas candidatas e
detalhes por fonte em [docs/fontes.md](docs/fontes.md). Estrutura de arquivos
a seguir em novos collectors: [docs/COLLECTOR_TEMPLATE.md](docs/COLLECTOR_TEMPLATE.md).

| Fonte | Status | Schema raw | Escopo (1 linha) |
| --- | --- | --- | --- |
| IBGE | ✅ collector pronto | `raw_ibge` | Municípios (hierarquia territorial) |
| CNES | ✅ collector pronto | `raw_cnes` | Estabelecimentos de saúde |
| SIA | ✅ collector pronto | `raw_sia` | Produção ambulatorial |
| SIH | planejado | `raw_sih` | Internações |
| SISAB | planejado | `raw_sisab` | Indicadores de atenção básica |
| FNS | planejado | `raw_fns` | Repasses/financiamento |
| SIOPS | planejado | `raw_siops` | Orçamento em saúde |
| SIM | planejado | `raw_sim` | Óbitos |
| SINASC | planejado | `raw_sinasc` | Nascidos vivos |

DAGs Airflow ficam para depois: primeiro todos os collectors, mantendo a
estrutura padronizada (ver template), depois orquestração.

## Observações pendentes

- **SIA**: `run_producao_ambulatorial.py` já loopa as 12 competências de 2025
  (escopo aprovado), mas só foi executado de ponta a ponta para 1 mês
  (dez/2025, validado e idempotente). A carga do ano completo (12 meses,
  ~2-3 arquivos de 100-180MB cada) ainda não rodou neste ambiente — estimativa
  de 1,5-2h de execução. Rodar manualmente quando fizer sentido:
  `python -m include.collectors.sia.run_producao_ambulatorial`.
