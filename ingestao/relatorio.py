"""Relatório da ingestão (markdown determinístico, sem data nem relógio)."""

import re
from collections import Counter

from comum.tipos import Trecho
from ingestao.coletar import Norma
from ingestao.parser import Resultado

CABECALHO_RESUMO = (
    "| Norma | Artigos no HTML | Artigos mantidos | Artigos removidos | "
    "Dispositivos mantidos | Dispositivos removidos | Trechos | Maior trecho |"
)


def lacunas(detectados: list[str]) -> list[str]:
    """Números ou letras de artigo ausentes na sequência dos artigos detectados."""
    numeros: dict[int, list[str]] = {}
    for chave in detectados:
        base, _, letra = chave.partition("-")
        numeros.setdefault(int(base), [])
        if letra:
            numeros[int(base)].append(letra)
    achados: list[str] = []
    if not numeros:
        return achados
    for n in range(min(numeros), max(numeros) + 1):
        if n not in numeros:
            achados.append(str(n))
    for n, letras in sorted(numeros.items()):
        esperadas = [chr(ord("A") + i) for i in range(len(letras))]
        if sorted(letras) != esperadas:
            faltam = [x for x in esperadas if x not in letras]
            achados.append(
                f"{n}-letras (presentes: {', '.join(sorted(letras))}; faltam: {', '.join(faltam) or '?'})"
            )
    return achados


def _celula(texto: str) -> str:
    return re.sub(r"\s+", " ", texto).replace("|", "\\|")


def gerar(
    dados: list[tuple[Norma, Resultado, list[Trecho]]], limite: int, avisos: list[str]
) -> str:
    linhas = ["# Relatório de ingestão", ""]
    linhas += [
        "Gerado por `python -m ingestao`. Não editar à mão.",
        f"Limite de tamanho do trecho: {limite} caracteres.",
        "",
        "## Resumo",
        "",
        CABECALHO_RESUMO,
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    totais = [0] * 7
    for norma, res, trechos in dados:
        inteiros = sum(
            1
            for r in res.removidos
            if r.rotulo.startswith("Art.") and r.motivo != "subordinado"
        )
        mantidos = sum(len(a.dispositivos) for a in res.artigos)
        maior = max((len(t.texto) for t in trechos), default=0)
        linha = [
            len(res.artigos_detectados),
            len(res.artigos),
            inteiros,
            mantidos,
            len(res.removidos),
            len(trechos),
        ]
        for i, v in enumerate(linha):
            totais[i] += v
        totais[6] = max(totais[6], maior)
        linhas.append(
            f"| {norma.sigla} | " + " | ".join(str(v) for v in linha) + f" | {maior} |"
        )
    linhas.append("| **Total** | " + " | ".join(f"**{v}**" for v in totais) + " |")
    linhas += ["", "## Páginas de origem", ""]
    for norma, res, _ in dados:
        linhas += [
            f"### {norma.sigla}",
            "",
            f"- Norma: {norma.titulo}",
            f"- Identificação na página: {_celula(res.identificacao)}",
            f"- Ementa na página: {_celula(res.ementa)}",
            f"- URL oficial: {norma.url}",
            f"- Arquivo salvo: `{norma.arquivo}` ({norma.tamanho} bytes, {norma.charset})",
            f"- SHA-256: `{norma.sha256}`",
            f"- Origem: {norma.origem}",
            f"- Data de coleta (do manifesto): {norma.data_coleta}",
            f"- Rodapé da página: {_celula(res.rodape)}",
            f"- Última alteração observada: {norma.ultima_alteracao_observada}",
            "",
        ]
    linhas += ["## Dispositivos removidos", ""]
    for norma, res, _ in dados:
        contagem = Counter(r.motivo for r in res.removidos)
        resumo = ", ".join(f"{k}: {v}" for k, v in sorted(contagem.items())) or "nenhum"
        linhas += [
            f"### {norma.sigla}",
            "",
            f"Total: {len(res.removidos)} ({resumo}).",
            "",
        ]
        if res.removidos:
            linhas += [
                "| Identificador | Rótulo | Motivo | Artigo | Marca |",
                "| --- | --- | --- | --- | --- |",
            ]
            for r in res.removidos:
                linhas.append(
                    f"| {r.id or '-'} | {_celula(r.rotulo)} | {r.motivo} | {r.artigo} | {_celula(r.marca)[:120]} |"
                )
            linhas.append("")
    linhas += ["## Verificações da estrutura", ""]
    for norma, res, trechos in dados:
        buracos = lacunas(res.artigos_detectados)
        dividas = sum(1 for t in trechos if ".parte" in t.id)
        ids = [t.id for t in trechos]
        linhas += [
            f"### {norma.sigla}",
            "",
            f"- Lacunas na sequência de artigos: {', '.join(buracos) if buracos else 'nenhuma'}",
            f"- Trechos de artigos divididos (partes): {dividas}",
            f"- Identificadores de trecho repetidos: {len(ids) - len(set(ids))}",
            f"- Ajustes de texto: {_resumo(res.ajustes)}",
            f"- Anomalias: {'; '.join(_celula(a) for a in res.anomalias) or 'nenhuma'}",
            "",
        ]
    linhas += ["## Avisos", ""]
    linhas += [f"- {a}" for a in avisos] or ["Nenhum."]
    return "\n".join(linhas) + "\n"


def _resumo(ajustes: list[str]) -> str:
    contagem = Counter(ajustes)
    return "; ".join(f"{k} (x{v})" for k, v in sorted(contagem.items())) or "nenhum"
