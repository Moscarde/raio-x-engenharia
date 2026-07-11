# CLAUDE.md

Este projeto é um pipeline de engenharia de dados em saúde pública usando **Apache Airflow com Astro**, **dbt** e **PostgreSQL**.

O objetivo é construir uma base analítica integrada para o projeto **Raio-X da Saúde**, ingerindo dados públicos de fontes como IBGE, CNES, SIA, SIH, SISAB, FNS, SIOPS, SIM e SINASC.

O projeto deve priorizar simplicidade, rastreabilidade, modularidade e clareza arquitetural.

---

## Contexto Técnico

Este repositório é um projeto Astro com Airflow local.

O PostgreSQL de serving é externo ao stack Astro e é configurado por
`POSTGRES_*`. O PostgreSQL interno do Astro armazena apenas metadados do
Airflow durante o desenvolvimento.

Serviços esperados em ambiente local:

```text
Airflow UI:
http://raio-x-engenharia.localhost:6563

Postgres:
postgresql://localhost:5432/postgres

Credenciais padrão locais:
postgres:postgres
```

Não assumir infraestrutura externa sem solicitação explícita.

---

## Princípios do Projeto

* Manter o MVP simples.
* Preferir soluções incrementais.
* Priorizar rastreabilidade dos dados.
* Separar coleta, orquestração e transformação.
* Evitar abstrações prematuras.
* Evitar acoplamento entre Airflow, collectors e dbt.
* Garantir que cada fonte possa evoluir de forma independente.
* Escrever código compreensível para portfólio técnico.

---

## Arquitetura Geral

Fluxo conceitual:

```text
Fonte pública
   ↓
Collector Python independente
   ↓
Tabela raw no PostgreSQL
   ↓
Modelo dbt staging
   ↓
Modelo dbt intermediate
   ↓
Modelo dbt mart
```

Responsabilidades:

```text
Collectors  → extração, parsing mínimo e carga raw
Airflow     → orquestração
dbt         → transformação, testes analíticos e documentação
PostgreSQL  → armazenamento do MVP
```

---

## Separação de Responsabilidades

### Collectors

Collectors devem ser módulos Python independentes.

Eles podem:

* Baixar dados de APIs públicas.
* Baixar arquivos públicos.
* Ler arquivos locais temporários.
* Fazer parsing técnico mínimo.
* Criar schemas e tabelas raw quando necessário.
* Carregar dados brutos no PostgreSQL.
* Registrar metadados técnicos de ingestão.

Eles não devem:

* Importar Airflow.
* Depender de `DagRun`, `TaskInstance`, `Variable` ou `XCom`.
* Fazer transformação analítica complexa.
* Criar modelos finais de indicadores.
* Misturar múltiplas fontes sem necessidade clara.

A DAG chama o collector. O collector não conhece a DAG.

---

### Airflow

DAGs devem ser simples, declarativas e fáceis de ler na UI.

DAGs podem:

* Definir agenda.
* Definir dependências entre tasks.
* Chamar funções públicas dos collectors.
* Executar comandos dbt quando necessário.
* Configurar retries, timeouts e tags.

DAGs não devem:

* Conter lógica pesada de coleta.
* Conter SQL analítico longo.
* Fazer chamadas externas no nível global do arquivo.
* Executar processamento pesado durante o import.
* Misturar muitas responsabilidades no mesmo arquivo.

Evite código top-level pesado em arquivos dentro de `dags/`.

---

### dbt

dbt é responsável pela transformação analítica.

Use dbt para:

* Padronizar colunas.
* Tipar campos.
* Criar modelos staging.
* Criar modelos intermediários.
* Criar marts finais.
* Documentar modelos.
* Testar chaves, nulos e relacionamentos.

Não use dbt para:

* Baixar dados da internet.
* Fazer scraping.
* Chamar APIs.
* Controlar retries de coleta.
* Substituir o Airflow.

---

## Organização de Diretórios

A estrutura pode evoluir, mas deve preservar a separação entre:

```text
dags/       → orquestração Airflow
include/    → código Python reutilizável pelo Airflow
dbt/        → projeto dbt
tests/      → testes automatizados
docs/       → documentação de apoio (template de collector, fontes candidatas)
```

Referências vivas:

