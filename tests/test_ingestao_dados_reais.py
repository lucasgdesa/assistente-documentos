"""Invariantes dos trechos reais (HTMLs versionados em dados/brutos). Sem rede."""

import json
import re
from pathlib import Path

import pytest

from ingestao import __main__ as ingestao_main
from ingestao import coletar
from ingestao.relatorio import lacunas

RAIZ = coletar.RAIZ
MANIFESTO = coletar.carregar()
MARCAS = re.compile(
    r"\((?:Vetad|Revogad|Redação dada|Incluíd|Vide|Vigência|Regulamento)", re.IGNORECASE
)


@pytest.fixture(scope="module")
def trechos(tmp_path_factory) -> list[dict]:
    saida = tmp_path_factory.mktemp("real")
    codigo = ingestao_main.executar(
        coletar.MANIFESTO, saida / "t.jsonl", saida / "r.md", RAIZ
    )
    assert codigo == 0
    linhas = (saida / "t.jsonl").read_text(encoding="utf-8").splitlines()
    return [json.loads(x) for x in linhas]


def test_arquivos_salvos_conferem_com_o_manifesto():
    assert coletar.validar(MANIFESTO, RAIZ) == []


def test_identificadores_unicos(trechos):
    ids = [t["id"] for t in trechos]
    assert len(ids) == len(set(ids))
    dispositivos = [d for t in trechos for d in t["dispositivos"]]
    por_norma = {}
    for t in trechos:
        por_norma.setdefault(t["norma"], []).extend(t["dispositivos"][1:])
    for lista in por_norma.values():
        assert len(lista) == len(set(lista))
    assert dispositivos


def test_nenhum_trecho_acima_do_limite(trechos):
    assert max(len(t["texto"]) for t in trechos) <= MANIFESTO.limite_caracteres


def test_sem_marcas_de_revogado_nem_notas_no_texto(trechos):
    for t in trechos:
        assert not MARCAS.search(t["texto"]), t["id"]


def test_cada_trecho_traz_os_campos_obrigatorios(trechos):
    for t in trechos:
        assert t["norma"] and t["artigo"] and t["texto"] and t["url"]
        assert t["data_coleta"] == "2026-11-05"
        assert t["vigencia"]
        if t["norma"] != "Dec. 7.962":  # esse decreto não tem títulos nem capítulos
            assert t["hierarquia"]
        assert t["dispositivos"][0] == t["id"].split(".parte")[0]


def test_sequencia_de_artigos_sem_buracos_inesperados():
    for norma in MANIFESTO.normas:
        res = coletar.parsear_norma(norma, coletar.ler_arquivo(norma, RAIZ))
        assert lacunas(res.artigos_detectados) == [], norma.sigla


def test_artigos_removidos_nao_viram_trechos():
    for norma in MANIFESTO.normas:
        res = coletar.parsear_norma(norma, coletar.ler_arquivo(norma, RAIZ))
        mantidos = {a.id for a in res.artigos}
        inteiros = {r.id for r in res.removidos if r.rotulo.startswith("Art.") and r.id}
        assert not (mantidos & inteiros)
        assert len(mantidos) + len(inteiros) == len(res.artigos_detectados)


def test_trechos_versionados_estao_em_dia(tmp_path):
    destino = RAIZ / "dados" / "trechos.jsonl"
    if not destino.exists():
        pytest.skip("dados/trechos.jsonl ainda não gerado")
    novo = tmp_path / "t.jsonl"
    ingestao_main.executar(coletar.MANIFESTO, novo, tmp_path / "r.md", RAIZ)
    assert novo.read_bytes() == destino.read_bytes()
    relatorio = RAIZ / "dados" / "relatorio-ingestao.md"
    assert (tmp_path / "r.md").read_bytes() == Path(relatorio).read_bytes()


def test_correcoes_de_espacamento_do_manifesto_foram_usadas():
    for norma in MANIFESTO.normas:
        res = coletar.parsear_norma(norma, coletar.ler_arquivo(norma, RAIZ))
        assert not any("sem efeito" in a for a in res.anomalias), norma.sigla
        usadas = [a for a in res.ajustes if a.startswith("espaçamento corrigido")]
        assert len(usadas) == len(norma.correcoes_espaco)
