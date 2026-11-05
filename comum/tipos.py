"""Tipos compartilhados entre ingestão, núcleo de RAG e aplicação."""

from dataclasses import dataclass, field
from typing import Literal

Status = Literal["respondida", "sem_resposta", "limite"]


@dataclass(frozen=True)
class Trecho:
    """Parte de uma norma, geralmente um artigo, usada na busca."""

    id: str  # identificador canônico, ex.: "cdc.art54-a.par2.inc3"
    norma: str  # sigla da norma, ex.: "CDC"
    artigo: str  # ex.: "54-A"
    texto: str
    dispositivos: tuple[str, ...] = ()  # ids dos dispositivos contidos
    hierarquia: tuple[str, ...] = ()  # ex.: ("Título I", "Capítulo II")
    vigencia: str = ""
    data_coleta: str = ""  # AAAA-MM-DD
    url: str = ""


@dataclass(frozen=True)
class Citacao:
    """Citação no nível do dispositivo: norma, artigo, parágrafo e inciso."""

    trecho_id: str
    norma: str
    artigo: str
    paragrafo: str | None = None  # ex.: "§ 1º" ou "parágrafo único"
    inciso: str | None = None  # ex.: "inciso IV"
    texto: str = ""  # texto literal do dispositivo
    url: str = ""
    data_coleta: str = ""

    def formatar(self) -> str:
        """Formato legal, ex.: 'CDC, art. 18, § 1º, inciso II'."""
        partes = [f"{self.norma}, art. {self.artigo}"]
        if self.paragrafo:
            partes.append(self.paragrafo)
        if self.inciso:
            partes.append(self.inciso)
        return ", ".join(partes)


@dataclass(frozen=True)
class Resposta:
    """Resultado de `responder()`."""

    status: Status
    texto: str
    citacoes: tuple[Citacao, ...] = field(default_factory=tuple)
    caso_pessoal: bool = False
