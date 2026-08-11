#!/usr/bin/env python3
"""
Junta PDFs de viagens em dois blocos:
  - autorizacoes: Autorizações de Viagens (Nacionais e Internacionais)
  - prestacoes: Prestações de Contas de Viagens

Cada execução relê os PDFs de entrada e sobrescreve os blocos em `blocos/`.
"""

from __future__ import annotations

import argparse
import csv
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from pypdf import PdfReader, PdfWriter


# Mapeamento interno do bloco para o nome fixo do arquivo de saída.
BLOCOS = {
    "autorizacoes": "autorizacoes_viagens.pdf",
    "prestacoes": "prestacoes_contas_viagens.pdf",
}

# Variações de nomenclatura vindas da query do banco ou do CSV exportado.
ALIASES = {
    "autorizacao": "autorizacoes",
    "autorizacoes": "autorizacoes",
    "autorizacoes_viagens": "autorizacoes",
    "autorizacao_viagem": "autorizacoes",
    "autorizacao_nacional": "autorizacoes",
    "autorizacao_internacional": "autorizacoes",
    "prestacao": "prestacoes",
    "prestacoes": "prestacoes",
    "prestacao_contas": "prestacoes",
    "prestacoes_contas": "prestacoes",
    "prestacao_de_contas": "prestacoes",
}


@dataclass(frozen=True)
class Documento:
    bloco: str
    ordem: int
    caminho: Path


def normalizar_bloco(valor: str) -> str:
    """Converte rótulos do banco/CSV para as chaves internas dos blocos."""
    chave = valor.strip().lower().replace("-", "_").replace(" ", "_")
    bloco = ALIASES.get(chave)
    if not bloco:
        raise ValueError(
            f"Bloco desconhecido: {valor!r}. "
            f"Use 'autorizacoes' ou 'prestacoes' (ou alias equivalente)."
        )
    return bloco


def ler_manifesto(
    caminho: Path,
    *,
    coluna_bloco: str,
    coluna_caminho: str,
    coluna_ordem: str | None,
    delimitador: str,
    encoding: str,
) -> list[Documento]:
    """Carrega a lista de PDFs a partir do CSV exportado da query do banco."""
    documentos: list[Documento] = []

    with caminho.open("r", encoding=encoding, newline="") as arquivo:
        leitor = csv.DictReader(arquivo, delimiter=delimitador)
        if not leitor.fieldnames:
            raise ValueError(f"Manifesto vazio: {caminho}")

        # Permite colunas com nomes diferentes no export (case-insensitive).
        campos = {nome.strip().lower(): nome for nome in leitor.fieldnames}
        for obrigatoria in (coluna_bloco, coluna_caminho):
            if obrigatoria.lower() not in campos:
                raise ValueError(
                    f"Coluna '{obrigatoria}' não encontrada em {caminho}. "
                    f"Colunas disponíveis: {', '.join(leitor.fieldnames)}"
                )

        nome_bloco = campos[coluna_bloco.lower()]
        nome_caminho = campos[coluna_caminho.lower()]
        nome_ordem = campos[coluna_ordem.lower()] if coluna_ordem else None

        for indice, linha in enumerate(leitor, start=2):
            valor_bloco = (linha.get(nome_bloco) or "").strip()
            valor_caminho = (linha.get(nome_caminho) or "").strip()
            if not valor_bloco and not valor_caminho:
                continue
            if not valor_bloco or not valor_caminho:
                raise ValueError(
                    f"Linha {indice} incompleta em {caminho}: "
                    f"bloco={valor_bloco!r}, caminho={valor_caminho!r}"
                )

            # Usa a coluna de ordem quando existir; senão, preserva a ordem do CSV.
            if nome_ordem and (linha.get(nome_ordem) or "").strip():
                ordem = int(str(linha[nome_ordem]).strip())
            else:
                ordem = indice

            documentos.append(
                Documento(
                    bloco=normalizar_bloco(valor_bloco),
                    ordem=ordem,
                    caminho=Path(valor_caminho),
                )
            )

    return documentos


def listar_pdfs_diretorio(diretorio: Path) -> list[Path]:
    """Lista PDFs da pasta ordenados alfabeticamente pelo nome do arquivo."""
    if not diretorio.is_dir():
        raise FileNotFoundError(f"Diretório não encontrado: {diretorio}")

    return sorted(
        (item for item in diretorio.iterdir() if item.is_file() and item.suffix.lower() == ".pdf"),
        key=lambda item: item.name.lower(),
    )


def documentos_por_diretorios(
    autorizacoes_dir: Path | None,
    prestacoes_dir: Path | None,
) -> list[Documento]:
    """Modo padrão: lê todos os PDFs das pastas de documentos originais."""
    documentos: list[Documento] = []

    if autorizacoes_dir:
        for ordem, caminho in enumerate(listar_pdfs_diretorio(autorizacoes_dir), start=1):
            documentos.append(Documento("autorizacoes", ordem, caminho))

    if prestacoes_dir:
        for ordem, caminho in enumerate(listar_pdfs_diretorio(prestacoes_dir), start=1):
            documentos.append(Documento("prestacoes", ordem, caminho))

    if not documentos:
        raise ValueError(
            "Nenhum PDF encontrado. Coloque os arquivos em "
            "documentos_originais/autorizacoes e/ou documentos_originais/prestacoes."
        )

    return documentos


