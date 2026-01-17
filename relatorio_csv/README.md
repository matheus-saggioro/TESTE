# Relatório CSV -> PDF

Rotina simples para gerar relatórios PDF em A4 a partir de arquivos CSV. O script detecta automaticamente o separador (`;` ou `,`) e inclui tabelas e gráficos úteis no relatório.

## Requisitos

Instale as dependências:

```bash
pip install -r relatorio_csv/requirements.txt
```

## Como usar

```bash
python relatorio_csv/generate_report.py --csv dados.csv --pdf saida/relatorio.pdf
```

O PDF gerado inclui:

- Resumo de linhas, colunas, valores ausentes e duplicados.
- Estatísticas numéricas (`describe`).
- Top 10 valores por coluna textual.
- Gráficos de ausências e histogramas das 3 principais colunas numéricas.
