{#
    dbt por padrão gera "<schema_do_profile>_<custom_schema>" (ex.:
    "staging_staging"). CLAUDE.md pede schemas exatos por camada
    (staging, intermediate, marts) — sem esse override, os schemas sairiam
    com prefixo duplicado.
#}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
