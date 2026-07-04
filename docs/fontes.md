# docs/fontes.md

Referência inicial das fontes de dados do projeto `raio-x-engenharia`.

Este arquivo registra rotas candidatas para exploração.
A rota definitiva, campos e regras de parsing devem ser confirmados dentro de cada collector no momento da implementação.

| Fonte               | Rota/base inicial                                                                                       | Formato esperado           | Observação                                                                          |
| ------------------- | ------------------------------------------------------------------------------------------------------- | -------------------------- | ----------------------------------------------------------------------------------- |
| IBGE                | `https://servicodados.ibge.gov.br/api/v1/localidades/municipios`                                        | JSON                       | Municípios e hierarquia territorial.                                                |
| CNES                | `ftp://ftp.datasus.gov.br/dissemin/publicos/CNES/200508_/Dados/`                                        | DBC/DBF                    | Arquivos dissemináveis do CNES.                                                     |
| SIA                 | `ftp://ftp.datasus.gov.br/dissemin/publicos/SIASUS/200801_/Dados/`                                      | DBC                        | Produção ambulatorial a partir de 2008.                                             |
| SIH                 | `ftp://ftp.datasus.gov.br/dissemin/publicos/SIHSUS/200801_/Dados/`                                      | DBC                        | Produção hospitalar a partir de 2008.                                               |
| SISAB               | `https://sisab.saude.gov.br/paginas/acessoRestrito/relatorio/federal/indicadores/indicadorPainel.xhtml` | CSV/Excel/ODS via download | Indicadores públicos da APS.                                                        |
| SISAB FTP           | `ftp://ftp.datasus.gov.br/dissemin/publicos/CMD/DadosSISAB/`                                            | a validar                  | Rota candidata para exploração futura.                                              |
| FNS                 | `https://consultafns.saude.gov.br/`                                                                     | HTML/API interna a validar | Consulta pública de repasses do FNS.                                                |
| FNS / Fundo a Fundo | `https://docs.api.transferegov.gestao.gov.br/fundoafundo/`                                              | API JSON                   | API documentada para transferências fundo a fundo. Avaliar aderência ao escopo FNS. |
| SIOPS               | `https://siops.datasus.gov.br/`                                                                         | HTML/downloads a validar   | Receitas e despesas públicas em saúde.                                              |
| SIM                 | `ftp://ftp.datasus.gov.br/dissemin/publicos/SIM/CID10/DORES/`                                           | DBC                        | Óbitos por residência.                                                              |
| SINASC              | `ftp://ftp.datasus.gov.br/dissemin/publicos/SINASC/NOV/DNRES/`                                          | DBC                        | Nascidos vivos.                                                                     |

---

## Escopo de volume para o MVP

Fontes com grande volume de dados (CNES, SIA, SIH, SISAB, SIM, SINASC) devem,
na primeira implementação, restringir a coleta a **um município de referência
(Rio de Janeiro, id_municipio 3304557) e ao ano de 2025**. Isso mantém o MVP
rápido de rodar e validar antes de abrir para todos os municípios/anos.

Referência do registro correspondente em `raw_ibge.municipios`:

```text
id_municipio    nome_municipio    id_microrregiao    nome_microrregiao    id_mesorregiao    nome_mesorregiao    id_uf    sigla_uf    nome_uf    id_regiao    sigla_regiao    nome_regiao    _loaded_at    _source_url
3304557    Rio de Janeiro    33018    Rio de Janeiro    3306    Metropolitana do Rio de Janeiro    33    RJ    Rio de Janeiro    3    SE    Sudeste    2026-07-04 07:40:44.230 -0300    https://servicodados.ibge.gov.br/api/v1/localidades/municipios
```

Ampliar para outros municípios/anos é decisão explícita de uma etapa futura,
não do MVP inicial.
