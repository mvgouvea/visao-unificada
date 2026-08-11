# Visão Unificada — Junção de PDFs de Viagens

Aplicação em Python para consolidar documentos de viagem em **dois blocos**, conforme exigido pelo processo:

| Bloco | Conteúdo | Arquivo gerado |
|---|---|---|
| **Autorizações** | Autorizações de Viagens Nacionais e Internacionais (juntas) | `autorizacoes_viagens.pdf` |
| **Prestações de Contas** | Prestações de Contas de Viagens | `prestacoes_contas_viagens.pdf` |

Cada bloco resulta em **um único arquivo PDF com múltiplas páginas**, reunindo todos os documentos daquele tipo na ordem definida.

### Comportamento a cada execução

Cada vez que você roda o script (`python merge_pdfs.py` ou pelo **Run** do Cursor):

1. Os PDFs são lidos **de novo** a partir das pastas de entrada (`documentos_originais/`) ou do CSV informado
2. Os blocos em `blocos/` são **gerados novamente do zero**
3. Se já existirem arquivos mesclados, eles são **substituídos** pelos novos

Ou seja: o resultado sempre reflete o conteúdo **atual** das pastas. Se você adicionar, remover ou trocar PDFs em `documentos_originais/` e executar de novo, os arquivos em `blocos/` serão atualizados.

> **Atenção:** feche os PDFs em `blocos/` antes de executar, se estiverem abertos — o Windows não permite sobrescrever arquivos em uso.

---

## Pré-requisitos

- Python 3.10 ou superior
- Acesso aos arquivos PDF referenciados (baixados do banco ou disponíveis em disco)

---

## Instalação

Na raiz do projeto:

```powershell
cd E:\application\dataeasy\_projects\qa\visao-unificada
python -m pip install -r requirements.txt
```

---

## Execução

Há duas formas de uso: **via CSV** (exportado da query do banco) ou **via pastas** com os PDFs já separados.

### Etapa 1 — Colocar os documentos originais

1. Execute a query no banco e baixe/copie os PDFs para as pastas corretas:
   - `documentos_originais/autorizacoes/` — Autorizações de Viagens (Nacionais e Internacionais)
   - `documentos_originais/prestacoes/` — Prestações de Contas de Viagens
2. Escolha uma das opções abaixo para executar a junção.

### Etapa 2 — Executar a junção

#### Opção A — Pastas padrão (mais simples)

Com os PDFs nas pastas acima, basta executar:

```powershell
python merge_pdfs.py
```

Os blocos serão gerados em `blocos/`.

#### Opção B — CSV exportado da query

Exporte o resultado da query para um arquivo CSV com, no mínimo, as colunas de **bloco**, **caminho** e **ordem**.

Exemplo (`manifest.example.csv`):

```csv
bloco;ordem;caminho
autorizacoes;1;C:\documentos\viagens\autorizacao_001.pdf
autorizacoes;2;C:\documentos\viagens\autorizacao_002.pdf
prestacoes;1;C:\documentos\viagens\prestacao_001.pdf
prestacoes;2;C:\documentos\viagens\prestacao_002.pdf
```

Comando:

```powershell
python merge_pdfs.py --manifest resultado_query.csv
```

Se as colunas do export tiverem outros nomes:

```powershell
python merge_pdfs.py `
  --manifest resultado_query.csv `
  --coluna-bloco tipo_documento `
  --coluna-caminho caminho_arquivo `
  --coluna-ordem numero_ordem
```

#### Opção C — Pastas personalizadas

```powershell
python merge_pdfs.py `
  --autorizacoes-dir C:\documentos\autorizacoes `
  --prestacoes-dir C:\documentos\prestacoes `
  --saida blocos
```

Os PDFs de cada pasta são ordenados **pelo nome do arquivo** (ordem alfabética).

> É possível informar apenas uma das pastas, caso exista documento de um bloco só.

### Etapa 3 — Verificar a saída

Após a execução, confira a pasta `blocos/`:

```
blocos/
├── autorizacoes_viagens.pdf
└── prestacoes_contas_viagens.pdf
```

O script exibe no terminal quantos PDFs foram mesclados e o total de páginas por bloco.

---

## Valores aceitos na coluna de bloco

O script reconhece automaticamente variações comuns:

**Autorizações:** `autorizacao`, `autorizacoes`, `autorizacao_nacional`, `autorizacao_internacional`, `autorizacoes_viagens`

**Prestações de Contas:** `prestacao`, `prestacoes`, `prestacao_contas`, `prestacoes_contas`, `prestacao_de_contas`

---

## Parâmetros disponíveis

| Parâmetro | Descrição | Padrão |
|---|---|---|
| `--manifest` | Caminho do CSV exportado da query | — |
| `--autorizacoes-dir` | Pasta com PDFs de autorizações | `documentos_originais/autorizacoes` |
| `--prestacoes-dir` | Pasta com PDFs de prestações de contas | `documentos_originais/prestacoes` |
| `--saida` | Pasta onde os blocos finais serão gravados | `./blocos` |
| `--coluna-bloco` | Nome da coluna de bloco no CSV | `bloco` |
| `--coluna-caminho` | Nome da coluna de caminho no CSV | `caminho` |
| `--coluna-ordem` | Nome da coluna de ordem no CSV | `ordem` |
| `--delimitador` | Delimitador do CSV | `;` |
| `--encoding` | Encoding do CSV | `utf-8-sig` |

---

## Estrutura de diretórios

```
visao-unificada/
├── documentos_originais/     # PDFs originais (entrada)
│   ├── autorizacoes/         # Autorizações de Viagens (Nacionais e Internacionais)
│   └── prestacoes/           # Prestações de Contas de Viagens
├── blocos/                   # PDFs mesclados (saída)
│   ├── autorizacoes_viagens.pdf
│   └── prestacoes_contas_viagens.pdf
├── merge_pdfs.py
├── requirements.txt
├── manifest.example.csv
└── README.md
```

Coloque os PDFs baixados da query nas subpastas de `documentos_originais/`. Os blocos finais serão gravados em `blocos/`.

---

## Problemas comuns

| Situação | Causa provável | Solução |
|---|---|---|
| `Permission denied` ao gravar | PDF de saída aberto em outro programa | Feche `blocos/autorizacoes_viagens.pdf` ou `blocos/prestacoes_contas_viagens.pdf` e rode de novo |
| `PDF não encontrado` | Caminho inválido ou arquivo não baixado | Confira se o caminho no CSV existe no disco |
| `Bloco desconhecido` | Valor não reconhecido na coluna de bloco | Use `autorizacoes` ou `prestacoes` (ou alias listado acima) |
| `Nenhum PDF encontrado` | Pasta vazia ou sem arquivos `.pdf` | Verifique extensão e conteúdo da pasta |
| Bloco sem documentos | Nenhuma linha/arquivo daquele tipo | O script avisa e não gera o PDF daquele bloco |
