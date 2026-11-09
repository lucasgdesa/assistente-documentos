# Assistente de Documentos

Assistente que responde perguntas sobre leis brasileiras do consumidor (CDC,
Decreto 7.962/2013 e Decreto 13.135/2026), sempre citando norma, artigo,
parágrafo e inciso. Projeto individual de estudo, com foco em avaliação
reproduzível. O PRD está em `docs/prd/assistente-documentos.md`.

Informação geral sobre a lei. Não é orientação jurídica e não substitui
advogado ou Procon.

## Estado atual: M1 (normas)

Existem os tipos compartilhados (`comum/tipos.py`), o contrato do núcleo
(`comum/contrato.py`), a ingestão das três normas (`ingestao/`), testes e CI.
Ainda não há busca nem resposta (`rag/` e `avaliacao/` são do Lucas). As 60
perguntas de avaliação estão em `avaliacao/perguntas_v1.jsonl`, ainda sem
referências.

A ingestão transforma os HTMLs oficiais em trechos por artigo, sem texto
tachado, revogado ou vetado:

- `normas.yaml`: manifesto com título, sigla, URL oficial, data de coleta,
  SHA-256 e última alteração observada de cada norma.
- `dados/brutos/`: cópia bruta dos HTMLs. O Planalto recusa conexões por script
  nesta rede, então os arquivos foram salvos manualmente pelo navegador (página
  completa) em 2026-11-05. A serialização do navegador não é byte a byte a do
  servidor.
- `dados/trechos.jsonl`: trechos gerados (um artigo por trecho; artigo acima de
  1.500 caracteres é dividido entre parágrafos ou incisos, repetindo o caput).
- `dados/trechos_alteradores.jsonl`: artigos que alteram outra norma e trazem
  texto dela (lista `artigos_alteradores` em `normas.yaml`). Ficam fora de
  `trechos.jsonl` e não geram identificadores de dispositivo.
- `dados/relatorio-ingestao.md`: relatório gerado, com artigos processados,
  dispositivos removidos e páginas de origem. É a fonte das métricas do M1.
- `docs/conferencia-normas.md`: o que foi conferido nas páginas (número, ementa,
  vigência, formato do HTML).

## Comandos de ingestão

```powershell
python -m ingestao.coletar validar     # confere os arquivos salvos com normas.yaml
python -m ingestao.coletar registrar   # após salvar novos HTMLs: atualiza SHA-256
python -m ingestao                     # gera dados/trechos.jsonl e o relatório
python -m ingestao.verificar cdc caminho/do/novo-cdc.htm
```

O verificador compara um HTML novo, salvo manualmente, com a versão coletada e
lista os dispositivos alterados, novos e removidos. Não acessa a rede. Sai com
0 se não houver diferença, 1 se houver e 2 em caso de erro. As siglas aceitas
são `cdc`, `dec7962` e `dec13135`.

A ingestão é determinística: a data de coleta vem do manifesto, nunca do relógio,
e duas execuções sobre o mesmo HTML geram arquivos idênticos.

## Instalação (Windows, PowerShell)

Requer Python 3.12 ou superior; o CI roda em 3.12. O Node.js só é necessário para
o `prettier`.

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env   # preencha a chave só quando for necessária
```

Se o PowerShell bloquear o script de ativação:
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.

## Testes e qualidade

```powershell
pytest
ruff check
ruff format --check
npx prettier --check .
```

Os testes não usam chave de API.

## Autoria

O código de `rag/` e `avaliacao/` é escrito à mão por Lucas. O restante é feito
com agentes de IA e revisado. Commits feitos pelo agente dev levam o trailer
`Autor-agente: dev`; nenhum commit que altere `rag/` ou `avaliacao/` o tem.

Exceção declarada: as 60 perguntas de `avaliacao/perguntas_v1.jsonl` foram
rascunhadas pelo Claude, a pedido do Lucas, a partir de títulos de reclamações
públicas do Reclame Aqui, e revisadas e aprovadas por ele. O commit leva os
trailers `Rascunho-por: Claude` e `Revisado-por: Lucas`. Elas foram escritas sem
consultar as normas coletadas, mas o Claude conhece o Código de Defesa do
Consumidor, o que pode aproximar os temas do que a lei cobre. As perguntas com
`origem` `rascunho-claude` não vêm de uma reclamação específica, e `url_origem`
aponta para a lista de reclamações da empresa, não para a reclamação exata.
