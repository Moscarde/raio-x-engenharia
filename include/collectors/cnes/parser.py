"""Parsing dos registros brutos de estabelecimentos retornados pelo CNES (grupo ST)."""

from __future__ import annotations

REQUIRED_FIELDS = (
    "CNES",
    "CODUFMUN",
    "PF_PJ",
    "NIV_DEP",
    "TP_UNID",
    "NATUREZA",
    "NAT_JUR",
    "ATIVIDAD",
    "VINC_SUS",
    "TPGESTAO",
    "ESFERA_A",
    "COMPETEN",
    "DT_ATUAL",
)

# Municípios de referência (id_municipio em raw_ibge.municipios: Rio de
# Janeiro 3304557, Paraty 3303807, Nova Iguaçu 3303500). O CNES usa
# CODUFMUN, código IBGE de 6 dígitos sem o dígito verificador (confirmado
# contra amostra real do CNES: CODUFMUN "330455" para as ~17k linhas do RJ
# capital em STRJ2512.dbc). Escopo MVP restringe a estes municípios (ver
# docs/fontes.md#escopo-de-volume-para-o-mvp).
MUNICIPIOS_REFERENCIA_CODUFMUN = ("330455", "330380", "330350")


def parse_estabelecimento(raw: dict) -> dict:
    """Normaliza um registro bruto de estabelecimento para raw_cnes.estabelecimentos.

    Espera os campos do grupo "ST" (Estabelecimentos) do CNES, conforme
    retornado por `include.collectors.cnes.client.fetch_estabelecimentos`.
    Os campos são códigos DATASUS (ex.: TP_UNID, NAT_JUR); o de-para para
    valores legíveis fica para as camadas staging/dbt, não para o raw layer.

    Exemplo:
        >>> parse_estabelecimento(raw)["codigo_cnes"]
        '0033979'
    """
    valores = {}
    for campo in REQUIRED_FIELDS:
        try:
            valores[campo] = raw[campo]
        except KeyError as exc:
            raise ValueError(
                f"Registro de estabelecimento {raw!r} sem campo obrigatório {exc}; "
                f"esperado {REQUIRED_FIELDS}."
            ) from exc

    return {
        "codigo_cnes": valores["CNES"],
        "cod_municipio_ibge6": valores["CODUFMUN"],
        "tipo_pessoa": valores["PF_PJ"],
        "nivel_dependencia": valores["NIV_DEP"],
        "tipo_unidade": valores["TP_UNID"],
        "natureza_organizacao": valores["NATUREZA"],
        "natureza_juridica": valores["NAT_JUR"],
        "atividade_ensino": valores["ATIVIDAD"],
        "vinculo_sus": valores["VINC_SUS"],
        "tipo_gestao": valores["TPGESTAO"],
        "esfera_administrativa": valores["ESFERA_A"],
        "competencia": valores["COMPETEN"],
        "data_atualizacao": valores["DT_ATUAL"],
    }


def parse_estabelecimentos(raw_estabelecimentos: list[dict]) -> list[dict]:
    """Filtra pelos municípios de referência do MVP e normaliza cada registro.

    O filtro por município acontece aqui (não no client) porque é escopo de
    ingestão do MVP, não uma limitação da fonte: o arquivo CNES é distribuído
    por UF inteira, sem recorte por município.
    """
    dos_municipios = [
        raw
        for raw in raw_estabelecimentos
        if raw.get("CODUFMUN") in MUNICIPIOS_REFERENCIA_CODUFMUN
    ]
    return [parse_estabelecimento(raw) for raw in dos_municipios]


REQUIRED_EQUIPE_FIELDS = (
    "IDEQUIPE",
    "CNES",
    "CODUFMUN",
    "TIPO_EQP",
    "NOME_EQP",
    "DT_ATIVA",
    "DT_DESAT",
    "MOTDESAT",
    "TP_DESAT",
    "COMPETEN",
    "ID_AREA",
    "NOMEAREA",
    "ID_SEGM",
    "DESCSEGM",
    "TIPOSEGM",
)