* [ROADMAP.md](ROADMAP.md) — status de cada fonte.
* [docs/fontes.md](docs/fontes.md) — rotas candidatas por fonte e escopo de volume do MVP.
* [docs/COLLECTOR_TEMPLATE.md](docs/COLLECTOR_TEMPLATE.md) — checklist de arquivos para um novo collector.

Collectors devem ficar em caminho previsível, preferencialmente:

```text
include/collectors/
```

Cada fonte deve ter seu próprio submódulo.

Exemplo conceitual:

```text
include/collectors/ibge/
include/collectors/cnes/
include/collectors/sia/
include/collectors/sih/
include/collectors/sisab/
```

---

## Convenções de Banco

Use schemas por camada e/ou fonte.

Para dados brutos, prefira schemas separados por fonte:

```text
raw_ibge
raw_cnes
raw_sia
raw_sih
raw_sisab
raw_fns
raw_siops
raw_sim
raw_sinasc
```

Para modelos dbt, use schemas lógicos conforme a camada:

```text
staging
intermediate
marts
```

Tabelas raw devem preservar rastreabilidade da origem.

Campos técnicos úteis:

```text
_loaded_at
_source_url
_source_file
_file_hash
_reference_period
_reference_year
_reference_month
```

Use apenas os campos técnicos que fizerem sentido para a fonte.

---

## Convenções de Nomeação dbt

Prefixos recomendados:

```text
stg_  → staging
int_  → intermediate
dim_  → dimensão
fct_  → fato
mart_ → tabela analítica ampla
```

Padrão para staging:

```text
stg_<fonte>__<entidade>
```

Exemplos:

```text
stg_ibge__municipios
stg_cnes__estabelecimentos
stg_sia__producao_ambulatorial
stg_sih__internacoes
stg_sisab__indicadores
```

---

## Seeds e dicionários externos (de-para)

Todo seed em `dbt/seeds/` que traduz código de fonte (DATASUS, IBGE, etc.)
para valor legível precisa de rastreabilidade da própria fonte, não só do
dado que ele decodifica. Isso facilita auditoria futura: alguém revisando
o dado precisa achar rápido de onde veio o de-para, quando foi consultado,
e o que ficou sem cobertura.

Regras:

