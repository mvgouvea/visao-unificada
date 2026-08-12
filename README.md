# Visão Unificada

Aplicação em Python para **unificar documentos de viagem em dois blocos PDF**, conforme o processo exigido:

| Bloco | Conteúdo | Saída |
|---|---|---|
| Autorizações | Viagens Nacionais e Internacionais (juntas) | `autorizacoes_viagens.pdf` |
| Prestações de Contas | Prestações de Contas de Viagens | `prestacoes_contas_viagens.pdf` |

Cada bloco gera **um único PDF com múltiplas páginas**, reunindo todos os documentos daquele tipo na ordem definida.

---

## Como funciona

1. Coloque os PDFs originais nas pastas de entrada:
   - `documentos_originais/autorizacoes/`
   - `documentos_originais/prestacoes/`
2. Execute o script.
3. Os blocos mesclados são gerados em `blocos/`.

A cada execução, os PDFs são lidos novamente e os arquivos de saída são **regenerados do zero**, refletindo sempre o conteúdo atual das pastas.

---

## Uso

**Instalação**

```bash
python -m pip install -r requirements.txt
```

**Execução padrão** (pastas do projeto)

```bash
python merge_pdfs.py
```

**Via CSV** (export da query do banco)

```bash
python merge_pdfs.py --manifest resultado_query.csv
```

O CSV deve conter colunas de **bloco**, **caminho** e **ordem**. Veja o formato em `manifest.example.csv`.

---

## Próximo passo

A versão atual atende via linha de comando. A evolução prevista inclui **interface gráfica** e fluxo mais intuitivo — seleção e organização de documentos com menos passos manuais, mantendo a mesma regra: dois blocos finais, um PDF por bloco.
