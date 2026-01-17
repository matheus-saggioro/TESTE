#!/usr/bin/env python3
import argparse
import os
import tempfile
from datetime import datetime

import matplotlib.pyplot as plt
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def load_csv(csv_path: str) -> pd.DataFrame:
    return pd.read_csv(csv_path, sep=None, engine="python")


def summarize_dataframe(df: pd.DataFrame) -> dict:
    total_missing = int(df.isna().sum().sum())
    duplicates = int(df.duplicated().sum())
    return {
        "rows": df.shape[0],
        "columns": df.shape[1],
        "missing": total_missing,
        "duplicates": duplicates,
    }


def dataframe_to_table(df: pd.DataFrame, max_rows: int = 50) -> Table:
    data = [df.columns.tolist()] + df.head(max_rows).values.tolist()
    table = Table(data, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    return table


def build_missing_chart(df: pd.DataFrame, output_path: str) -> str:
    missing_counts = df.isna().sum().sort_values(ascending=False)
    plt.figure(figsize=(8, 4))
    missing_counts.plot(kind="bar")
    plt.title("Ausências por coluna")
    plt.ylabel("Quantidade de valores ausentes")
    plt.xlabel("Colunas")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    return output_path


def build_histograms(df: pd.DataFrame, output_dir: str) -> list[str]:
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    if not numeric_cols:
        return []
    top_cols = df[numeric_cols].count().sort_values(ascending=False).head(3).index.tolist()
    image_paths: list[str] = []
    for col in top_cols:
        fig_path = os.path.join(output_dir, f"hist_{col}.png")
        plt.figure(figsize=(6, 4))
        df[col].dropna().hist(bins=20)
        plt.title(f"Histograma: {col}")
        plt.xlabel(col)
        plt.ylabel("Frequência")
        plt.tight_layout()
        plt.savefig(fig_path, dpi=150)
        plt.close()
        image_paths.append(fig_path)
    return image_paths


def build_report(df: pd.DataFrame, pdf_path: str, csv_path: str) -> None:
    os.makedirs(os.path.dirname(pdf_path), exist_ok=True)

    doc = SimpleDocTemplate(pdf_path, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("Relatório CSV", styles["Title"]))
    elements.append(Paragraph(f"Arquivo: {os.path.basename(csv_path)}", styles["Normal"]))
    elements.append(Paragraph(f"Gerado em: {datetime.now():%d/%m/%Y %H:%M}", styles["Normal"]))
    elements.append(Spacer(1, 12))

    summary = summarize_dataframe(df)
    summary_data = [
        ["Linhas", summary["rows"]],
        ["Colunas", summary["columns"]],
        ["Valores ausentes", summary["missing"]],
        ["Linhas duplicadas", summary["duplicates"]],
    ]
    elements.append(Paragraph("Resumo", styles["Heading2"]))
    elements.append(Table(summary_data, hAlign="LEFT"))
    elements.append(Spacer(1, 12))

    numeric_df = df.select_dtypes(include="number")
    elements.append(Paragraph("Estatísticas numéricas", styles["Heading2"]))
    if numeric_df.empty:
        elements.append(Paragraph("Não há colunas numéricas no arquivo.", styles["Normal"]))
    else:
        describe_df = numeric_df.describe().reset_index().rename(columns={"index": "estatística"})
        elements.append(dataframe_to_table(describe_df))
    elements.append(Spacer(1, 12))

    text_cols = df.select_dtypes(include="object").columns.tolist()
    elements.append(Paragraph("Top 10 valores por coluna textual", styles["Heading2"]))
    if not text_cols:
        elements.append(Paragraph("Não há colunas textuais no arquivo.", styles["Normal"]))
    else:
        for col in text_cols:
            top_values = df[col].astype(str).value_counts(dropna=True).head(10)
            top_df = top_values.reset_index()
            top_df.columns = [col, "contagem"]
            elements.append(Paragraph(col, styles["Heading3"]))
            elements.append(dataframe_to_table(top_df))
            elements.append(Spacer(1, 8))

    elements.append(Paragraph("Gráficos", styles["Heading2"]))
    with tempfile.TemporaryDirectory() as tmpdir:
        missing_chart = build_missing_chart(df, os.path.join(tmpdir, "missing.png"))
        elements.append(Image(missing_chart, width=400, height=200))
        elements.append(Spacer(1, 12))

        histograms = build_histograms(df, tmpdir)
        if histograms:
            for hist_path in histograms:
                elements.append(Image(hist_path, width=350, height=240))
                elements.append(Spacer(1, 12))
        else:
            elements.append(Paragraph("Sem colunas numéricas para histogramas.", styles["Normal"]))

        doc.build(elements)


def main() -> None:
    parser = argparse.ArgumentParser(description="Gerador de relatório CSV -> PDF")
    parser.add_argument("--csv", required=True, help="Caminho do CSV de entrada")
    parser.add_argument("--pdf", required=True, help="Caminho do PDF de saída")
    args = parser.parse_args()

    df = load_csv(args.csv)
    build_report(df, args.pdf, args.csv)


if __name__ == "__main__":
    main()