def agrupar_por_bloco(documentos: Iterable[Documento]) -> dict[str, list[Documento]]:
    """Separa os documentos por bloco e ordena antes da mesclagem."""
    agrupados: dict[str, list[Documento]] = {bloco: [] for bloco in BLOCOS}
    for documento in documentos:
        agrupados.setdefault(documento.bloco, []).append(documento)

    for bloco, itens in agrupados.items():
        itens.sort(key=lambda item: (item.ordem, str(item.caminho).lower()))

    return agrupados


def mesclar_bloco(documentos: list[Documento], destino: Path) -> int:
    """
    Concatena os PDFs de um bloco e grava o arquivo final.

    Sobrescreve `destino` se já existir (comportamento esperado a cada execução).
    """
    if not documentos:
        return 0

    writer = PdfWriter()
    paginas = 0

    for documento in documentos:
        caminho = documento.caminho
        if not caminho.is_file():
            raise FileNotFoundError(f"PDF não encontrado: {caminho}")

        reader = PdfReader(str(caminho))
        # Tenta abrir PDFs protegidos sem senha (comum em exports do sistema).
        if reader.is_encrypted:
            reader.decrypt("")

        for pagina in reader.pages:
            writer.add_page(pagina)
            paginas += 1

    destino.parent.mkdir(parents=True, exist_ok=True)
    try:
        with destino.open("wb") as saida:
            writer.write(saida)
    except PermissionError as exc:
        raise PermissionError(
            f"Não foi possível gravar {destino}. "
            "Feche o arquivo se estiver aberto em outro programa (leitor de PDF, navegador etc.) "
            "e execute novamente."
        ) from exc

    return paginas


def construir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Junta PDFs de viagens em dois blocos (autorizações e prestações de contas)."
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        help="CSV exportado da query do banco com colunas de bloco, caminho e ordem.",
    )
    parser.add_argument(
        "--autorizacoes-dir",
        type=Path,
        default=Path("documentos_originais/autorizacoes"),
        help="Diretório com PDFs de Autorizações de Viagens (padrão: documentos_originais/autorizacoes).",
    )
    parser.add_argument(
        "--prestacoes-dir",
        type=Path,
        default=Path("documentos_originais/prestacoes"),
        help="Diretório com PDFs de Prestações de Contas (padrão: documentos_originais/prestacoes).",
    )
    parser.add_argument(
        "--saida",
        type=Path,
        default=Path("blocos"),
        help="Diretório de saída dos blocos mesclados (padrão: ./blocos).",
    )
    parser.add_argument(
        "--coluna-bloco",
        default="bloco",
        help="Nome da coluna de bloco no CSV (padrão: bloco).",
    )
    parser.add_argument(
        "--coluna-caminho",
        default="caminho",
        help="Nome da coluna de caminho no CSV (padrão: caminho).",
    )
    parser.add_argument(
        "--coluna-ordem",
        default="ordem",
        help="Nome da coluna de ordem no CSV (padrão: ordem). Use vazio para ordem da linha.",
    )
    parser.add_argument(
        "--delimitador",
        default=";",
        help="Delimitador do CSV (padrão: ';').",
    )
    parser.add_argument(
        "--encoding",
        default="utf-8-sig",
        help="Encoding do CSV (padrão: utf-8-sig).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = construir_parser()
    args = parser.parse_args(argv)

    # Fonte dos PDFs: CSV da query ou pastas locais (padrão).
    if args.manifest:
        coluna_ordem = args.coluna_ordem.strip() or None
        documentos = ler_manifesto(
            args.manifest,
            coluna_bloco=args.coluna_bloco,
            coluna_caminho=args.coluna_caminho,
            coluna_ordem=coluna_ordem,
            delimitador=args.delimitador,
            encoding=args.encoding,
        )
    else:
        documentos = documentos_por_diretorios(args.autorizacoes_dir, args.prestacoes_dir)

    agrupados = agrupar_por_bloco(documentos)
    saida = args.saida.resolve()
    total_paginas = 0
    arquivos_gerados = 0

    print(f"Saída: {saida}")
    # Um arquivo de saída por bloco; cada execução regenera os PDFs mesclados.
    for bloco, nome_arquivo in BLOCOS.items():
        itens = agrupados.get(bloco, [])
        if not itens:
            print(f"[AVISO] Bloco '{bloco}' sem documentos — arquivo não gerado.")
            continue

        destino = saida / nome_arquivo
        paginas = mesclar_bloco(itens, destino)
        total_paginas += paginas
        arquivos_gerados += 1
        print(
            f"[OK] {destino.name}: {len(itens)} PDF(s), {paginas} página(s) "
            f"-> {destino}"
        )

    if arquivos_gerados == 0:
        print("[ERRO] Nenhum bloco foi gerado.", file=sys.stderr)
        return 1

    print(f"Concluído: {arquivos_gerados} arquivo(s), {total_paginas} página(s) no total.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
