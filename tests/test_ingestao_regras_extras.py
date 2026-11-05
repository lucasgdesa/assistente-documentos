"""Revisão do M1: alíneas sem inciso, marcas de remoção, notas de vigência e RF27."""

import json

import pytest

from ingestao import __main__ as ingestao_main
from ingestao import coletar, trechos
from ingestao.parser import decodificar, parsear
from tests.auxiliares import FIXTURE, html_com, norma_teste


def disps(res):
    return {d.id: d for a in res.artigos for d in a.dispositivos}


# H1: alíneas sem inciso aberto


def test_alinea_direto_sob_paragrafo():
    html = html_com(
        "<p>Art. 1º Caput.</p><p>Parágrafo único. Texto:</p>"
        "<p>a) primeira;</p><p>b) segunda.</p>"
    )
    res = disps(parsear(html, "x"))
    assert "x.art1.parunico.alia" in res and "x.art1.parunico.alib" in res
    assert all(not i.startswith(".") and ".." not in i for i in res)


def test_alinea_direto_sob_caput():
    html = html_com("<p>Art. 1º Caput:</p><p>a) primeira;</p><p>b) segunda.</p>")
    res = disps(parsear(html, "x"))
    assert "x.art1.alia" in res and "x.art1.alib" in res


def test_alinea_sob_inciso_continua_igual_e_nao_vaza_para_o_paragrafo_seguinte():
    html = html_com(
        "<p>Art. 1º Caput:</p><p>I - um:</p><p>a) alínea;</p>"
        "<p>§ 1º Parágrafo:</p><p>a) alínea do parágrafo.</p>"
    )
    res = disps(parsear(html, "x"))
    assert "x.art1.inc1.alia" in res
    assert "x.art1.par1.alia" in res


# M2: marcas de remoção


@pytest.mark.parametrize(
    ("trecho", "motivo"),
    [
        ("§ 1º (Suprimido)", "suprimido"),
        ("§ 1º (Sem efeito)", "sem_efeito"),
        ("§ 1º Sem efeito.", "sem_efeito"),
        (
            "§ 1º (Declarado inconstitucional pelo STF, na ADI fictícia)",
            "inconstitucional",
        ),
        (
            "§ 1º Declarado inconstitucional pelo STF na ADI fictícia.",
            "inconstitucional",
        ),
        ("§ 1º Revogado.", "revogado"),
        ("§ 1º Revogado pela Lei fictícia nº 1, de 2000.", "revogado"),
        ("§ 1º Texto fictício antigo. (Suprimido pela Lei fictícia nº 2)", "suprimido"),
    ],
)
def test_m2_marcas_de_remocao_nao_passam_como_vigentes(trecho, motivo):
    html = html_com(f"<p>Art. 1º Caput.</p><p>{trecho}</p><p>§ 2º Mantido.</p>")
    res = parsear(html, "x")
    assert "x.art1.par1" not in disps(res)
    assert "x.art1.par2" in disps(res)
    assert [r.motivo for r in res.removidos] == [motivo]


def test_m2_expressao_declarada_inconstitucional_gera_anomalia_e_mantem():
    html = html_com(
        "<p>Art. 1º Caput fictício. (Expressão declarada inconstitucional pelo STF)</p>"
    )
    res = parsear(html, "x")
    assert "x.art1" in disps(res)
    assert any("remoção parcial" in a for a in res.anomalias)


# L1: frase normal que começa com palavra de remoção


@pytest.mark.parametrize(
    "frase",
    [
        "Revogados os dispositivos em contrário, o fornecedor deve informar.",
        "Revogado o disposto no art. 5º, fica mantido o restante.",
        "Vetado o aumento, o consumidor pode reclamar.",
        "Sem efeito o contrato, as partes retornam ao estado anterior.",
        "Suprimida a cláusula, o contrato continua.",
    ],
)
def test_l1_frase_normal_nao_e_removida(frase):
    html = html_com(f"<p>Art. 1º Caput.</p><p>§ 1º {frase}</p>")
    res = parsear(html, "x")
    assert "x.art1.par1" in disps(res)
    assert not res.removidos


# M3: notas de vigência


def test_m3_nota_vide_vigencia_e_producao_de_efeito_ficam_registradas():
    html = html_com(
        "<p>Art. 1º Caput. (Vide Lei fictícia nº 1)</p>"
        "<p>§ 1º Um. (Vigência a partir de 1º.1.2099)</p>"
        "<p>§ 2º Dois. (Produção de efeitos)</p>"
        "<p>§ 3º Três. (Redação dada pela Lei fictícia nº 3) Vigência</p>"
    )
    res = parsear(html, "x")
    d = disps(res)
    assert d["x.art1"].avisos == ("(Vide Lei fictícia nº 1)",)
    assert d["x.art1.par1"].avisos == ("(Vigência a partir de 1º.1.2099)",)
    assert d["x.art1.par2"].avisos == ("(Produção de efeitos)",)
    assert d["x.art1.par3"].avisos == ("(Vigência)",)
    assert d["x.art1.par3"].notas == ("(Redação dada pela Lei fictícia nº 3)",)
    futuras = [a for a in res.anomalias if "vigência futura" in a]
    assert len(futuras) == 2


