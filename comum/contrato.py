"""Contrato do núcleo de RAG (implementado por Lucas em `rag/`).

Esta é só a assinatura. A lógica não pertence ao M0.

`rag/` expõe `buscar` e `responder` como funções soltas, como no PRD. O módulo
em si cumpre o Protocol, por isso não é preciso criar uma classe.
"""

from typing import Protocol

from comum.tipos import Resposta, Trecho


class Nucleo(Protocol):
    def buscar(self, pergunta: str, k: int = 5) -> list[Trecho]:
        """No máximo k trechos, em ordem decrescente de pontuação."""
        ...

    def responder(self, pergunta: str) -> Resposta:
        """Busca, gera, valida citações e aplica recusa e caso pessoal."""
        ...
