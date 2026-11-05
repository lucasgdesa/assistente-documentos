"""Coleta manual: valida e registra os HTMLs salvos pelo navegador.

O Planalto recusa conexões por script nesta rede, então não há download aqui.
O manifesto `normas.yaml` guarda, por norma, o arquivo salvo, a data de coleta
e o SHA-256. Nada aqui lê o relógio: a data de coleta vem do manifesto.

Uso:
    python -m ingestao.coletar validar
    python -m ingestao.coletar registrar [--data AAAA-MM-DD]
"""

import argparse
import hashlib
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml

from ingestao.parser import Resultado, decodificar, detectar_charset, parsear

RAIZ = Path(__file__).resolve().parent.parent
MANIFESTO = RAIZ / "normas.yaml"
LIMITE_PADRAO = 1500


@dataclass(frozen=True)
class Norma:
    sigla: str
    id_prefixo: str
    titulo: str
    identificacao: str
    ementa: str
    url: str
    arquivo: str
    charset: str
    origem: str
    data_coleta: str
    sha256: str
    tamanho: int
    ultima_alteracao_observada: str
    vigencia: str
    correcoes_espaco: tuple[tuple[str, str], ...] = ()
    artigos_alteradores: tuple[str, ...] = ()


@dataclass(frozen=True)
class Manifesto:
    limite_caracteres: int
    normas: tuple[Norma, ...]


def _norma(item: dict) -> Norma:
    pares = tuple((str(a), str(b)) for a, b in item.pop("correcoes_espaco", []))
    alteradores = tuple(str(x) for x in item.pop("artigos_alteradores", []))
    return Norma(**item, correcoes_espaco=pares, artigos_alteradores=alteradores)


def carregar(caminho: Path = MANIFESTO) -> Manifesto:
    bruto = yaml.safe_load(caminho.read_text(encoding="utf-8"))
    normas = tuple(_norma(item) for item in bruto["normas"])
    return Manifesto(int(bruto.get("limite_caracteres", LIMITE_PADRAO)), normas)


def sha256_bytes(dados: bytes) -> str:
    return hashlib.sha256(dados).hexdigest()


def parsear_norma(norma: Norma, dados: bytes) -> Resultado:
    """Parse de um HTML com o prefixo e as correções da norma."""
    return parsear(
        decodificar(dados),
        norma.id_prefixo,
        norma.correcoes_espaco,
        norma.artigos_alteradores,
    )


def ler_arquivo(norma: Norma, raiz: Path = RAIZ) -> bytes:
    return (raiz / norma.arquivo).read_bytes()


def _url_salva(dados: bytes) -> str:
    achado = re.search(rb"saved from url=\(\d+\)(\S+)", dados[:2048])
    return achado.group(1).decode("ascii", errors="replace") if achado else ""


def identificacao_igual(a: str, b: str) -> bool:
    def limpar(x: str) -> str:
        return re.sub(r"\s+", " ", x).strip().rstrip(".").upper()

    return limpar(a) == limpar(b)


def validar_norma(norma: Norma, raiz: Path = RAIZ) -> list[str]:
    """Lista de problemas do arquivo salvo (vazia se estiver tudo certo)."""
    caminho = raiz / norma.arquivo
    if not caminho.is_file():
        return [f"{norma.sigla}: arquivo ausente: {norma.arquivo}"]
    dados = caminho.read_bytes()
    problemas = []
    if sha256_bytes(dados) != norma.sha256:
        problemas.append(f"{norma.sigla}: SHA-256 difere do manifesto")
    if len(dados) != norma.tamanho:
        problemas.append(f"{norma.sigla}: tamanho difere do manifesto")
    if detectar_charset(dados) != norma.charset:
        problemas.append(f"{norma.sigla}: charset declarado difere do manifesto")
    url = _url_salva(dados)
    if url and url != norma.url:
        problemas.append(f"{norma.sigla}: URL de origem do arquivo ({url}) difere")
    pagina = parsear_norma(norma, dados)
    if not identificacao_igual(pagina.identificacao, norma.identificacao):
        problemas.append(f"{norma.sigla}: a página não traz '{norma.identificacao}'")
    return problemas


def validar(manifesto: Manifesto, raiz: Path = RAIZ) -> list[str]:
    problemas: list[str] = []
    for norma in manifesto.normas:
        problemas.extend(validar_norma(norma, raiz))
    return problemas


def registrar(
    caminho: Path = MANIFESTO, raiz: Path = RAIZ, data_coleta: str | None = None
) -> list[str]:
    """Atualiza SHA-256, tamanho e charset (e a data, se informada) no manifesto.

    Edita só as linhas dos campos, para preservar o formato do arquivo.
    """
    manifesto = carregar(caminho)
    linhas = caminho.read_text(encoding="utf-8").split("\n")
    por_sigla = {n.sigla: n for n in manifesto.normas}
    atual: Norma | None = None
    novos: dict[str, str] = {}
    avisos: list[str] = []
    for i, linha in enumerate(linhas):
        achado = re.match(r"\s*- sigla:\s*(.+?)\s*$", linha)
        if achado:
            atual = por_sigla[achado.group(1).strip("\"'")]
            dados = ler_arquivo(atual, raiz)
            novos = {
                "sha256": f'"{sha256_bytes(dados)}"',
                "tamanho": str(len(dados)),
                "charset": detectar_charset(dados),
            }
            if data_coleta:
                novos["data_coleta"] = f'"{data_coleta}"'
            continue
        if atual is None:
            continue
        campo = re.match(r"(\s+)(\w+):", linha)
        if campo and campo.group(2) in novos:
            linhas[i] = f"{campo.group(1)}{campo.group(2)}: {novos[campo.group(2)]}"
    caminho.write_text("\n".join(linhas), encoding="utf-8", newline="\n")
    avisos.extend(validar(carregar(caminho), raiz))
    return avisos


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("acao", choices=["validar", "registrar"])
    ap.add_argument("--data", help="data de coleta AAAA-MM-DD (só em 'registrar')")
    args = ap.parse_args(argv)
    if args.acao == "validar":
        problemas = validar(carregar())
    else:
        problemas = registrar(data_coleta=args.data)
    for p in problemas:
        print(p, file=sys.stderr)
    if not problemas:
        print("ok: arquivos salvos conferem com normas.yaml")
    return 1 if problemas else 0


if __name__ == "__main__":
    raise SystemExit(main())
