"""Pipeline: CA4 (hash idêntico em duas execuções) e validação do manifesto."""

import hashlib
from pathlib import Path

from ingestao import __main__ as ingestao_main
from ingestao import coletar
from tests.test_ingestao_verificar import montar_projeto


def sha(caminho: Path) -> str:
    return hashlib.sha256(caminho.read_bytes()).hexdigest()


def rodar(manifesto: Path, destino: Path) -> tuple[Path, Path]:
    destino.mkdir()
    jsonl, relatorio = destino / "trechos.jsonl", destino / "relatorio.md"
    codigo = ingestao_main.executar(manifesto, jsonl, relatorio, manifesto.parent)
    assert codigo == 0
    return jsonl, relatorio


def test_ca4_duas_execucoes_geram_arquivos_identicos(tmp_path):
    manifesto = montar_projeto(tmp_path)
    a = rodar(manifesto, tmp_path / "a")
    b = rodar(manifesto, tmp_path / "b")
    assert sha(a[0]) == sha(b[0])
    assert sha(a[1]) == sha(b[1])


def test_ca4_data_de_coleta_vem_do_manifesto(tmp_path):
    manifesto = montar_projeto(tmp_path)
    jsonl, relatorio = rodar(manifesto, tmp_path / "saida")
    assert '"data_coleta": "2000-01-02"' in jsonl.read_text(encoding="utf-8")
    assert "2000-01-02" in relatorio.read_text(encoding="utf-8")


def test_relatorio_traz_contagens_e_paginas_de_origem(tmp_path):
    manifesto = montar_projeto(tmp_path)
    _, relatorio = rodar(manifesto, tmp_path / "saida")
    texto = relatorio.read_text(encoding="utf-8")
    assert "## Resumo" in texto and "## Páginas de origem" in texto
    assert "https://exemplo.invalido/norma.html" in texto
    assert "fic.art5" in texto and "revogado" in texto and "vetado" in texto
    assert "Lacunas na sequência de artigos" in texto


def test_arquivo_alterado_depois_do_registro_e_recusado(tmp_path, capsys):
    manifesto = montar_projeto(tmp_path)
    arquivo = tmp_path / "dados" / "brutos" / "ficticia.html"
    arquivo.write_bytes(arquivo.read_bytes() + b"<!-- alterado -->")
    codigo = ingestao_main.executar(
        manifesto, tmp_path / "t.jsonl", tmp_path / "r.md", tmp_path
    )
    assert codigo == 1
    assert "SHA-256 difere" in capsys.readouterr().err
    assert not (tmp_path / "t.jsonl").exists()


def test_validar_e_registrar_do_manifesto(tmp_path):
    manifesto = montar_projeto(tmp_path)
    assert coletar.validar(coletar.carregar(manifesto), tmp_path) == []
    assert coletar.registrar(manifesto, tmp_path, data_coleta="2001-02-03") == []
    assert coletar.carregar(manifesto).normas[0].data_coleta == "2001-02-03"
