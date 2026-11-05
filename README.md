# Assistente de Documentos

Assistente que responde perguntas sobre leis brasileiras do consumidor (CDC,
Decreto 7.962/2013 e Decreto 13.135/2026), sempre citando norma, artigo,
parágrafo e inciso. Projeto individual de estudo, com foco em avaliação
reproduzível. O PRD está em `docs/prd/assistente-documentos.md`.

Informação geral sobre a lei. Não é orientação jurídica e não substitui
advogado ou Procon.

## Estado atual: M0 (Fundação)

Existem apenas os tipos compartilhados (`comum/tipos.py`), o contrato do núcleo
(`comum/contrato.py`), testes e CI. Ainda não há ingestão, busca nem resposta.

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
