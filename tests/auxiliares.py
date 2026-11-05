"""Apoio dos testes de ingestão (dados fictícios)."""

from pathlib import Path

from ingestao.coletar import Norma

FIXTURE = Path(__file__).parent / "fixtures" / "norma_ficticia.html"


def norma_teste(prefixo: str = "fic", arquivo: str = "x.html", sha: str = "0") -> Norma:
    return Norma(
        sigla="FIC",
        id_prefixo=prefixo,
        titulo="Norma fictícia",
        identificacao="LEI Nº 0, DE 1 DE JANEIRO DE 2000.",
        ementa="Norma fictícia, inventada para testes automatizados.",
        url="https://exemplo.invalido/norma.html",
        arquivo=arquivo,
        charset="windows-1252",
        origem="fixture fictícia",
        data_coleta="2000-01-02",
        sha256=sha,
        tamanho=0,
        ultima_alteracao_observada="nenhuma",
        vigencia="Vigência fictícia",
    )


def html_com(corpo: str) -> str:
    return f"<html><body>{corpo}</body></html>"


def frase(n: int, tamanho: int) -> str:
    """Texto fictício de tamanho aproximado, único por n."""
    base = f"Frase fictícia {n} de enchimento para testar o limite de tamanho. "
    return (base * (tamanho // len(base) + 1))[:tamanho].rstrip() + "."
