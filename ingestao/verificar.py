"""Verificador de atualização (RF5), sem acesso à rede.

Compara um HTML salvo manualmente com a versão registrada em `normas.yaml` e
relata as diferenças por dispositivo.

Uso: python -m ingestao.verificar SIGLA CAMINHO_DO_NOVO_HTML
Saída: 0 sem diferenças, 1 com diferenças, 2 erro de uso ou arquivo inválido.
"""

import argparse
import sys
from dataclasses import dataclass, field
from pathlib import Path

from ingestao import coletar
from ingestao.coletar import Norma
from ingestao.parser import Resultado


@dataclass
class Diferencas:
    adicionados: list[str] = field(default_factory=list)
    removidos: list[str] = field(default_factory=list)
    alterados: list[str] = field(default_factory=list)
    novas_remocoes: list[str] = field(default_factory=list)

    @property
    def vazio(self) -> bool:
        return not (
            self.adicionados or self.removidos or self.alterados or self.novas_remocoes
        )

    def artigos_afetados(self) -> list[str]:
        ids = self.adicionados + self.removidos + self.alterados
        return sorted({i.split(".")[1] for i in ids if "." in i})


def _indexar(res: Resultado) -> dict[str, tuple[str, tuple[str, ...]]]:
    return {d.id: (d.texto, d.notas) for a in res.artigos for d in a.dispositivos}


def comparar(antigo: Resultado, novo: Resultado) -> Diferencas:
    a, n = _indexar(antigo), _indexar(novo)
    dif = Diferencas()
    dif.adicionados = sorted(set(n) - set(a))
    dif.removidos = sorted(set(a) - set(n))
    dif.alterados = sorted(i for i in set(a) & set(n) if a[i] != n[i])
    antes = {(r.id, r.rotulo, r.artigo, r.motivo, r.marca) for r in antigo.removidos}
    for r in novo.removidos:
        if (r.id, r.rotulo, r.artigo, r.motivo, r.marca) not in antes:
            dif.novas_remocoes.append(
                f"{r.id or r.rotulo} ({r.motivo}, art. {r.artigo})"
            )
    dif.novas_remocoes.sort()
    return dif


def formatar(norma: Norma, dif: Diferencas) -> str:
    if dif.vazio:
        return f"{norma.sigla}: sem diferenças em relação à versão coletada."
    linhas = [f"{norma.sigla}: diferenças em relação à versão coletada:"]
    secoes = [
        ("Dispositivos alterados", dif.alterados),
        ("Dispositivos novos", dif.adicionados),
        ("Dispositivos que sumiram", dif.removidos),
        ("Novos removidos (revogado, vetado, tachado)", dif.novas_remocoes),
    ]
    for titulo, itens in secoes:
        if itens:
            linhas.append(f"- {titulo} ({len(itens)}):")
            linhas.extend(f"    {i}" for i in itens)
    linhas.append(f"Artigos afetados: {', '.join(dif.artigos_afetados()) or '-'}")
    return "\n".join(linhas)


def localizar_norma(manifesto: coletar.Manifesto, nome: str) -> Norma:
    alvo = nome.strip().lower()
    for norma in manifesto.normas:
        if alvo in (norma.sigla.lower(), norma.id_prefixo.lower()):
            return norma
    validas = ", ".join(n.id_prefixo for n in manifesto.normas)
    raise ValueError(f"norma desconhecida: {nome} (use uma de: {validas})")


def verificar(
    norma: Norma, novo_caminho: Path, raiz: Path = coletar.RAIZ
) -> Diferencas:
    """Compara o arquivo novo com o registrado; levanta ValueError se for outra norma."""
    novo = coletar.parsear_norma(norma, novo_caminho.read_bytes())
    if not coletar.identificacao_igual(novo.identificacao, norma.identificacao):
        raise ValueError(f"o arquivo não é {norma.identificacao}")
    antigo = coletar.parsear_norma(norma, coletar.ler_arquivo(norma, raiz))
    return comparar(antigo, novo)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Compara um HTML salvo com a versão coletada"
    )
    ap.add_argument("norma", help="sigla ou prefixo, ex.: cdc, dec7962, dec13135")
    ap.add_argument("arquivo", type=Path, help="HTML novo, salvo pelo navegador")
    ap.add_argument("--manifesto", type=Path, default=coletar.MANIFESTO)
    args = ap.parse_args(argv)
    try:
        manifesto = coletar.carregar(args.manifesto)
        norma = localizar_norma(manifesto, args.norma)
        dif = verificar(norma, args.arquivo, args.manifesto.parent)
    except (ValueError, OSError) as erro:
        print(f"erro: {erro}", file=sys.stderr)
        return 2
    print(formatar(norma, dif))
    return 0 if dif.vazio else 1


if __name__ == "__main__":
    raise SystemExit(main())
