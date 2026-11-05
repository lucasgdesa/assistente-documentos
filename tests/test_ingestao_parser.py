"""Parser: CA5 (tachado, revogado, vetado) e CA6 (identificadores) com fixture fictícia."""

from pathlib import Path

import pytest

from ingestao.parser import ErroParser, decodificar, parsear

FIXTURE = Path(__file__).parent / "fixtures" / "norma_ficticia.html"


@pytest.fixture(scope="module")
def res():
    return parsear(decodificar(FIXTURE.read_bytes()), "fic")


def ids(res):
    return [d.id for a in res.artigos for d in a.dispositivos]


def textos(res):
    return "\n".join(d.texto for a in res.artigos for d in a.dispositivos)


def test_decodifica_windows_1252():
    assert "Fictício" in decodificar(FIXTURE.read_bytes())


def test_cabecalho_e_hierarquia(res):
    assert res.identificacao.startswith("LEI Nº 0")
    assert res.ementa.startswith("Norma fictícia")
    art1 = res.artigos[0]
    assert art1.hierarquia == (
        "Título I - Das Disposições de Teste",
        "Capítulo I - Do Capítulo Fictício",
    )
    art11 = next(a for a in res.artigos if a.numero == "11")
    assert art11.hierarquia[-1] == "Capítulo II - DO SEGUNDO CAPÍTULO FICTÍCIO"


def test_ids_unicos_e_artigo_com_letra(res):
    todos = ids(res)
    assert len(todos) == len(set(todos))
    assert "fic.art54-a" in todos
    assert "fic.art54-a.par2.inc3" in todos
    assert "fic.art54-b" in todos


def test_ordinais_variados_viram_o_mesmo_rotulo(res):
    art1 = {d.id: d.texto for d in res.artigos[0].dispositivos}
    assert art1["fic.art1.par2"].startswith("§ 2º Parágrafo")
    assert art1["fic.art1.par3"].startswith("§ 3º Parágrafo")
    assert art1["fic.art1.par4"].startswith("§ 4º Parágrafo")


def test_incisos_e_alineas(res):
    todos = ids(res)
    assert "fic.art1.inc1" in todos
    assert "fic.art1.inc1.alia" in todos
    assert "fic.art1.inc2" in todos
    inc1 = next(d for d in res.artigos[0].dispositivos if d.id == "fic.art1.inc1")
    assert inc1.texto.startswith("I - ")


def test_paragrafo_unico(res):
    assert "fic.art2.parunico" in ids(res)


def test_ordinal_tachado_nao_e_revogacao(res):
    art2 = next(a for a in res.artigos if a.numero == "2")
    assert art2.dispositivos[0].texto.startswith("Art. 2º Texto")
    assert not any(r.artigo == "2" for r in res.removidos)


def test_ca5_tachado_nao_chega_aos_trechos(res):
    saida = textos(res)
    assert "antigo fictício" not in saida
    assert "riscado" not in saida
    tachados = [r for r in res.removidos if r.motivo == "tachado"]
    assert len(tachados) == 4  # parágrafo inteiro, trecho parcial, classe CSS, estilo
    assert any("antigo fictício" in r.marca for r in tachados)


def test_ca5_versao_nova_substitui_a_tachada(res):
    novo = next(d for d in res.artigos[2].dispositivos if d.id == "fic.art3.par1")
    assert "Texto novo fictício" in novo.texto
    assert novo.notas == ("(Redação dada pela Lei fictícia nº 1, de 2001)",)
    assert "Redação dada" not in novo.texto


def test_ca5_revogado_e_vetado_fora_e_no_relatorio(res):
    removidos = {r.id: r for r in res.removidos if r.id}
    assert removidos["fic.art5"].motivo == "revogado"
    assert removidos["fic.art6"].motivo == "vetado"
    assert removidos["fic.art7.par1"].motivo == "vetado"
    assert removidos["fic.art8.inc2"].motivo == "revogado"  # sem tachado, só nota
    for chave in ("fic.art5", "fic.art6", "fic.art7.par1", "fic.art8.inc2"):
        assert chave not in ids(res)
    numeros = {a.numero for a in res.artigos}
    assert not ({"5", "6"} & numeros)
    assert "Revogado" not in textos(res) and "Vetado" not in textos(res)


def test_dispositivo_subordinado_a_removido_tambem_sai(res):
    sub = [r for r in res.removidos if r.motivo == "subordinado"]
    assert len(sub) == 1 and sub[0].artigo == "7"
    art7 = next(a for a in res.artigos if a.numero == "7")
    assert [d.id for d in art7.dispositivos] == ["fic.art7", "fic.art7.par2"]


def test_notas_nao_ficam_no_texto(res):
    art10 = next(a for a in res.artigos if a.numero == "10")
    texto = art10.dispositivos[0].texto
    assert texto == "Art. 10. Texto fictício número dez."
    assert art10.dispositivos[0].notas == (
        "(Incluído pela Lei fictícia nº 4, de 2004)",
    )


def test_emenda_citada_nao_vira_dispositivo(res):
    art11 = next(a for a in res.artigos if a.numero == "11")
    assert [d.id for d in art11.dispositivos] == ["fic.art11"]
    assert "Art. 99" in art11.dispositivos[0].texto
    assert "fic.art99" not in ids(res)


def test_rodape_e_artigos_detectados(res):
    assert res.rodape.startswith("Este texto não substitui")
    assert "5" in res.artigos_detectados and "6" in res.artigos_detectados


def test_identificador_duplicado_falha():
    html = "<html><body><p>Art. 1º A.</p><p>Art. 1º B.</p></body></html>"
    with pytest.raises(ErroParser):
        parsear(html, "x")


def test_numeral_partido_pela_serializacao_e_ajustado():
    html = "<html><body><p>Art. 1º Texto:</p><p>I - um;</p><p>I I - dois.</p></body></html>"
    res = parsear(html, "x")
    assert [d.id for d in res.artigos[0].dispositivos] == [
        "x.art1",
        "x.art1.inc1",
        "x.art1.inc2",
    ]
    assert any("numeral partido" in a for a in res.ajustes)


def test_pontuacao_solta_pela_serializacao_e_normalizada():
    html = "<html><body><p>Art. 1º Veja o art. 2º , 3º e 4º .</p></body></html>"
    texto = parsear(html, "x").artigos[0].dispositivos[0].texto
    assert texto == "Art. 1º Veja o art. 2º, 3º e 4º."


def test_correcao_de_espacamento_e_registrada():
    html = "<html><body><p>Art. 1º Texto ante riores aqui.</p></body></html>"
    res = parsear(html, "x", (("ante riores", "anteriores"),))
    assert res.artigos[0].dispositivos[0].texto == "Art. 1º Texto anteriores aqui."
    assert any("espaçamento corrigido" in a for a in res.ajustes)


def test_correcao_sem_efeito_vira_anomalia():
    html = "<html><body><p>Art. 1º Texto.</p></body></html>"
    res = parsear(html, "x", (("não existe", "x"),))
    assert any("sem efeito" in a for a in res.anomalias)
