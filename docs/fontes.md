# docs/fontes.md

Referência inicial das fontes de dados do projeto `raio-x-engenharia`.

Este arquivo registra rotas candidatas para exploração.
A rota definitiva, campos e regras de parsing devem ser confirmados dentro de cada collector no momento da implementação.

| Fonte               | Rota/base inicial                                                                                       | Formato esperado           | Observação                                                                          |
| ------------------- | ------------------------------------------------------------------------------------------------------- | -------------------------- | ----------------------------------------------------------------------------------- |
| IBGE                | `https://servicodados.ibge.gov.br/api/v1/localidades/municipios`                                        | JSON                       | Municípios e hierarquia territorial.                                                |
| IBGE / população    | `https://servicodados.ibge.gov.br/api/v3/agregados/6579/periodos/-1/variaveis/9324`                     | JSON (API agregados/SIDRA) | ✅ Estimativas da população residente por município (agregado 6579, referência 1º de julho); ver ROADMAP.md. |
| CNES                | `ftp://ftp.datasus.gov.br/dissemin/publicos/CNES/200508_/Dados/`                                        | DBC/DBF                    | Arquivos dissemináveis do CNES.                                                     |
| SIA                 | `ftp://ftp.datasus.gov.br/dissemin/publicos/SIASUS/200801_/Dados/`                                      | DBC                        | Produção ambulatorial a partir de 2008.                                             |
| SIH                 | `ftp://ftp.datasus.gov.br/dissemin/publicos/SIHSUS/200801_/Dados/`                                      | DBC                        | Produção hospitalar a partir de 2008.                                               |
| SISAB               | `https://sisab.saude.gov.br/paginas/acessoRestrito/relatorio/federal/indicadores/indicadorPainel.xhtml` | CSV/Excel/ODS via download | ❌ Rota original. Painel exige navegação restrita/sessão, sem download simples via API/FTP. |
| SISAB FTP           | `ftp://ftp.datasus.gov.br/dissemin/publicos/CMD/DadosSISAB/`                                            | a validar                  | ❌ Rota candidata. Diretório `Dados` vazio no FTP.                                  |
| SISAB / DEMAS       | `https://apidadosabertos.saude.gov.br/atencao-primaria/indicador-desempenho-programa-previne-brasil`   | JSON (API DEMAS)           | ✅ Rota efetiva encontrada depois das duas acima falharem. API REST pública sem autenticação; ver ROADMAP.md. |
| SISAB / DEMAS cadastro vinculado | `https://apidadosabertos.saude.gov.br/atencao-primaria/cadastro-vinculado-programa-previne-brasil` | JSON (API DEMAS) | ✅ Mesma API do indicador de desempenho, endpoint diferente. Dá população IBGE embutida + pessoas vinculadas por tipo/situação de equipe (eSF/eAP/eAPP/eCR) — base de cobertura de APS/equipes ESF; ver ROADMAP.md. |
| CNES / equipes de APS | `ftp://ftp.datasus.gov.br/dissemin/publicos/CNES/200508_/Dados/` (grupo "EP") | DBC/DBF | ✅ Mesmo FTP do grupo "ST" (Estabelecimentos), grupo diferente. Cadastro/situação de equipes por competência (IDEQUIPE, tipo, ativação/desativação); ver ROADMAP.md e docs/COLLECTOR_TEMPLATE.md. |
| FNS                 | `https://consultafns.saude.gov.br/`                                                                     | HTML/API interna a validar | Consulta pública de repasses do FNS.                                                |
| FNS / Fundo a Fundo | `https://docs.api.transferegov.gestao.gov.br/fundoafundo/`                                              | API JSON                   | API documentada para transferências fundo a fundo. Avaliar aderência ao escopo FNS. |
| Financiamento completo / Portal da Transparência | `https://api.portaldatransparencia.gov.br/api-de-dados/despesas/recursos-recebidos` | JSON (API, exige chave) | ✅ Única fonte deste projeto que exige autenticação (chave pessoal gratuita via cadastro de e-mail). Complementa o FNS Fundo a Fundo (recorte estreito) com recursos recebidos pelo CNPJ do município, de qualquer unidade vinculada ao Ministério da Saúde; ver ROADMAP.md e docs/COLLECTOR_TEMPLATE.md. |
| SIOPS               | `https://siops.datasus.gov.br/`                                                                         | HTML/downloads a validar   | ❌ Rota original. Relatório de cálculo do % de saúde (`carregarDadosLC141.php`) tem bug real: respostas de 300+MB com valores zerados. |
| SIOPS / SICONFI     | `https://apidatalake.tesouro.gov.br/ords/cdwhprd/siconfi/tt/rreo`                                       | JSON (API SICONFI)         | ✅ Rota efetiva encontrada depois da rota acima falhar. API REST pública sem autenticação (Tesouro Nacional); ver ROADMAP.md. |
| SIM                 | `ftp://ftp.datasus.gov.br/dissemin/publicos/SIM/CID10/DORES/`                                           | DBC                        | Óbitos por residência.                                                              |
| SINASC              | `ftp://ftp.datasus.gov.br/dissemin/publicos/SINASC/NOV/DNRES/`                                          | DBC                        | Nascidos vivos.                                                                     |

