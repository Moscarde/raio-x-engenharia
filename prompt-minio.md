# Prompt: infraestrutura MinIO na VPS

```text
Implemente um object storage S3-compatible com MinIO single-node para o projeto
raio-x-engenharia, hospedado na VPS 2.25.172.31.

Objetivo:
- MinIO armazenará dados landing, raw, staging e intermediate em Parquet.
- PostgreSQL continuará reservado às tabelas gold: dimensões, fatos e marts.
- Airflow na VPS acessará MinIO pela rede Docker interna.
- Máquinas de desenvolvimento poderão acessar MinIO por HTTP no IP público.
- Não migrar collectors ou dbt para Parquet nesta etapa.

Restrições:
- Não modificar diretamente o stack gerado pelo Astro.
- Criar docker-compose.minio.yml independente para o MinIO.
- Não usar Caddy, DNS, TLS ou domínio nesta etapa.
- Persistir dados em /srv/raio-x/minio/data.
- Usar MinIO single-node, sem modo distribuído.
- Usar a rede Docker externa raio-x-data, compartilhada com o scheduler Astro.
- Endpoint interno: http://minio:9000
- Endpoint remoto: http://2.25.172.31:9000
- Console remoto: http://2.25.172.31:9001
- Não usar credenciais root pela aplicação.
- Gerar todas as senhas diretamente na VPS com alta entropia; nunca escrever
  segredos em arquivos versionados, documentação ou saída de logs.
- Documentar explicitamente que HTTP público não é adequado para credenciais
  permanentes ou dados sensíveis e que a exposição deve ser limitada por firewall.
- Documentar que MinIO single-node na mesma VPS não oferece alta disponibilidade
  nem substitui backup externo.

Segurança:
- Configurar firewall para permitir portas 9000 e 9001 somente para os IPs
  administrativos autorizados. Nunca liberar para 0.0.0.0/0.
- Se não for possível manter IPs de origem fixos, documentar acesso remoto por:
  ssh -L 9000:localhost:9000 -L 9001:localhost:9001 usuario@2.25.172.31
  Nesse caso, não expor 9000 e 9001 publicamente.
- Proteger o console com as credenciais próprias do MinIO.
- Criar usuário de produção limitado aos buckets prod.
- Criar usuário de desenvolvimento limitado aos buckets dev.

Entregas:
1. docker-compose.minio.yml com MinIO, volume persistente, healthcheck,
   restart unless-stopped e participação na rede externa raio-x-data.
2. .env.example sem segredos reais.
3. Script administrativo não interativo que:
   - espera o healthcheck;
   - cria os buckets:
     raio-x-landing-prod
     raio-x-lake-prod
     raio-x-artifacts-prod
     raio-x-landing-dev
     raio-x-lake-dev
     raio-x-artifacts-dev
   - cria políticas segregadas para prod e dev;
   - cria usuários de aplicação sem privilégios administrativos.
4. docs/minio.md com instalação, operação, firewall, acesso por SSH tunnel,
   backup, restore e rotação de credenciais.
5. Atualização do docker-compose.override.yml para conectar o scheduler Astro
   à rede externa raio-x-data, permitindo resolver http://minio:9000.
6. Atualização do .gitignore para arquivos locais do MinIO e arquivos .env.
7. Não adicionar dependências Python nesta etapa.

Variáveis esperadas:
MINIO_ROOT_USER
MINIO_ROOT_PASSWORD
MINIO_BROWSER_REDIRECT_URL=http://2.25.172.31:9001

OBJECT_STORAGE_ENDPOINT=http://minio:9000
OBJECT_STORAGE_EXTERNAL_ENDPOINT=http://2.25.172.31:9000
OBJECT_STORAGE_REGION=us-east-1
OBJECT_STORAGE_SECURE=false

OBJECT_STORAGE_LANDING_BUCKET=raio-x-landing-prod
OBJECT_STORAGE_LAKE_BUCKET=raio-x-lake-prod
OBJECT_STORAGE_ARTIFACTS_BUCKET=raio-x-artifacts-prod
OBJECT_STORAGE_ACCESS_KEY
OBJECT_STORAGE_SECRET_KEY

OBJECT_STORAGE_DEV_ACCESS_KEY
OBJECT_STORAGE_DEV_SECRET_KEY

Validação:
- docker compose -f docker-compose.minio.yml config
- MinIO healthcheck aprovado
- Scheduler do Astro resolve minio e acessa http://minio:9000
- mc consegue criar/listar objetos usando usuários prod e dev
- Usuário dev não acessa buckets prod
- Portas 9000/9001 não estão abertas para IPs não autorizados
- Acesso remoto por túnel SSH funciona.
```