def test_m3_vigencia_futura_nao_aparece_como_em_vigor():
    html = html_com(
        "<p>Art. 1º Caput.</p><p>§ 1º Um. (Vigência a partir de 1º.1.2099)</p>"
        "<p>Art. 2º Normal. (Vide Lei fictícia nº 1)</p>"
    )
    res = parsear(html, "x")
    lista, _ = trechos.gerar_trechos(res, norma_teste(), 1500)
    por_id = {t.id: t for t in lista}
    assert por_id["x.art1"].vigencia.startswith("Vigência futura ou condicionada")
    assert "Vigência a partir de 1º.1.2099" in por_id["x.art1"].vigencia
    assert por_id["x.art2"].vigencia.startswith("Vigência fictícia")
    assert "Notas do Planalto: Vide Lei fictícia nº 1" in por_id["x.art2"].vigencia


def test_m3_nota_de_cabecalho_e_nota_sem_dispositivo_deixam_rastro():
    html = html_com(
        "<p>Art. 1º Caput.</p><p>CAPÍTULO II</p><p>NOME FICTÍCIO</p>"
        "<p>(Incluído pela Lei fictícia nº 9)</p><p>Art. 2º Outro.</p>"
        "<p>SEÇÃO I Nome (Vide Lei fictícia nº 8)</p>"
    )
    res = parsear(html, "x")
    assert any("nota sem dispositivo" in a for a in res.ajustes)
    assert any("nota de cabeçalho" in a and "Vide" in a for a in res.ajustes)


# RF27: artigos alteradores


@pytest.fixture(scope="module")
def com_alteradores():
    return parsear(decodificar(FIXTURE.read_bytes()), "fic", (), ("fic.art11",))


def test_rf27_alterador_sai_dos_artigos_e_nao_gera_dispositivos(com_alteradores):
    res = com_alteradores
    assert "fic.art11" not in {a.id for a in res.artigos}
    assert [a.id for a in res.alteradores] == ["fic.art11"]
    alt = res.alteradores[0]
    assert len(alt.dispositivos) == 1  # só o artigo, sem dispositivos internos
    assert "Art. 99" in alt.dispositivos[0].texto
    assert "Parágrafo único. Texto citado fictício." in alt.dispositivos[0].texto
    assert not [a for a in res.anomalias if "art11" in a]
    lista, _ = trechos.gerar_trechos(res, norma_teste(), 1500)
    assert not any(
        "art11" in t.id or "art11" in " ".join(t.dispositivos) for t in lista
    )


def test_rf27_texto_literal_sem_aspas_acrescentadas(com_alteradores):
    alt = trechos.gerar_alteradores(com_alteradores, norma_teste())[0]
    assert alt.cita_outra_norma is True
    assert alt.texto.count('"') == 2  # só as que já estavam no HTML
    assert alt.norma_citada is None  # o enunciado não nomeia a norma


def test_rf27_norma_citada_so_quando_consta_do_texto():
    html = html_com(
        "<p>Art. 1º O art. 5º da Lei nº 7.347, de 24 de julho de 1985, passa a ter:</p>"
        '<p>"Art. 5º Texto citado fictício."</p><p>Art. 2º Caput.</p>'
        "<p>Art. 3º Altera as Leis nº 1 e nº 2:</p><p>“Art. 9º Citado.”</p>"
    )
    res = parsear(html, "x", (), ("x.art1", "x.art3"))
    por_id = {t.id: t for t in trechos.gerar_alteradores(res, norma_teste("x"))}
    assert por_id["x.art1"].norma_citada == "Lei nº 7.347, de 24 de julho de 1985"
    assert por_id["x.art3"].norma_citada is None  # duas normas: ambíguo


def test_rf27_alerta_para_artigo_fora_da_lista_com_linha_citada_entre_aspas():
    res = parsear(decodificar(FIXTURE.read_bytes()), "fic")
    alertas = [a for a in res.anomalias if a.startswith("alerta RF27")]
    assert any("fic.art11" in a and "marcador" in a for a in alertas)


def test_rf27_alerta_para_linha_citada_sem_aspas_por_numeracao_fora_de_sequencia():
    html = html_com(
        "<p>Art. 1º Altera outra norma:</p><p>Art. 99. Linha citada sem aspas.</p>"
        "<p>Art. 2º Normal.</p>"
    )
    res = parsear(html, "x")
    alertas = [a for a in res.anomalias if a.startswith("alerta RF27")]
    assert any("art. 99" in a and "fora de sequência" in a for a in alertas)
    assert any("art. 2 após art. 99" in a for a in alertas)