---

## Escopo de volume para o MVP

Fontes com grande volume de dados (CNES, SIA, SIH, SISAB, SIM, SINASC, FNS,
SIOPS) devem restringir a coleta a **municípios de referência e ao ano de
2025**. Isso mantém o MVP rápido de rodar e validar antes de abrir para
todos os municípios/anos.

Município de referência original do MVP, mais 2 municípios adicionados em
2026-07-05 (Paraty e Nova Iguaçu, ambos RJ) — 3 no total, em todas as fontes
exceto IBGE (nacional, sem filtro) e SIA (estado inteiro desde 2026-07-04,
ver seção abaixo):

```text
id_municipio    nome_municipio    id_uf  sigla_uf
3304557         Rio de Janeiro    33     RJ
3303807         Paraty            33     RJ
3303500         Nova Iguaçu       33     RJ
```

Códigos por fonte (cada uma usa um sistema de identificação diferente para
o mesmo conjunto de municípios — ver constantes `MUNICIPIOS_REFERENCIA_*`
em cada `parser.py`):

| Fonte | Sistema de código | Rio de Janeiro | Paraty | Nova Iguaçu |
| --- | --- | --- | --- | --- |
| CNES/SIH/SIM/SINASC | IBGE 6 dígitos (sem DV) | 330455 | 330380 | 330350 |
| SISAB (DEMAS) | IBGE 6 dígitos (sem DV) | 330455 | 330380 | 330350 |
| SIOPS (SICONFI) | IBGE 7 dígitos (id_ente) | 3304557 | 3303807 | 3303500 |
| FNS (Fundo a Fundo) | CNPJ do ente | 42498733000148 | 29172475000147 | 29138278000101 |

Ampliar para outros municípios/anos além destes 3 é decisão explícita de
uma etapa futura, não do MVP inicial.

**Exceção confirmada (2026-07-13)**: a demanda "Comparação entre pares"
(ver ROADMAP.md) expandiu 2 fontes pro RJ inteiro (92 municípios,
confirmado explicitamente com o usuário) — só população estimada do IBGE
(`run_populacao_estimada_rj.py`) e porte de rede do CNES (contagem de
estabelecimentos, `run_rede_porte_municipio.py`, `raw_cnes.rede_porte_municipio`).
As demais fontes (SIH, SIM, SINASC, SISAB, SIOPS, FNS, Portal da
Transparência, e a coleta detalhada de estabelecimentos/equipes do CNES)
seguem restritas aos 3 municípios de referência.

Exceção confirmada: **SIM** (óbitos) e **SINASC** (nascidos vivos) são bases
anuais consolidadas com atraso de publicação — 2025 não está disponível no
FTP do DATASUS para nenhuma das duas. Usam o último ano realmente publicado
no momento da implementação: SIM ano 2024, SINASC ano 2022. Ver
[docs/COLLECTOR_TEMPLATE.md](COLLECTOR_TEMPLATE.md) para detalhes.

Segunda exceção, de decisão explícita (não de limitação da fonte): **SIA**
carrega o **estado (UF) inteiro**, não só o município de referência.
Motivo: `client.py` já decodifica o arquivo DBC inteiro (`to_dict`) antes
de qualquer filtro por município ser possível — o custo de CPU é pago de
qualquer forma, então filtrar por município antes do INSERT só descartava
~38% das linhas já decodificadas (medido: Rio é 62% do estado num arquivo
de nov/2025), sem ganho de tempo real e fechando a porta pra outros
municípios do RJ no futuro. Volume sobe de ~56M para ~90M linhas/ano; ver
ROADMAP.md.
