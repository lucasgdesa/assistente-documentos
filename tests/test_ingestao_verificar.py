"""Verificador de atualização: CA7 (relata artigo alterado; sem mudança, sem relato)."""

from pathlib import Path

from ingestao import coletar, verificar
from ingestao.parser import decodificar, parsear
from tests.auxiliares import FIXTURE, norma_teste


def montar_projeto(tmp_path: Path) -> Path:
    """Projeto temporário com a fixture fictícia registrada em um normas.yaml."""
    (tmp_path / "dados" / "brutos").mkdir(parents=True)
    copia = tmp_path / "dados" / "brutos" / "ficticia.html"
    copia.write_bytes(FIXTURE.read_bytes())
    manifesto = tmp_path / "normas.yaml"
    manifesto.write_text(
        "limite_caracteres: 1500\n"
        "normas:\n"
        "  - sigla: FIC\n"
        "    id_prefixo: fic\n"
        "    titulo: Norma fictícia\n"
        '    identificacao: "LEI Nº 0, DE 1 DE JANEIRO DE 2000."\n'
        "    ementa: Norma fictícia\n"
        "    url: https://exemplo.invalido/norma.html\n"
        "    arquivo: dados/brutos/ficticia.html\n"
        "    charset: windows-1252\n"
        "    origem: fixture fictícia\n"
        '    data_coleta: "2000-01-02"\n'
        '    sha256: "0"\n'
        "    tamanho: 0\n"
        "    ultima_alteracao_observada: nenhuma\n"
        "    vigencia: fictícia\n"
        "    artigos_alteradores: [fic.art11]\n",
        encoding="utf-8",
    )
    assert coletar.registrar(manifesto, tmp_path) == []
    return manifesto


def novo_arquivo(tmp_path: Path, de: str, para: str) -> Path:
    texto = FIXTURE.read_bytes().decode("cp1252").replace(de, para)
    assert texto != FIXTURE.read_bytes().decode("cp1252")
    destino = tmp_path / "novo.html"
    destino.write_bytes(texto.encode("cp1252"))
    return destino


def test_ca7_artigo_alterado_e_relatado(tmp_path, capsys):
    manifesto = montar_projeto(tmp_path)
    novo = novo_arquivo(
        tmp_path, "Texto fictício número nove.", "Texto fictício nove, mudado."
    )
    codigo = verificar.main(["fic", str(novo), "--manifesto", str(manifesto)])
    saida = capsys.readouterr().out
    assert codigo == 1
    assert "fic.art9" in saida and "Artigos afetados: art9" in saida


def test_ca7_sem_alteracao_nao_relata(tmp_path, capsys):
    manifesto = montar_projeto(tmp_path)
    codigo = verificar.main(["fic", str(FIXTURE), "--manifesto", str(manifesto)])
    assert codigo == 0
    assert "sem diferenças" in capsys.readouterr().out


def test_ca7_so_o_html_muda_sem_mudar_o_texto_nao_relata(tmp_path):
    manifesto = montar_projeto(tmp_path)
    reserializado = novo_arquivo(tmp_path, "<p>Art. 9º", "<p>\n  Art.  9º")
    norma = coletar.carregar(manifesto).normas[0]
    assert verificar.verificar(norma, reserializado, tmp_path).vazio


def test_ca7_dispositivo_novo_e_nova_revogacao_sao_relatados(tmp_path):
    manifesto = montar_projeto(tmp_path)
    norma = coletar.carregar(manifesto).normas[0]
    novo = novo_arquivo(
        tmp_path,
        "<p>Art. 12. Texto fictício número doze.</p>",
        "<p>Art. 12. (Revogado pela Lei fictícia nº 9)</p><p>Art. 13. Texto fictício novo.</p>",
    )
    dif = verificar.verificar(norma, novo, tmp_path)
    assert "fic.art13" in dif.adicionados
    assert "fic.art12" in dif.removidos
    assert any("fic.art12" in r for r in dif.novas_remocoes)


def test_arquivo_de_outra_norma_e_rejeitado(tmp_path, capsys):
    manifesto = montar_projeto(tmp_path)
    outro = novo_arquivo(
        tmp_path,
        "LEI Nº 0, DE 1 DE JANEIRO DE 2000.",
        "LEI Nº 1, DE 2 DE JANEIRO DE 2000.",
    )
    codigo = verificar.main(["fic", str(outro), "--manifesto", str(manifesto)])
    assert codigo == 2
    assert "erro" in capsys.readouterr().err


def test_norma_desconhecida_e_erro_de_uso(tmp_path, capsys):
    manifesto = montar_projeto(tmp_path)
    codigo = verificar.main(["xyz", str(FIXTURE), "--manifesto", str(manifesto)])
    assert codigo == 2


def test_comparar_resultados_iguais_nao_tem_diferencas():
    res = parsear(decodificar(FIXTURE.read_bytes()), "fic")
    assert verificar.comparar(res, res).vazio
    assert norma_teste().sigla == "FIC"


def test_ca7_artigo_novo_no_fim_da_norma_e_relatado(tmp_path, capsys):
    manifesto = montar_projeto(tmp_path)
    novo = novo_arquivo(
        tmp_path,
        "<p>Brasília, 1 de janeiro de 2000.</p>",
        "<p>Art. 55. Texto fictício de artigo novo.</p>"
        "<p>Brasília, 1 de janeiro de 2000.</p>",
    )
    codigo = verificar.main(["fic", str(novo), "--manifesto", str(manifesto)])
    saida = capsys.readouterr().out
    assert codigo == 1
    assert "Dispositivos novos (1)" in saida and "fic.art55" in saida
    assert "Artigos afetados: art55" in saida


def test_ca7_artigo_alterador_continua_sendo_comparado(tmp_path, capsys):
    manifesto = montar_projeto(tmp_path)
    novo = novo_arquivo(
        tmp_path, "Texto citado de outra norma fictícia.", "Texto citado mudado."
    )
    codigo = verificar.main(["fic", str(novo), "--manifesto", str(manifesto)])
    assert codigo == 1
    assert "fic.art11" in capsys.readouterr().out