def test_rf27_alerta_para_paragrafo_fora_de_sequencia():
    html = html_com("<p>Art. 1º Caput.</p><p>§ 1º Um.</p><p>§ 4º Quatro.</p>")
    alertas = parsear(html, "x").anomalias
    assert any("§ 4 após § 1" in a for a in alertas)


def test_rf27_sem_alerta_quando_a_sequencia_esta_certa_com_vetados_e_letras():
    html = html_com(
        "<p>Art. 1º Caput.</p><p>§ 1º (Vetado).</p><p>§ 2º Dois.</p>"
        "<p>Art. 1º-A. Letra.</p><p>Art. 2º Dois.</p>"
    )
    assert not [a for a in parsear(html, "x").anomalias if "RF27" in a]


def test_rf27_alterador_listado_e_ausente_gera_alerta():
    res = parsear(html_com("<p>Art. 1º Caput.</p>"), "x", (), ("x.art7",))
    assert any("não encontrado: x.art7" in a for a in res.anomalias)


def test_rf27_dispositivo_proprio_de_alterador_vira_texto_literal():
    html = html_com(
        "<p>Art. 1º Altera outra norma:</p><p>§ 1º Linha própria.</p>"
        "<p>I - item.</p><p>Art. 2º Normal.</p>"
    )
    res = parsear(html, "x", (), ("x.art1",))
    assert [a.id for a in res.artigos] == ["x.art2"]
    texto = res.alteradores[0].dispositivos[0].texto
    assert "Linha própria" in texto and "item" in texto


def test_rf27_pipeline_grava_arquivo_dos_alteradores(tmp_path):
    (tmp_path / "dados" / "brutos").mkdir(parents=True)
    (tmp_path / "dados" / "brutos" / "ficticia.html").write_bytes(FIXTURE.read_bytes())
    manifesto = tmp_path / "normas.yaml"
    manifesto.write_text(
        "limite_caracteres: 1500\n"
        "normas:\n"
        "  - sigla: FIC\n    id_prefixo: fic\n    titulo: Norma fictícia\n"
        '    identificacao: "LEI Nº 0, DE 1 DE JANEIRO DE 2000."\n'
        "    ementa: x\n    url: https://exemplo.invalido/n.html\n"
        "    arquivo: dados/brutos/ficticia.html\n    charset: windows-1252\n"
        "    origem: fixture\n"
        '    data_coleta: "2000-01-02"\n    sha256: "0"\n    tamanho: 0\n'
        "    ultima_alteracao_observada: nenhuma\n    vigencia: fictícia\n"
        "    artigos_alteradores: [fic.art11]\n",
        encoding="utf-8",
    )
    assert coletar.registrar(manifesto, tmp_path) == []
    saida = tmp_path / "t.jsonl"
    assert ingestao_main.executar(manifesto, saida, tmp_path / "r.md", tmp_path) == 0
    ids = [json.loads(x)["id"] for x in saida.read_text(encoding="utf-8").splitlines()]
    assert "fic.art11" not in ids
    alt = json.loads(
        (tmp_path / "trechos_alteradores.jsonl").read_text(encoding="utf-8")
    )
    assert alt["id"] == "fic.art11" and alt["cita_outra_norma"] is True
    assert "norma_citada" in alt and alt["norma_citada"] is None
    relatorio = (tmp_path / "r.md").read_text(encoding="utf-8")
    assert "## Artigos alteradores (RF27)" in relatorio and "fic.art11" in relatorio
    assert "fic.art11 traz linha citada" not in relatorio


def test_rf27_relatorio_lista_alertas_de_artigo_fora_da_lista(tmp_path):
    (tmp_path / "dados" / "brutos").mkdir(parents=True)
    (tmp_path / "dados" / "brutos" / "ficticia.html").write_bytes(FIXTURE.read_bytes())
    manifesto = tmp_path / "normas.yaml"
    manifesto.write_text(
        "limite_caracteres: 1500\n"
        "normas:\n"
        "  - sigla: FIC\n    id_prefixo: fic\n    titulo: Norma fictícia\n"
        '    identificacao: "LEI Nº 0, DE 1 DE JANEIRO DE 2000."\n'
        "    ementa: x\n    url: https://exemplo.invalido/n.html\n"
        "    arquivo: dados/brutos/ficticia.html\n    charset: windows-1252\n"
        "    origem: fixture\n"
        '    data_coleta: "2000-01-02"\n    sha256: "0"\n    tamanho: 0\n'
        "    ultima_alteracao_observada: nenhuma\n    vigencia: fictícia\n",
        encoding="utf-8",
    )
    assert coletar.registrar(manifesto, tmp_path) == []
    assert (
        ingestao_main.executar(
            manifesto, tmp_path / "t.jsonl", tmp_path / "r.md", tmp_path
        )
        == 0
    )
    relatorio = (tmp_path / "r.md").read_text(encoding="utf-8")
    assert "alerta RF27: fic.art11 traz linha citada" in relatorio