# Tipos de equipe que compõem a Atenção Primária financiada pelo Previne
# Brasil (eSF=70, eCR=73, eAPP=74, eAP=76 — mesma tipologia usada pelo
# endpoint DEMAS de cadastro vinculado). Exclui eSB/odonto (71/72) e demais
# tipos (NASF, consultório de rua etc.) fora do escopo desta demanda.
# Confirmado contra amostra real: RJ dez/2025 tem 3.641 linhas tipo 70 e
# 1.911 tipo 71 estado inteiro.
TIPOS_EQUIPE_APS = ("70", "73", "74", "76")


def parse_equipe_aps(raw: dict) -> dict:
    """Normaliza uma equipe do grupo "EP" para as colunas de raw_cnes.equipes_aps.

    Espera os campos retornados por
    `include.collectors.cnes.client.fetch_equipes_aps`.

    Exemplo:
        >>> parse_equipe_aps(raw)["codigo_tipo_equipe"]
        '70'
    """
    valores = {}
    for campo in REQUIRED_EQUIPE_FIELDS:
        try:
            valores[campo] = raw[campo]
        except KeyError as exc:
            raise ValueError(
                f"Registro de equipe APS {raw!r} sem campo obrigatório {exc}; "
                f"esperado {REQUIRED_EQUIPE_FIELDS}."
            ) from exc
    return {
        "id_equipe": valores["IDEQUIPE"],
        "codigo_cnes": valores["CNES"],
        "cod_municipio_ibge6": valores["CODUFMUN"],
        "codigo_tipo_equipe": valores["TIPO_EQP"],
        "nome_equipe": valores["NOME_EQP"],
        "competencia_ativacao": valores["DT_ATIVA"],
        "competencia_desativacao": valores["DT_DESAT"],
        "motivo_desativacao": valores["MOTDESAT"],
        "tipo_desativacao": valores["TP_DESAT"],
        "competencia": valores["COMPETEN"],
        "id_area": valores["ID_AREA"],
        "nome_area": valores["NOMEAREA"],
        "id_segmento": valores["ID_SEGM"],
        "descricao_segmento": valores["DESCSEGM"],
        "tipo_segmento": valores["TIPOSEGM"],
    }


def parse_equipes_aps(raw_equipes: list[dict]) -> list[dict]:
    """Filtra equipes de APS dos municípios de referência e normaliza cada registro.

    Dois filtros, ambos de escopo de ingestão (não limitação da fonte): só
    os municípios do MVP (grupo "EP" vem por UF inteira, igual ao "ST") e só
    os tipos de equipe de APS (TIPOS_EQUIPE_APS) — o grupo "EP" traz também
    eSB/odonto e outros tipos fora desta demanda.
    """
    equipes_aps = [
        raw
        for raw in raw_equipes
        if raw.get("CODUFMUN") in MUNICIPIOS_REFERENCIA_CODUFMUN
        and raw.get("TIPO_EQP") in TIPOS_EQUIPE_APS
    ]
    return [parse_equipe_aps(raw) for raw in equipes_aps]


