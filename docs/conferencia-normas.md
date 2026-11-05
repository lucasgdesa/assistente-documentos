# Conferência das normas (M1, seção 14.4 do PRD)

Conferência feita em 2026-11-05 sobre os HTMLs salvos manualmente pelo navegador, em `dados/brutos/`. Cada item cita a evidência na própria página. Este documento traz trechos das normas e não deve ser lido antes de as 60 perguntas estarem commitadas.

## Como os arquivos foram obtidos

- O Planalto recusou toda conexão feita por script nesta rede (`httpx` e `curl`: reset de conexão e timeout, inclusive na raiz do domínio). Por isso a coleta é manual: Lucas salvou as três páginas pelo navegador em 2026-11-05, no modo "página completa".
- Cada arquivo é uma serialização do navegador, não os bytes originais do servidor. Traz o comentário `saved from url=` e uma pasta `*_files` só com imagens e CSS (fora do git, ver `.gitignore`).
- `dec-7962.htm` foi reformatado na serialização (uma tag por linha). Isso quebrou o espaçamento de alguns pontos, tratados como descrito em "Anomalias de texto" abaixo.
- A URL gravada no comentário `saved from url=` do Decreto 13.135 usa `d13135.htm` em minúsculas. É essa a URL registrada em `normas.yaml`.

## 1. Número, ementa e URL

- **CDC.** Página: "LEI Nº 8.078, DE 11 DE SETEMBRO DE 1990." Ementa: "Dispõe sobre a proteção do consumidor e dá outras providências." URL: `https://www.planalto.gov.br/ccivil_03/leis/l8078compilado.htm`. Rodapé: "Este texto não substitui o publicado no DOU de 12.9.1990 e Retificado em 10.1.2007".
- **Decreto 7.962/2013.** Página: "DECRETO Nº 7.962, DE 15 DE MARÇO DE 2013". Ementa: "Regulamenta a Lei nº 8.078, de 11 de setembro de 1990, para dispor sobre a contratação no comércio eletrônico." URL: `https://www.planalto.gov.br/ccivil_03/_ato2011-2014/2013/decreto/d7962.htm`. Rodapé: "Este texto não substitui o publicado no DOU de 15.3.2013 - Edição extra". Art. 9º: entra em vigor sessenta dias após a publicação.
- **Decreto 13.135/2026.** Página: "DECRETO Nº 13.135, DE 9 DE OUTUBRO DE 2026". Ementa: "Regulamenta a Lei nº 8.078, de 11 de setembro de 1990 – Código de Defesa do Consumidor, para estabelecer diretrizes e normas sobre o Serviço de Atendimento ao Consumidor." URL: `https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2026/decreto/d13135.htm`.

Os três números e ementas conferem com a seção 3.1 do PRD.

## 2. Decreto 13.135/2026: publicação, vigência e fornecedores

- **Publicação.** Rodapé da página: "Este texto não substitui o publicado no DOU de 13.10.2026". O decreto é de 9 de outubro de 2026 ("Brasília, 9 de outubro de 2026; 205º da Independência e 138º da República").
- **Vigência.** Art. 25: "Este Decreto entra em vigor vinte dias após a data de sua publicação." A página não traz a data final. Contando 20 dias a partir de 13.10.2026, a vigência começaria em 2026-11-02. Esse cálculo é uma inferência, não consta da página, e a regra de contagem de prazo de vacância deve ser confirmada. Na data de coleta (2026-11-05) o prazo já teria passado.
- **Revogação.** Art. 24: "Fica revogado o Decreto nº 11.034, de 5 de abril de 2022." O CDC compilado traz, na linha de links do cabeçalho, a nota "(Vide Decreto nº 11.034, de 2022)", sem indicar a revogação.
- **A quais fornecedores se aplica.** Art. 1º, parágrafo único: estão sujeitos ao decreto os fornecedores (I) "de produtos e serviços regulados pelo Poder Executivo federal que se enquadrem nos critérios estabelecidos pela agência ou pelo órgão regulador competente" e (II) "que ofertem ou prestem, por meio de plataformas ou outros meios digitais, serviços financeiros, de pagamento, de crédito ou outros serviços de natureza financeira ao consumidor, e que estejam sujeitos à regulação ou à supervisão do Banco Central do Brasil". O art. 2º trata de forma específica de plataformas digitais de intermediação, transporte remunerado privado e entrega. O alcance depende, portanto, de critérios fixados por agências e órgãos reguladores que não estão no texto. Isso é um limite de alcance a declarar em `sobre.html` e no README.
- **Conferência pendente.** A data exata de vigência no DOU, a ser confirmada em fonte oficial pelo Lucas.

