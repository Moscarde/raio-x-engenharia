"""Cliente para estabelecimentos de saúde (CNES) via pysus."""

from __future__ import annotations

import pysus

GROUP_ESTABELECIMENTOS = "ST"


def source_filename(uf: str, ano: int, mes: int) -> str:
    """Nome do arquivo DBC de origem no FTP do DATASUS para uf/ano/mes.

    Exemplo:
        >>> source_filename("RJ", 2025, 12)
        'STRJ2512.dbc'
    """
    return f"{GROUP_ESTABELECIMENTOS}{uf.upper()}{ano % 100:02d}{mes:02d}.dbc"


def fetch_estabelecimentos(uf: str, ano: int, mes: int) -> list[dict]:
    """Busca estabelecimentos de saúde do CNES (grupo Estabelecimentos) para uf/ano/mes.

    Não faz parsing: retorna um dict por estabelecimento com as colunas
    originais do grupo "ST", cru. `pysus` resolve o download FTP do arquivo
    DBC e a decompressão para tabular.

    Exemplo:
        >>> registros = fetch_estabelecimentos("RJ", 2025, 12)
        >>> registros[0]["CODUFMUN"]
        '330010'
    """
    dataframe = pysus.cnes(
        state=uf, year=ano, month=mes, group=GROUP_ESTABELECIMENTOS, as_dataframe=True
    )
    if dataframe.empty:
        raise RuntimeError(
            f"CNES não retornou registros para uf={uf!r}, ano={ano}, mes={mes}, "
            f"grupo={GROUP_ESTABELECIMENTOS!r} ({source_filename(uf, ano, mes)}); "
            "esperado DataFrame não vazio."
        )
    return dataframe.to_dict("records")
