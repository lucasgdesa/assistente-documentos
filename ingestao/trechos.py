"""Trechos por estrutura: um artigo por trecho, dividido se passar do limite.

Artigo acima do limite é dividido entre parágrafos ou incisos, repetindo o
caput em cada parte (norma e artigo ficam nos campos do trecho). Determinístico:
não usa relógio nem ordem de conjuntos.
"""

import json
from dataclasses import asdict
from pathlib import Path

from comum.tipos import Trecho
from ingestao.coletar import Norma
from ingestao.parser import Artigo, Dispositivo, Resultado


def _tamanho(caput: Dispositivo, blocos: list[list[Dispositivo]]) -> int:
    return len(montar_texto(caput, blocos))


def montar_texto(caput: Dispositivo, blocos: list[list[Dispositivo]]) -> str:
    partes = [caput.texto] + [d.texto for bloco in blocos for d in bloco]
    return "\n".join(partes)


def _blocos_atomicos(grupo: list[Dispositivo]) -> list[list[Dispositivo]]:
    """Parágrafo ou inciso, junto das suas alíneas."""
    blocos: list[list[Dispositivo]] = []
    for d in grupo:
        if d.tipo == "alinea" and blocos:
            blocos[-1].append(d)
        else:
            blocos.append([d])
    return blocos


def _grupos(artigo: Artigo) -> list[list[list[Dispositivo]]]:
    """Grupos do artigo (incisos do caput; cada parágrafo com seus incisos)."""
    grupos: list[list[Dispositivo]] = []
    chave = None
    for d in artigo.dispositivos[1:]:
        if d.grupo != chave:
            grupos.append([])
            chave = d.grupo
        grupos[-1].append(d)
    return [_blocos_atomicos(g) for g in grupos]


def dividir(artigo: Artigo, limite: int) -> list[list[list[Dispositivo]]]:
    """Partes do artigo; cada parte é uma lista de blocos (sem o caput)."""
    caput = artigo.dispositivos[0]
    grupos = _grupos(artigo)
    todos = [b for g in grupos for b in g]
    if not todos or _tamanho(caput, todos) <= limite:
        return [todos]
    partes: list[list[list[Dispositivo]]] = []
    atual: list[list[Dispositivo]] = []

    def fecha() -> None:
        nonlocal atual
        if atual:
            partes.append(atual)
        atual = []

    for grupo in grupos:
        if _tamanho(caput, atual + grupo) <= limite:
            atual = atual + grupo
        elif _tamanho(caput, grupo) <= limite:
            fecha()
            atual = list(grupo)
        else:
            fecha()
            for bloco in grupo:
                if atual and _tamanho(caput, atual + [bloco]) > limite:
                    fecha()
                atual = atual + [bloco]
    fecha()
    return partes


def _vigencia(norma: Norma, blocos: list[list[Dispositivo]], caput: Dispositivo) -> str:
    vistas: list[str] = []
    for d in [caput] + [d for b in blocos for d in b]:
        for nota in d.notas:
            texto = nota.strip("()").strip()
            if texto not in vistas:
                vistas.append(texto)
    if not vistas:
        return norma.vigencia
    return f"{norma.vigencia} | Alterações: {'; '.join(vistas)}"


def gerar_trechos(
    resultado: Resultado, norma: Norma, limite: int
) -> tuple[list[Trecho], list[str]]:
    """Trechos da norma e avisos (trechos que não couberam no limite)."""
    trechos: list[Trecho] = []
    avisos: list[str] = []
    for artigo in resultado.artigos:
        caput = artigo.dispositivos[0]
        partes = dividir(artigo, limite)
        for i, blocos in enumerate(partes, start=1):
            id_trecho = artigo.id if len(partes) == 1 else f"{artigo.id}.parte{i}"
            ids = (artigo.id,) + tuple(d.id for b in blocos for d in b)
            trecho = Trecho(
                id=id_trecho,
                norma=norma.sigla,
                artigo=artigo.numero,
                texto=montar_texto(caput, blocos),
                dispositivos=ids,
                hierarquia=artigo.hierarquia,
                vigencia=_vigencia(norma, blocos, caput),
                data_coleta=norma.data_coleta,
                url=norma.url,
            )
            if len(trecho.texto) > limite:
                avisos.append(
                    f"{id_trecho}: {len(trecho.texto)} caracteres, acima do limite"
                )
            trechos.append(trecho)
    return trechos, avisos


def escrever_jsonl(trechos: list[Trecho], caminho: Path) -> None:
    linhas = [json.dumps(asdict(t), ensure_ascii=False) for t in trechos]
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text("\n".join(linhas) + "\n", encoding="utf-8", newline="\n")