## 3. Lei 14.181/2021 na compilação do CDC

Sim, já aparece. O HTML traz 71 ocorrências de "Lei nº 14.181, de 2021", nas notas "(Incluído pela Lei nº 14.181, de 2021)". Isso inclui o Capítulo VI-A ("Da prevenção e do tratamento do superendividamento", arts. 54-A a 54-G) e o Capítulo V do Título III ("Da conciliação no superendividamento", arts. 104-A a 104-C), além de incisos dos arts. 4º, 5º, 6º e 51. Os dispositivos mantidos nos trechos que carregam essa nota são 65, distribuídos em 13 artigos. Alguns dispositivos incluídos por essa lei constam como "(VETADO)" (art. 54-E, por exemplo) e saíram dos trechos.

## 4. Medida provisória de 2026 no art. 57 do CDC

- A página traz duas notas no art. 57: "§ 1º ... (Redação dada pela Medida Provisória nº 1.393, de 2026)" e "§ 2º ... (Incluído pela Medida Provisória nº 1.393, de 2026)". O PRD citava apenas o § 1º. O link das notas aponta para `.../_ato2023-2026/2026/mpv/mpv1393.htm#art4`.
- A página não informa a data da MP nem se ela foi convertida em lei.
- **Risco.** Medida provisória pode perder eficácia se não for convertida em lei no prazo constitucional (a conferir: art. 62, § 3º, da Constituição). O texto de art. 57, § 1º e § 2º, pode deixar de valer sem que o HTML do CDC seja atualizado de imediato. Cada trecho do art. 57 traz essa nota no campo `vigencia`, e `normas.yaml` registra a MP em `ultima_alteracao_observada`. O verificador de atualização (`python -m ingestao.verificar`) deve ser usado antes de cada tag e mensalmente enquanto a demo estiver no ar. A situação da MP 1.393/2026 (vigente, convertida ou perdida) não foi verificada.

## 5. Formato do HTML

- **Charset.** Os três arquivos declaram `charset=windows-1252` na tag `meta`. Nenhum é UTF-8.
- **Texto tachado.** `<strike>`: 0 ocorrências nos três. `<del>`: 0. `line-through` em CSS: 0. `<s>`: 2, ambas no CDC, e as duas envolvem apenas o ordinal de um parágrafo (`§ 1<s>º</s>` e `§ 2<s>º</s>`, ambos no art. 8º): é formatação, não revogação. O parser mantém o ordinal e registra o ajuste ("ordinal marcado como tachado mantido", 2 vezes). Ele também trata `<s>`, `<strike>`, `<del>`, estilo inline `line-through` e classes CSS com `line-through` como texto removido, e lista o que remover, mas nenhuma página real tem isso hoje.
- **Texto revogado.** O CDC não tem nenhuma ocorrência da palavra "revogado" (e os decretos só a usam no art. 24 do Decreto 13.135, que revoga outra norma). A compilação mostra só a redação vigente, com a nota "(Redação dada pela ...)" ou "(Incluído pela ...)" ao lado do dispositivo. Não há blocos com a versão antiga e a nova do mesmo dispositivo em sequência: o parser falha se um mesmo identificador aparecer duas vezes, e isso não ocorreu.
- **Vetados.** O CDC traz 42 dispositivos marcados com o texto "(Vetado)" ou "(VETADO)", sem nenhuma marcação visual além do texto. 12 são artigos inteiros (11, 15, 16, 45, 54-E, 62, 85, 86, 89, 96, 108 e 109). Todos saem dos trechos e constam no relatório.
- **Nota no lugar do texto.** O inciso XI do art. 39 do CDC traz uma anotação do Planalto ("Dispositivo incluído pela MPV nº 1.890-67 ... transformado em inciso XIII, quando da conversão na Lei nº 9.870") no lugar de texto normativo. Foi removido como `nota_editorial` e listado no relatório.
- **Notas de redação.** As notas "(Redação dada ...)", "(Incluído ...)", "(Vide ...)", "(Vigência)" e "(Regulamento)" são links dentro do parágrafo. O parser tira essas notas do texto do trecho. As de alteração ficam no campo `vigencia`.
- **Âncoras por artigo.** O CDC não tem âncoras por artigo no arquivo salvo (as ocorrências de `#artN` são links, não âncoras). O Decreto 7.962 tem `<a name="art1">` a `art9`. O Decreto 13.135 tem `<a name="art1">` a `art25`. O parser não depende de âncoras; usa o rótulo "Art." do texto.
- **Variações de rótulo no CDC.** Ordinais aparecem como "º", "°", "§ 1 º", "§ 3 o", "§ 4.°" e artigos acima de 9 como "Art. 10.". Os rótulos são normalizados (`§ 3º`) no texto do trecho; o resto do texto não é alterado.
- **Artigos de emenda.** Os arts. 110 a 117 do CDC e o art. 8º do Decreto 7.962 citam dispositivos de outras normas, em geral entre aspas. Pelo RF27 eles estão listados em `artigos_alteradores` no `normas.yaml`, ficam fora de `dados/trechos.jsonl` e vão para `dados/trechos_alteradores.jsonl`, com o texto literal. No art. 113 do CDC as aspas aparecem só na abertura do primeiro parágrafo citado e no fim do último: faltam no próprio HTML (conferido no arquivo bruto), não foram perdidas pelo parser, e nenhuma aspa é acrescentada.

