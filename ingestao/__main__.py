"""Ingestão completa: valida os HTMLs salvos, faz o parse e grava os trechos.

Uso: python -m ingestao [--saida dados/trechos.jsonl] [--relatorio dados/relatorio-ingestao.md]
"""

import argparse
import sys
from pathlib import Path

from comum.tipos import Trecho
from ingestao import coletar, relatorio, trechos
from ingestao.parser import Resultado

RAIZ = coletar.RAIZ


def executar(
    manifesto_caminho: Path, saida: Path, caminho_relatorio: Path, raiz: Path = RAIZ
) -> int:
    manifesto = coletar.carregar(manifesto_caminho)
    problemas = coletar.validar(manifesto, raiz)
    if problemas:
        for p in problemas:
            print(p, file=sys.stderr)
        return 1
    dados: list[tuple[coletar.Norma, Resultado, list[Trecho]]] = []
    avisos: list[str] = []
    todos: list[Trecho] = []
    for norma in manifesto.normas:
        res = coletar.parsear_norma(norma, coletar.ler_arquivo(norma, raiz))
        lista, aviso = trechos.gerar_trechos(res, norma, manifesto.limite_caracteres)
        dados.append((norma, res, lista))
        avisos.extend(f"{norma.sigla}: {a}" for a in aviso)
        todos.extend(lista)
    ids = [t.id for t in todos]
    if len(ids) != len(set(ids)):
        print("identificadores de trecho repetidos", file=sys.stderr)
        return 1
    trechos.escrever_jsonl(todos, saida)
    texto = relatorio.gerar(dados, manifesto.limite_caracteres, avisos)
    caminho_relatorio.parent.mkdir(parents=True, exist_ok=True)
    caminho_relatorio.write_text(texto, encoding="utf-8", newline="\n")
    print(f"{len(todos)} trechos em {saida}; relatório em {caminho_relatorio}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Gera dados/trechos.jsonl e o relatório")
    ap.add_argument("--manifesto", type=Path, default=RAIZ / "normas.yaml")
    ap.add_argument("--saida", type=Path, default=RAIZ / "dados" / "trechos.jsonl")
    ap.add_argument(
        "--relatorio", type=Path, default=RAIZ / "dados" / "relatorio-ingestao.md"
    )
    args = ap.parse_args(argv)
    return executar(args.manifesto, args.saida, args.relatorio)


if __name__ == "__main__":
    raise SystemExit(main())
