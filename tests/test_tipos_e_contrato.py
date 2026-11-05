import dataclasses
import inspect

import pytest

from comum.contrato import Nucleo
from comum.tipos import Citacao, Resposta, Trecho


def test_citacao_formata_artigo_paragrafo_e_inciso():
    c = Citacao("cdc.art18.par1.inc2", "CDC", "18", "§ 1º", "inciso II")
    assert c.formatar() == "CDC, art. 18, § 1º, inciso II"


def test_citacao_so_artigo_e_paragrafo_unico():
    assert Citacao("x", "Dec. 7.962", "5").formatar() == "Dec. 7.962, art. 5"
    c = Citacao("x", "CDC", "54-A", paragrafo="parágrafo único")
    assert c.formatar() == "CDC, art. 54-A, parágrafo único"


def test_resposta_padrao_e_imutavel():
    r = Resposta(status="sem_resposta", texto="x")
    assert r.citacoes == () and r.caso_pessoal is False
    with pytest.raises(dataclasses.FrozenInstanceError):
        r.texto = "y"  # type: ignore[misc]


def test_trecho_tem_campos_do_prd():
    campos = {f.name for f in dataclasses.fields(Trecho)}
    assert {"id", "norma", "artigo", "dispositivos", "hierarquia"} <= campos
    assert {"vigencia", "data_coleta", "texto"} <= campos


def test_contrato_tem_assinaturas_previstas():
    buscar = inspect.signature(Nucleo.buscar)
    assert list(buscar.parameters) == ["self", "pergunta", "k"]
    assert buscar.parameters["k"].default == 5
    assert list(inspect.signature(Nucleo.responder).parameters) == [
        "self",
        "pergunta",
    ]
