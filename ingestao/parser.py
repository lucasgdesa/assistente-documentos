"""Parser do HTML do Planalto: hierarquia, artigos e dispositivos.

Remove texto tachado e dispositivos revogados ou vetados e os lista em
`Resultado.removidos`. Não depende de rede nem de relógio.
"""

import re
from dataclasses import dataclass, field

from bs4 import BeautifulSoup, Comment, NavigableString, Tag

NIVEL = {"artigo": 0, "paragrafo": 1, "inciso": 2, "alinea": 3}
HIERARQUIA_NIVEL = {"livro": 0, "título": 1, "capítulo": 2, "seção": 3, "subseção": 4}

_BR = ""  # marcador de quebra de linha (<br>)
_ORDINAIS = {"º", "°", "ª", "o", "a"}
_LETRAS = "A-Za-zÀ-ÿ"
_ORD = r"(?:\.?\s*[º°ª]|\.?\s*o(?=\s|$))?"
_SUFIXO = rf"(?:-\s*(?P<l>[A-Z]{{1,2}})(?![{_LETRAS}]))?"
_FIM = r"\s*[.\-–—:]?\s*(?P<r>.*)$"

ART_RE = re.compile(rf"^Art\.?\s*(?P<n>\d+)\s*{_ORD}\s*{_SUFIXO}{_FIM}", re.DOTALL)
PAR_RE = re.compile(rf"^§\s*(?P<n>\d+)\s*{_ORD}\s*{_SUFIXO}{_FIM}", re.DOTALL)
PUN_RE = re.compile(r"^Par[aá]grafo\s+[úu]nico\s*[.\-–—:]?\s*(?P<r>.*)$", re.DOTALL)
INC_RE = re.compile(
    r"^(?P<n>[IVXLCDM]+)\s*(?:-\s*(?P<l>[A-Z])(?=\s*[-–—]))?\s*[-–—]\s*(?P<r>.*)$",
    re.DOTALL,
)
INC_PARTIDO_RE = re.compile(r"^([IVXLC])\s+([IVXLC]+)(\s*[-–—])")
ALI_RE = re.compile(r"^(?P<n>[a-z])\)\s*(?P<r>.*)$", re.DOTALL)
CABECALHO_RE = re.compile(
    r"^(?P<t>LIVRO|TÍTULO|CAPÍTULO|SEÇÃO|SUBSEÇÃO)\s+"
    r"(?P<n>[IVXLCDM]+(?:-[A-Z])?|ÚNICO)\b\s*(?P<r>.*)$",
    re.DOTALL,
)
_MARCAS_REMOCAO = (
    r"Revogad[oa]|Vetad[oa]|Suprimid[oa]|Sem efeito|Declarad[oa] inconstitucional"
)
NOTA_RE = re.compile(
    r"\(\s*(?:Redação dada|Incluíd[oa]|Renumerad[oa]|Vide|Regulamento|Vigência|"
    r"Produção de efeito|Expressão|Declarad[oa]|Suprimid[oa]|Sem efeito|"
    r"Revogad[oa]|Vetad[oa])[^)]*\)",
    re.IGNORECASE,
)
NOTA_ALTERACAO_RE = re.compile(
    r"^\(\s*(?:Redação dada|Incluíd[oa]|Renumerad[oa])", re.IGNORECASE
)
NOTA_REMOCAO_RE = re.compile(rf"^\(\s*(?:{_MARCAS_REMOCAO})", re.IGNORECASE)
NOTA_FUTURA_RE = re.compile(
    r"^\(\s*(?:Vigência a partir|Vigência diferida|Produção de efeitos?)", re.IGNORECASE
)
NOTA_SUSPEITA_RE = re.compile(
    r"revogad|suprimid|sem efeito|inconstitucion|suspens", re.IGNORECASE
)
LINK_SOLTO_RE = re.compile(r"(?:\s+(?:Vigência|Regulamento|Mensagem de veto))+\s*$")
NOTA_EDITORIAL_RE = re.compile(
    r"^Dispositivo (?:incluído|transformado)\b", re.IGNORECASE
)
# corpo que é só a marca de remoção (com a origem, quando houver), não uma frase
SO_REMOVIDO_RE = re.compile(
    r"^(?:(?:Revogad[oa]|Vetad[oa]|Suprimid[oa])"
    r"(?:\s+(?:pel[oa]s?|por)\s+(?:Lei|Decreto|Medida|Emenda|Resolução|ADI)\b[^.;]{0,120})?"
    r"|Sem efeito"
    r"|Declarad[oa] inconstitucional\s+pel[oa]\s+[^.;]{0,150})\s*[.;]?$",
    re.IGNORECASE,
)
ABRE_ASPAS = ("“", '"')
FECHA_ASPAS_RE = re.compile(r"[”\"]\s*(?:\(NR\))?\s*\.?\s*$")
PONTUACAO_RE = re.compile(r"\s+([,;:.)])")
ABRE_PAREN_RE = re.compile(r"\(\s+")
_ROMANOS = [(1000, "M"), (900, "CM"), (500, "D"), (400, "CD"), (100, "C"), (90, "XC")]
_ROMANOS += [(50, "L"), (40, "XL"), (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")]


class ErroParser(ValueError):
    """Estrutura do HTML que o parser não consegue tratar com segurança."""


@dataclass(frozen=True)
class Dispositivo:
    id: str
    tipo: str  # artigo, paragrafo, inciso, alinea
    rotulo: str  # ex.: "Art. 18", "§ 1º", "Parágrafo único", "IV", "a"
    texto: str  # com o rótulo canônico, sem notas de redação
    grupo: str  # id do parágrafo ao qual pertence, ou o id do artigo (caput)
    notas: tuple[str, ...] = ()  # notas de alteração (Redação dada, Incluído)
    avisos: tuple[str, ...] = ()  # outras notas: Vide, Vigência, Produção de efeito


@dataclass(frozen=True)
class Artigo:
    id: str
    numero: str  # ex.: "54-A"
    hierarquia: tuple[str, ...]
    dispositivos: tuple[Dispositivo, ...]  # o primeiro é o caput


@dataclass(frozen=True)
class Removido:
    id: str  # vazio se o identificador não pôde ser derivado
    rotulo: str
    motivo: str  # tachado, revogado, vetado, nota_editorial, subordinado
    artigo: str
    marca: str  # nota ou texto tachado que motivou a remoção


@dataclass
class Resultado:
    artigos: list[Artigo] = field(default_factory=list)
    alteradores: list[Artigo] = field(default_factory=list)
    removidos: list[Removido] = field(default_factory=list)
    anomalias: list[str] = field(default_factory=list)
    ajustes: list[str] = field(default_factory=list)
    identificacao: str = ""
    ementa: str = ""
    local_data: str = ""
    rodape: str = ""
    artigos_detectados: list[str] = field(default_factory=list)


def detectar_charset(dados: bytes) -> str:
    """Charset declarado no HTML, em minúsculas (vazio se não houver)."""
    cabeca = dados[:4096].decode("ascii", errors="ignore")
    achado = re.search(r"charset\s*=\s*([\w-]+)", cabeca, re.IGNORECASE)
    return achado.group(1).lower() if achado else ""


def decodificar(dados: bytes) -> str:
    """Decodifica usando o charset declarado (padrão windows-1252)."""
    return dados.decode(detectar_charset(dados) or "windows-1252")


def _para_romano(n: int) -> str:
    saida = ""
    for valor, simbolo in _ROMANOS:
        while n >= valor:
            saida += simbolo
            n -= valor
    return saida


def _romano_para_int(romano: str) -> int | None:
    valores = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
    total = 0
    for i, letra in enumerate(romano):
        v = valores[letra]
        seguinte = valores[romano[i + 1]] if i + 1 < len(romano) else 0
        total += -v if v < seguinte else v
    return total if total > 0 and _para_romano(total) == romano else None


def _classes_tachadas(sopa: BeautifulSoup) -> set[str]:
    css = " ".join(s.get_text() for s in sopa.find_all("style"))
    return set(re.findall(r"\.([\w-]+)\s*\{[^}]*line-through", css))


def _tachado(tag: Tag, classes: set[str]) -> bool:
    if tag.name in ("s", "strike", "del"):
        return True
    if "line-through" in str(tag.get("style", "")).lower():
        return True
    return bool(classes & set(tag.get("class") or []))


def _segmentos(no: Tag, tachado: bool, classes: set[str]) -> list[tuple[str, bool]]:
    saida: list[tuple[str, bool]] = []
    for filho in no.children:
        if isinstance(filho, Comment):
            continue
        if isinstance(filho, NavigableString):
            saida.append((str(filho), tachado))
        elif isinstance(filho, Tag):
            if filho.name in ("script", "style"):
                continue
            if filho.name == "br":
                saida.append((_BR, tachado))
                continue
            saida.extend(
                _segmentos(filho, tachado or _tachado(filho, classes), classes)
            )
    return saida


def _normalizar(texto: str) -> str:
    texto = re.sub(r"\s+", " ", texto.replace(_BR, " ")).strip()
    return PONTUACAO_RE.sub(r"\1", ABRE_PAREN_RE.sub("(", texto))


def _separar_notas(texto: str) -> tuple[str, list[str]]:
    """Tira as notas do Planalto do texto. O link solto "Vigência" vira nota."""
    notas = [re.sub(r"\s+", " ", n).strip() for n in NOTA_RE.findall(texto)]
    limpo = re.sub(r"\s+", " ", NOTA_RE.sub(" ", texto)).strip()
    solto = LINK_SOLTO_RE.search(limpo)
    if solto and "Vigência" in solto.group() and "(Vigência)" not in notas:
        notas.append("(Vigência)")
    limpo = LINK_SOLTO_RE.sub("", limpo)
    limpo = re.sub(r"\s+([,;:.])", r"\1", limpo)
    limpo = re.sub(r"([;:,])\s*\.$", r"\1", limpo)
    return limpo.strip(), notas


def _motivo(remocao: str) -> str:
    texto = remocao.lower()
    if NOTA_EDITORIAL_RE.match(remocao):
        return "nota_editorial"
    for chave, motivo in (
        ("vetad", "vetado"),
        ("suprimid", "suprimido"),
        ("sem efeito", "sem_efeito"),
        ("inconstitucional", "inconstitucional"),
    ):
        if chave in texto:
            return motivo
    return "revogado"


@dataclass
class _Classe:
    tipo: str  # artigo, paragrafo, unico, inciso, alinea, cabecalho, texto
    chave: str = ""  # identificador relativo (n, n-l)
    rotulo: str = ""  # forma de exibição
    prefixo: str = ""  # rótulo como aparece no início do texto
    resto: str = ""
    ajustes: tuple[str, ...] = ()


def _numerado(n: int, letra: str | None) -> tuple[str, str, str]:
    """Devolve (chave, rotulo, forma no texto) de um número com letra opcional."""
    base = f"{n}º" if n <= 9 else f"{n}"
    rotulo = base + (f"-{letra}" if letra else "")
    ponto = "" if (n <= 9 and not letra) else "."
    chave = f"{n}" + (f"-{letra}" if letra else "")
    return chave, rotulo, rotulo + ponto


def _classificar(texto: str) -> _Classe:
    if (m := CABECALHO_RE.match(texto)) is not None:
        return _Classe("cabecalho", m["n"], m["t"].lower(), "", m["r"])
    if (m := ART_RE.match(texto)) is not None:
        chave, rotulo, forma = _numerado(int(m["n"]), m["l"])
        return _Classe(
            "artigo", chave, f"Art. {rotulo}", f"Art. {forma}", m["r"].strip()
        )
    if (m := PAR_RE.match(texto)) is not None:
        chave, rotulo, forma = _numerado(int(m["n"]), m["l"])
        return _Classe("paragrafo", chave, f"§ {rotulo}", f"§ {forma}", m["r"].strip())
    if (m := PUN_RE.match(texto)) is not None:
        return _Classe(
            "unico", "unico", "Parágrafo único", "Parágrafo único.", m["r"].strip()
        )
    ajustes: tuple[str, ...] = ()
    partido = INC_PARTIDO_RE.match(texto)
    if partido and _romano_para_int(partido[1] + partido[2]):
        junto = partido[1] + partido[2]
        ajustes = (f"numeral partido pela serialização: '{partido[1]} {partido[2]}'",)
        texto = junto + texto[partido.end(2) :]
    m = INC_RE.match(texto)
    if m is not None and (valor := _romano_para_int(m["n"])):
        sufixo = f"-{m['l']}" if m["l"] else ""
        return _Classe(
            "inciso",
            f"{valor}{sufixo.lower()}",
            f"{m['n']}{sufixo}",
            f"{m['n']}{sufixo} -",
            m["r"].strip(),
            ajustes,
        )
    if (m := ALI_RE.match(texto)) is not None:
        return _Classe("alinea", m["n"], m["n"], f"{m['n']})", m["r"].strip())
    return _Classe("texto", resto=texto)


def _dividir_notas(notas: list[str]) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Separa notas de alteração das demais notas que ficam como aviso."""
    alteracoes = tuple(n for n in notas if NOTA_ALTERACAO_RE.match(n))
    avisos = tuple(
        n
        for n in notas
        if not NOTA_ALTERACAO_RE.match(n)
        and not NOTA_REMOCAO_RE.match(n)
        and not re.match(r"^\(\s*Regulamento", n, re.IGNORECASE)
    )
    return alteracoes, avisos


class _Construtor:
    def __init__(self, prefixo: str, alteradores: frozenset[str] = frozenset()) -> None:
        self.prefixo = prefixo
        self.alteradores = alteradores
        self.alterador = False
        self.ultimo_num: int | None = None
        self.ultimo_chave = ""
        self.ultimo_par = 0
        self.alertados: set[str] = set()
        self.resultado = Resultado()
        self.hierarquia: dict[int, str] = {}
        self.artigo_id = ""
        self.artigo_numero = ""
        self.disps: list[Dispositivo] = []
        self.ultimo: int | None = None  # índice do último dispositivo mantido
        self.par_id = ""
        self.inc_id = ""
        self.bloqueio: int | None = None
        self.ids: set[str] = set()
        self.cabecalho_aberto: tuple[int, str] | None = None

    def fechar_artigo(self) -> None:
        if self.artigo_id and self.disps:
            hier = tuple(self.hierarquia[k] for k in sorted(self.hierarquia))
            artigo = Artigo(self.artigo_id, self.artigo_numero, hier, tuple(self.disps))
            if self.alterador:
                self.resultado.alteradores.append(artigo)
            else:
                self.resultado.artigos.append(artigo)
        self.alterador = False
        self.ultimo_par = 0
        self.artigo_id = self.artigo_numero = ""
        self.disps, self.ultimo, self.par_id, self.inc_id = [], None, "", ""
        self.bloqueio = None

    def definir_cabecalho(self, classe: _Classe) -> None:
        nivel = HIERARQUIA_NIVEL[classe.rotulo]
        numero = "único" if classe.chave == "ÚNICO" else classe.chave
        nome, notas = _separar_notas(classe.resto)
        base = f"{classe.rotulo.capitalize()} {numero}"
        self.registrar_notas_cabecalho(base, notas)
        self.fechar_artigo()
        for k in [k for k in self.hierarquia if k >= nivel]:
            del self.hierarquia[k]
        self.hierarquia[nivel] = f"{base} - {nome}" if nome else base
        self.cabecalho_aberto = None if nome else (nivel, base)

    def completar_nome(self, texto: str) -> None:
        if self.cabecalho_aberto is None:
            return
        nivel, base = self.cabecalho_aberto
        nome, notas = _separar_notas(texto)
        self.registrar_notas_cabecalho(base, notas)
        if nome:
            self.hierarquia[nivel] = f"{base} - {nome}"
            self.cabecalho_aberto = None

    def registrar_notas_cabecalho(self, base: str, notas: list[str]) -> None:
        for nota in notas:
            self.resultado.ajustes.append(f"nota de cabeçalho ({base}): {nota}")

    def _novo_id(self, tipo: str, classe: _Classe) -> str:
        if tipo == "artigo":
            return f"{self.prefixo}.art{classe.chave.lower()}"
        if tipo == "paragrafo":
            suf = "parunico" if classe.tipo == "unico" else f"par{classe.chave.lower()}"
            return f"{self.artigo_id}.{suf}"
        if tipo == "alinea":
            return f"{self.inc_id or self.par_id or self.artigo_id}.ali{classe.chave}"
        return f"{self.par_id or self.artigo_id}.inc{classe.chave}"

    def _remover(self, classe: _Classe, motivo: str, marca: str, disp_id: str) -> None:
        self.resultado.removidos.append(
            Removido(disp_id, classe.rotulo, motivo, self.artigo_numero, marca)
        )

    def adicionar(self, classe: _Classe) -> None:
        tipo = "paragrafo" if classe.tipo == "unico" else classe.tipo
        nivel = NIVEL[tipo]
        if self.bloqueio is not None and nivel > self.bloqueio:
            self._remover(classe, "subordinado", "dispositivo superior removido", "")
            return
        self.bloqueio = None
        self.resultado.ajustes.extend(classe.ajustes)
        if tipo == "artigo":
            self.fechar_artigo()
            self.artigo_numero = classe.chave
            self.resultado.artigos_detectados.append(classe.chave)
            self.artigo_id = f"{self.prefixo}.art{classe.chave.lower()}"
            self.alterador = self.artigo_id in self.alteradores
            self._checar_sequencia_artigo(classe.chave)
        elif not self.artigo_id:
            self.resultado.anomalias.append(f"dispositivo sem artigo: {classe.rotulo}")
            return
        if classe.tipo == "paragrafo" and "-" not in classe.chave:
            self._checar_sequencia_paragrafo(int(classe.chave))
        disp_id = self._novo_id(tipo, classe)
        if disp_id in self.ids:
            raise ErroParser(f"identificador duplicado: {disp_id}")
        self.ids.add(disp_id)
        if tipo == "paragrafo":
            self.par_id, self.inc_id = disp_id, ""
        elif tipo == "inciso":
            self.inc_id = disp_id
        corpo, notas = _separar_notas(classe.resto)
        remocao = next((n for n in notas if NOTA_REMOCAO_RE.match(n)), "")
        if not remocao and SO_REMOVIDO_RE.match(corpo):
            remocao = corpo
        if not remocao and NOTA_EDITORIAL_RE.match(corpo):
            remocao = corpo  # anotação do Planalto no lugar do texto
        if remocao:
            self._remover(classe, _motivo(remocao), remocao, disp_id)
            self.bloqueio = nivel
            if tipo == "artigo":
                self.artigo_id, self.disps, self.ultimo = "", [], None
                self.alterador = False
            return
        for n in notas:
            if NOTA_FUTURA_RE.match(n):
                msg = f"{disp_id}: nota de vigência futura ou condicionada: {n}"
                self.resultado.anomalias.append(msg)
            if NOTA_SUSPEITA_RE.search(n) and not NOTA_ALTERACAO_RE.match(n):
                msg = f"{disp_id}: nota de remoção parcial, dispositivo mantido: {n}"
                self.resultado.anomalias.append(msg)
        alteracoes, avisos = _dividir_notas(notas)
        texto = f"{classe.prefixo} {corpo}".strip()
        grupo = self.par_id if (tipo != "artigo" and self.par_id) else self.artigo_id
        self.disps.append(
            Dispositivo(disp_id, tipo, classe.rotulo, texto, grupo, alteracoes, avisos)
        )
        self.ultimo = len(self.disps) - 1

    def continuar(self, texto: str) -> None:
        if self.bloqueio is not None:
            return
        corpo, notas = _separar_notas(texto)
        if self.ultimo is None:
            for n in notas:
                self.resultado.ajustes.append(f"nota sem dispositivo: {n}")
            return
        atual = self.disps[self.ultimo]
        alteracoes, avisos = _dividir_notas(notas)
        for n in notas:
            if NOTA_REMOCAO_RE.match(n) or NOTA_FUTURA_RE.match(n):
                msg = f"{atual.id}: nota de remoção ou vigência em continuação: {n}"
                self.resultado.anomalias.append(msg)
        novo = f"{atual.texto}\n{corpo}" if corpo else atual.texto
        self.disps[self.ultimo] = Dispositivo(
            atual.id,
            atual.tipo,
            atual.rotulo,
            novo,
            atual.grupo,
            atual.notas + alteracoes,
            atual.avisos + avisos,
        )

    def alertar(self, chave: str, mensagem: str) -> None:
        if chave not in self.alertados:
            self.alertados.add(chave)
            self.resultado.anomalias.append(f"alerta RF27: {mensagem}")

    def _checar_sequencia_artigo(self, chave: str) -> None:
        num = int(chave.partition("-")[0])
        anterior = self.ultimo_num
        if anterior is not None and num not in (anterior, anterior + 1):
            self.alertar(
                f"seq-art-{chave}",
                f"numeração de artigo fora de sequência: art. {chave} "
                f"após art. {self.ultimo_chave}",
            )
        self.ultimo_num, self.ultimo_chave = num, chave

    def _checar_sequencia_paragrafo(self, numero: int) -> None:
        if numero != self.ultimo_par + 1:
            self.alertar(
                f"seq-par-{self.artigo_id}-{numero}",
                f"numeração de parágrafo fora de sequência em {self.artigo_id}: "
                f"§ {numero} após § {self.ultimo_par}",
            )
        self.ultimo_par = numero

    def linha_citada(self, texto: str) -> None:
        """Alerta se uma linha citada (entre aspas ou em citação) traz marcador."""
        if self.alterador or not self.artigo_id:
            return
        interno = _classificar(texto.lstrip('"“ '))
        if interno.tipo in ("artigo", "paragrafo", "unico"):
            self.alertar(
                f"citada-{self.artigo_id}",
                f"{self.artigo_id} traz linha citada de outra norma com marcador "
                f"de {interno.rotulo}, fora de artigos_alteradores",
            )

    def tachado(self, struck: str, artigo_vivo: str = "") -> None:
        texto = _normalizar(struck)
        classe = _classificar(texto)
        disp_id = ""
        if classe.tipo == "artigo":
            disp_id = f"{self.prefixo}.art{classe.chave.lower()}"
        rotulo = classe.rotulo if classe.tipo != "texto" else "(sem rótulo)"
        self.resultado.removidos.append(
            Removido(
                disp_id, rotulo, "tachado", artigo_vivo or self.artigo_numero, texto
            )
        )


def _fora_de_paragrafo(sopa: BeautifulSoup) -> list[str]:
    achados = []
    for tx in sopa.body.find_all(string=True):
        pai = tx.parent.name if tx.parent else ""
        if isinstance(tx, Comment) or pai in ("script", "style", "title"):
            continue
        if tx.find_parent(["p", "h1", "h2", "h3"]) is not None or not tx.strip():
            continue
        if tx.strip() in {"Vigência", "Regulamento", "Mensagem de veto"}:
            continue
        achados.append(re.sub(r"\s+", " ", tx.strip())[:60])
    return achados


def parsear(
    html: str,
    prefixo: str,
    correcoes: tuple[tuple[str, str], ...] = (),
    alteradores: tuple[str, ...] = (),
) -> Resultado:
    """Extrai artigos e dispositivos do HTML (texto já decodificado).

    `correcoes` são pares (de, para) de espaçamento quebrado pela serialização
    do HTML (palavra partida em duas). Cada uso entra em `ajustes`; par que não
    é encontrado entra em `anomalias`. `alteradores` são os ids dos artigos que
    alteram outra norma e trazem o texto dela (RF27): ficam em `alteradores`, sem
    identificadores de dispositivo.
    """
    sopa = BeautifulSoup(html, "lxml")
    classes = _classes_tachadas(sopa)
    c = _Construtor(prefixo, frozenset(alteradores))
    res = c.resultado
    res.anomalias.extend(
        f"texto fora de parágrafo: {x}" for x in _fora_de_paragrafo(sopa)
    )
    em_citacao = False
    usadas: set[str] = set()
    anterior = ""
    for p in sopa.body.find_all("p"):
        vivos, tachados = [], []
        for texto_seg, marcado in _segmentos(p, _tachado(p, classes), classes):
            if marcado and texto_seg.strip() in _ORDINAIS:
                marcado = False  # ordinal formatado como tachado, não é revogação
                res.ajustes.append("ordinal marcado como tachado mantido")
            (tachados if marcado else vivos).append(texto_seg)
        texto = _normalizar("".join(vivos))
        for de, para in correcoes:
            if de in texto:
                texto = texto.replace(de, para)
                usadas.add(de)
                res.ajustes.append(f"espaçamento corrigido: '{de}' -> '{para}'")
        struck = "".join(tachados)
        if struck.strip() and res.artigos_detectados:
            vivo = _classificar(texto) if texto else None
            c.tachado(struck, vivo.chave if vivo and vivo.tipo == "artigo" else "")
        if not texto:
            continue
        if texto.startswith("Brasília,"):
            res.local_data = texto
            break
        classe = _classificar(texto)
        if not res.artigos_detectados and classe.tipo not in ("cabecalho", "artigo"):
            if re.match(r"^(LEI|DECRETO)\s+N", texto) and not res.identificacao:
                res.identificacao = texto
            if re.match(r"^(O PRESIDENTE|A PRESIDENTA)", texto):
                res.ementa = anterior
            anterior = texto
            continue
        em_bloco = p.find_parent("blockquote") is not None
        if em_citacao or em_bloco or texto.startswith(ABRE_ASPAS):
            if texto.startswith(ABRE_ASPAS) and not em_citacao:
                em_citacao = FECHA_ASPAS_RE.search(texto[1:]) is None
            elif em_citacao and FECHA_ASPAS_RE.search(texto):
                em_citacao = False
            c.linha_citada(texto)
            c.continuar(texto)
        elif c.alterador and classe.tipo not in ("artigo", "cabecalho"):
            c.continuar(texto)
        elif classe.tipo == "cabecalho":
            c.definir_cabecalho(classe)
        elif classe.tipo == "texto" and c.cabecalho_aberto is not None:
            c.completar_nome(texto)
        elif classe.tipo == "texto":
            c.continuar(texto)
        else:
            c.adicionar(classe)
    c.fechar_artigo()
    achados = {a.id for a in res.alteradores}
    res.anomalias.extend(
        f"alerta RF27: artigo alterador listado e não encontrado: {a}"
        for a in alteradores
        if a not in achados
    )
    res.anomalias.extend(
        f"correção de espaçamento sem efeito: '{de}'"
        for de, _ in correcoes
        if de not in usadas
    )
    for p in sopa.body.find_all("p"):
        bruto = _normalizar(p.get_text())
        if bruto.startswith("Este texto não substitui"):
            res.rodape = bruto
    return res