* Todo seed de de-para tem uma entrada correspondente em
  `dbt/seeds/_seeds__models.yml` (ou arquivo equivalente por domínio), com
  `description` contendo:
  * URL da fonte oficial consultada.
  * Data em que foi consultada (dado externo muda; a data marca a validade
    da cópia local).
  * Cobertura: quantos códigos do domínio real foram verificados vs. total
    de códigos distintos observados na fonte (ex.: "22 de 25 códigos
    confirmados contra a Tabela II da Receita Federal; 4000, 2305, 2313
    sem confirmação, ficam de fora do seed").
* Nunca adivinhar/inventar valor de código sem fonte verificável. Código
  sem confirmação fica de fora do seed (o join em staging retorna `NULL`
  para ele) — `NULL` documentado é melhor que rótulo errado.
* Se a fonte for uma página HTML sem API, preferir extrair valores exatos
  (grep pelo código, não pelo nome) antes de transcrever manualmente.
* Quando um domínio inteiro não tiver fonte oficial verificável no momento
  da implementação, documentar isso onde o código cru é mantido (comentário
  no `.sql` do model + linha em `ROADMAP_DBT.md`), em vez de deixar seed
  incompleto sem explicação.

---

## Estilo de Código Python

* Funções devem ter entre 4 e 20 linhas sempre que possível.
* Arquivos devem ter menos de 500 linhas.
* Divida arquivos por responsabilidade.
* Uma função deve fazer uma coisa.
* Um módulo deve ter uma responsabilidade principal.
* Use nomes específicos e pesquisáveis.
* Evite nomes genéricos como `data`, `handler`, `manager`, `processor`.
* Use type hints explícitos.
* Evite `Any`, `Dict` genérico e funções sem tipo.
* Evite duplicação.
* Prefira early return em vez de muitos `else`.
* Use no máximo 2 níveis de indentação.
* Mensagens de erro devem conter o valor problemático e o formato esperado.

---

## Estilo de SQL

* Priorize legibilidade.
* Use CTEs claras.
* Nomeie CTEs pelo que representam.
* Evite SQL excessivamente compacto.
* Evite `SELECT *` em marts e fatos finais.
* Use `SELECT *` em staging apenas quando for intencional.
* Uma CTE deve representar uma etapa lógica.
* Não coloque regra de negócio relevante sem nome ou comentário.

---

## Comentários e Docstrings

* Preserve comentários existentes durante refatorações.
* Comentários devem explicar o motivo, não o óbvio.
* Evite comentários como “faz request” ou “cria tabela”.
* Use docstrings em funções públicas.
* Docstrings devem explicar intenção e conter um exemplo simples quando útil.
* Documente limitações conhecidas de fontes externas.

---

## Testes

Os testes devem rodar com um único comando.

Comando padrão:

```bash
pytest
```

Regras:

* Toda função relevante deve ter teste.
* Correções de bug devem ter teste de regressão.
* Mock de I/O externo deve usar classes fake nomeadas.
* Evite stubs inline difíceis de entender.
* Testes devem ser rápidos, independentes, repetíveis e autoexplicativos.

Testes de collector (`tests/collectors/<fonte>/`) rodam com `pytest` puro,
sem Airflow instalado. Isso é garantido por `pytest.ini`
(`testpaths = tests/collectors`, `pythonpath = .`). `astro dev pytest`
continua cobrindo `tests/` inteiro, inclusive `tests/dags/` (que exige
Airflow), porque passa esse caminho explicitamente e ignora `testpaths`.

---

## Dependências

* Injete dependências por parâmetro ou construtor.
* Evite dependências globais escondidas.
* Encapsule bibliotecas externas atrás de interfaces simples do projeto.
* Não adicione dependências novas sem necessidade clara.
* Prefira biblioteca padrão quando for suficiente.

`requirements.txt` contém dependências de execução (ex. `requests`,
`psycopg[binary]`, `python-dotenv`) usadas tanto na imagem Astro/Airflow
quanto no `.venv` local de desenvolvimento. `requirements-dev.txt` contém
apenas ferramentas de dev/teste (`pytest`, `ruff`, `black`) e nunca entra na
imagem Airflow.

---

## Logging

Use logs técnicos estruturados quando possível.

Logs devem informar:

* Fonte.
* Tabela.
* Quantidade de linhas.
* Período de referência, quando existir.
* URL, endpoint ou arquivo, quando útil.
* Tempo de execução, quando útil.

Evite logs genéricos como:

```text
iniciando
fim
erro
```

---

## Tratamento de Erros

Erros devem ser explícitos e úteis.

Inclua quando possível:

* Fonte.
* Endpoint ou arquivo.
* Valor problemático.
* Formato esperado.
* Sugestão de correção.

Não silencie exceções.

Evite:

```python
try:
    ...
except Exception:
    pass
```

---

## Idempotência

Pipelines devem ser idempotentes sempre que possível.

Executar a mesma DAG mais de uma vez para o mesmo período não deve duplicar dados indevidamente.

Estratégias aceitas:

* `upsert` por chave natural.
* `delete + insert` por partição.
* Carga full refresh para dimensões pequenas.
* Registro de metadados de ingestão.

A estratégia deve ser simples e adequada ao volume da fonte.

---

## Formatação

Use formatadores padrão.

Python:

```bash
black .
ruff check .
```

SQL/dbt:

```bash
sqlfluff lint dbt/
```

Se uma ferramenta ainda não estiver configurada, não introduza complexidade sem necessidade.

---

## Segurança

Nunca commitar:

```text
senhas
tokens
arquivos .env reais
credenciais de banco
chaves privadas
```

Mesmo usando dados públicos, mantenha rastreabilidade da origem.

Não introduzir dados sensíveis no projeto sem solicitação explícita e política clara.

---

## Instruções para IA

Ao trabalhar neste projeto:

* Leia este arquivo antes de propor mudanças.
* Preserve a separação entre collectors, Airflow e dbt.
* Não crie abstrações grandes sem necessidade.
* Não acople collectors ao Airflow.
* Não coloque lógica de coleta no dbt.
* Não coloque lógica analítica nas DAGs.
* Prefira mudanças pequenas e incrementais.
* Mantenha o projeto compreensível para fins de portfólio.
* Explique decisões técnicas relevantes.
* Quando houver dúvida entre simplicidade e sofisticação, escolha simplicidade.