## Anomalias de texto

- **Decreto 7.962 (serialização).** Quatro pontos: o inciso II do art. 4º aparece como "I I -" (corrigido para "II -" pelo parser, que registra o ajuste); duas palavras partidas ("ante riores" e "d as demandas", corrigidas por pares explícitos em `correcoes_espaco` no `normas.yaml`); e, no inciso VI do mesmo artigo, a remissão "referidas no inciso , pelo mesmo meio" está sem o numeral. O numeral ausente **não** foi preenchido, para não escrever texto de lei. Deve ser conferido contra a página oficial na conferência CA3.
- **Pontuação solta.** Espaços antes de vírgula, ponto e fecha-parênteses, vindos da serialização (por exemplo "art. 2º ,"), são removidos do texto.
- **CDC, penas.** Algumas linhas "Pena" aparecem sem o hífen no HTML ("Pena Detenção ..."). Mantido como está na página.
- **Preâmbulo.** Um parágrafo vazio no início do Decreto 13.135 e parágrafos vazios no fim dos Decretos são ignorados.

## Limites do que foi verificado

- O texto dos trechos foi comparado com os próprios HTMLs salvos, não com o site no ar. A conferência de 15 dispositivos contra a página oficial (CA3) é do Lucas.
- A situação atual da MP 1.393/2026 e a data exata da vigência do Decreto 13.135/2026 no DOU não foram confirmadas fora da página.
- O Decreto 11.034/2022 só foi confirmado como revogado pelo art. 24 do Decreto 13.135 (a página dele não foi aberta).

## Revisão do M1: notas e marcas

- **Marcas de remoção.** Além de "(Revogado)" e "(Vetado)", o parser trata "(Suprimido)", "(Sem efeito)", "Sem efeito." e "(Declarado inconstitucional ...)" como remoção, e lista o dispositivo no relatório. Marca explícita é exigida: uma frase normal que apenas começa com "Revogado ..." continua no texto. Nota parcial (por exemplo "(Expressão declarada inconstitucional ...)") mantém o dispositivo e gera anomalia no relatório. Nenhuma dessas marcas existe nas três páginas reais; só a fixture fictícia as exercita.
- **Notas de vigência.** As notas "Vide", "Vigência a partir de", "Produção de efeito" e o link "Vigência" não são mais descartadas: vão para o campo `vigencia` do trecho ("Notas do Planalto: ..."). Nota de vigência futura gera anomalia e troca o início do campo por "Vigência futura ou condicionada", para o trecho não aparecer como "Em vigor". Notas "Regulamento" continuam descartadas (são links para regulamentação, não para vigência). Notas de cabeçalho e notas soltas sem dispositivo ficam em "Ajustes de texto" do relatório.
- **Casos reais.** Nas páginas reais só aparece o link "Vigência", em 3 trechos do CDC (art. 6º, duas partes, e art. 43). Os links apontam para o artigo de vigência da lei alteradora (Lei 12.741/2012, art. 6º; Lei 13.146/2015, art. 127), ambas anteriores à coleta. Não há nota de vigência futura nem de produção de efeito diferida. Por isso os trechos mantêm "Em vigor" e só ganham a nota registrada. O conteúdo desses artigos de vigência não foi lido.
- **Alertas RF27.** Nas três normas reais, nenhum artigo fora de `artigos_alteradores` tem linha citada com marcador interno nem numeração de artigo ou de parágrafo fora de sequência (inclusive no Decreto 13.135).

## Melhorias registradas (fora desta rodada)

- **L2.** Notas por dispositivo: hoje o trecho só junta as notas de todos os seus dispositivos no campo `vigencia`. Não dá para saber a qual dispositivo cada nota pertence.
- **L3.** Hierarquia no verificador: o verificador compara dispositivos, não títulos, capítulos e seções. Mudança só de hierarquia não é relatada.
