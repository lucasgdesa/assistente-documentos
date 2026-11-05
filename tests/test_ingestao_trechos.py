"""Trechos: CA6 (limite de tamanho, repetição de norma, artigo e caput)."""

import json

from comum.tipos import Trecho
from ingestao.parser import decodificar, parsear
from ingestao.trechos import escrever_jsonl, gerar_trechos
from tests.auxiliares import FIXTURE, frase, html_com, norma_teste

LIMITE = 600


def gerar(html: str, limite: int = LIMITE):
    res = parsear(html, "fic")
    return gerar_trechos(res, norma_teste(), limite)


def artigo_grande() -> str:
    corpo = f"<p>Art. 1º Caput fictício: {frase(0, 80)}</p>"
    for i in range(1, 4):
        corpo += f"<p>§ {i}º {frase(i, 300)}</p>"
    corpo += f"<p>§ 4º Parágrafo com incisos: {frase(9, 60)}</p>"
    for i, romano in enumerate(["I", "II", "III", "IV"], start=1):
        corpo += f"<p>{romano} - {frase(20 + i, 250)}</p>"
    corpo += "<p>Art. 2º Artigo curto fictício.</p>"
    return html_com(corpo)


def test_artigo_curto_gera_um_trecho_com_o_id_do_artigo():
    trechos, avisos = gerar(decodificar(FIXTURE.read_bytes()), limite=1500)
    por_id = {t.id: t for t in trechos}
    assert "fic.art1" in por_id and "fic.art54-a" in por_id
    assert not any(".parte" in t.id for t in trechos)
    assert avisos == []
    t = por_id["fic.art54-a"]
    assert t.dispositivos[0] == "fic.art54-a"
    assert "fic.art54-a.par2.inc3" in t.dispositivos
    assert t.norma == "FIC" and t.artigo == "54-A"
    assert t.data_coleta == "2000-01-02" and t.url.startswith("https://")
    assert t.hierarquia[-1].startswith("Capítulo II")


def test_ca6_artigo_grande_e_dividido_sem_passar_do_limite():
    trechos, avisos = gerar(artigo_grande())
    partes = [t for t in trechos if t.id.startswith("fic.art1.parte")]
    assert len(partes) >= 3
    assert avisos == []
    assert all(len(t.texto) <= LIMITE for t in trechos)


def test_ca6_cada_parte_repete_norma_artigo_e_caput():
    trechos, _ = gerar(artigo_grande())
    caput = "Art. 1º Caput fictício:"
    for t in (t for t in trechos if t.id.startswith("fic.art1.parte")):
        assert t.norma == "FIC" and t.artigo == "1"
        assert t.texto.startswith(caput)
        assert t.dispositivos[0] == "fic.art1"


def test_ca6_partes_cobrem_todos_os_dispositivos_sem_repeti_los():
    trechos, _ = gerar(artigo_grande())
    partes = [t for t in trechos if t.id.startswith("fic.art1.parte")]
    vistos = [d for t in partes for d in t.dispositivos if d != "fic.art1"]
    esperados = ["fic.art1.par1", "fic.art1.par2", "fic.art1.par3", "fic.art1.par4"]
    esperados += [f"fic.art1.par4.inc{i}" for i in range(1, 5)]
    assert vistos == esperados
    assert len({t.id for t in trechos}) == len(trechos)


def test_ca6_paragrafo_com_incisos_prefere_ficar_junto_quando_cabe():
    html = html_com(
        f"<p>Art. 1º {frase(0, 100)}</p><p>§ 1º {frase(1, 200)}</p>"
        f"<p>§ 2º Com incisos:</p><p>I - {frase(2, 100)}</p><p>II - {frase(3, 100)}</p>"
    )
    trechos, _ = gerar(html, limite=450)
    assert len(trechos) == 2
    assert trechos[1].dispositivos == (
        "fic.art1",
        "fic.art1.par2",
        "fic.art1.par2.inc1",
        "fic.art1.par2.inc2",
    )


def test_bloco_que_nao_cabe_gera_aviso_sem_perder_texto():
    html = html_com(f"<p>Art. 1º {frase(0, 50)}</p><p>§ 1º {frase(1, 400)}</p>")
    trechos, avisos = gerar(html, limite=200)
    assert avisos and "fic.art1" in avisos[0]
    assert "§ 1º" in " ".join(t.texto for t in trechos)


def test_vigencia_lista_notas_de_alteracao_sem_repetir():
    html = html_com(
        "<p>Art. 1º Caput. (Incluído pela Lei fictícia nº 1)</p>"
        "<p>§ 1º Um. (Incluído pela Lei fictícia nº 1)</p>"
        "<p>§ 2º Dois. (Redação dada pela Lei fictícia nº 2)</p>"
    )
    trechos, _ = gerar(html, limite=1500)
    vig = trechos[0].vigencia
    assert vig.startswith("Vigência fictícia | Alterações: ")
    assert vig.count("Incluído pela Lei fictícia nº 1") == 1
    assert "Redação dada pela Lei fictícia nº 2" in vig


def test_jsonl_tem_campos_do_trecho_e_termina_com_quebra(tmp_path):
    trechos, _ = gerar(decodificar(FIXTURE.read_bytes()), limite=1500)
    destino = tmp_path / "t.jsonl"
    escrever_jsonl(trechos, destino)
    bruto = destino.read_bytes()
    assert bruto.endswith(b"\n") and b"\r" not in bruto
    primeiro = json.loads(bruto.decode("utf-8").splitlines()[0])
    assert set(primeiro) == set(Trecho.__dataclass_fields__)
    assert isinstance(primeiro["dispositivos"], list)