def parse_estabelecimento_detalhado(raw: dict) -> dict:
    """Normaliza um registro bruto de estabelecimento detalhado do DEMAS.

    Espera os campos retornados por
    `include.collectors.cnes.client.fetch_estabelecimentos_detalhados`. Só
    `codigo_cnes` é obrigatório — os demais campos vêm `None` na própria
    API quando o estabelecimento não os informou (confirmado contra
    amostra real).

    Exemplo:
        >>> parse_estabelecimento_detalhado(raw)["codigo_cnes"]
        '1082493'
    """
    try:
        codigo_cnes = raw["codigo_cnes"]
    except KeyError as exc:
        raise ValueError(
            f"Registro de estabelecimento detalhado {raw!r} sem campo "
            f"obrigatório {exc}; esperado codigo_cnes."
        ) from exc

    return {
        # Mesmo formato de 7 dígitos com zero à esquerda de
        # raw_cnes.estabelecimentos.codigo_cnes — a API retorna inteiro,
        # sem preenchimento (confirmado: 1082493 vem sem zero à esquerda
        # porque já tem 7 dígitos, mas códigos menores perderiam o zero
        # sem este ljust).
        "codigo_cnes": str(codigo_cnes).zfill(7),
        "nome_razao_social": raw.get("nome_razao_social"),
        "nome_fantasia": raw.get("nome_fantasia"),
        "codigo_tipo_unidade": raw.get("codigo_tipo_unidade"),
        "codigo_cep": raw.get("codigo_cep_estabelecimento"),
        "endereco": raw.get("endereco_estabelecimento"),
        "numero_endereco": raw.get("numero_estabelecimento"),
        "bairro": raw.get("bairro_estabelecimento"),
        "numero_telefone": raw.get("numero_telefone_estabelecimento"),
        "latitude": raw.get("latitude_estabelecimento_decimo_grau"),
        "longitude": raw.get("longitude_estabelecimento_decimo_grau"),
        "email": raw.get("endereco_email_estabelecimento"),
        "descricao_turno_atendimento": raw.get("descricao_turno_atendimento"),
        "faz_atendimento_ambulatorial_sus": raw.get(
            "estabelecimento_faz_atendimento_ambulatorial_sus"
        ),
        "descricao_esfera_administrativa": raw.get("descricao_esfera_administrativa"),
        "codigo_motivo_desabilitacao": raw.get(
            "codigo_motivo_desabilitacao_estabelecimento"
        ),
        "possui_centro_cirurgico": raw.get("estabelecimento_possui_centro_cirurgico"),
        "possui_centro_obstetrico": raw.get("estabelecimento_possui_centro_obstetrico"),
        "possui_centro_neonatal": raw.get("estabelecimento_possui_centro_neonatal"),
        "possui_atendimento_hospitalar": raw.get(
            "estabelecimento_possui_atendimento_hospitalar"
        ),
        "possui_servico_apoio": raw.get("estabelecimento_possui_servico_apoio"),
        "possui_atendimento_ambulatorial": raw.get(
            "estabelecimento_possui_atendimento_ambulatorial"
        ),
        "data_atualizacao": raw.get("data_atualizacao"),
    }


def parse_estabelecimentos_detalhados(raw_estabelecimentos: list[dict]) -> list[dict]:
    """Aplica parse_estabelecimento_detalhado a cada item da lista bruta do DEMAS."""
    return [parse_estabelecimento_detalhado(raw) for raw in raw_estabelecimentos]


def parse_rede_porte_municipio(raw_estabelecimentos: list[dict]) -> list[dict]:
    """Conta estabelecimentos de saúde por município, para todos os municípios da UF.

    Diferente de parse_estabelecimentos (que filtra pelos 3 municípios de
    referência do MVP), esta função não filtra município nenhum — alimenta
    a demanda "Comparação entre pares" (ver ROADMAP.md), que precisa de um
    universo maior que os 3 de referência. Reaproveita a mesma lista bruta
    do grupo "ST" já buscada por fetch_estabelecimentos, sem nova chamada à
    fonte. Contagem simples (1 estabelecimento = 1 unidade), sem distinguir
    porte por leitos/complexidade — o grupo "ST" não tem essa informação
    (ver docs/COLLECTOR_TEMPLATE.md).

    Exemplo:
        >>> parse_rede_porte_municipio(raw)[0]["quantidade_estabelecimentos"]
        17953
    """
    contagem: dict[str, int] = {}
    competencia = None
    for raw in raw_estabelecimentos:
        cod_municipio = raw["CODUFMUN"]
        contagem[cod_municipio] = contagem.get(cod_municipio, 0) + 1
        competencia = raw["COMPETEN"]

    return [
        {
            "cod_municipio_ibge6": cod_municipio,
            "competencia": competencia,
            "quantidade_estabelecimentos": quantidade,
        }
        for cod_municipio, quantidade in contagem.items()
    ]
