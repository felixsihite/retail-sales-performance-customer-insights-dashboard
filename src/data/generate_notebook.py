from __future__ import annotations

import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]
NOTEBOOK_PATH = BASE_DIR / "notebooks" / "01_retail_sales_customer_insights.ipynb"


def markdown_cell(text: str) -> dict[str, object]:
    return {"cell_type": "markdown", "metadata": {}, "source": text.splitlines(keepends=True)}


def code_cell(code: str) -> dict[str, object]:
    return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": code.splitlines(keepends=True)}


def build_notebook() -> dict[str, object]:
    cells = [
        markdown_cell(
            "# Retail Sales Performance & Customer Insights Dashboard\n\n"
            "This notebook documents the data cleaning, feature engineering, and exploratory analysis steps used to build the portfolio project around the UCI `Online Retail` dataset."
        ),
        markdown_cell(
            "## Business Objective\n\n"
            "Analyze transaction-level retail data to understand revenue trends, customer behavior, and product performance. "
            "The output supports stakeholder reporting in Power BI and provides actionable recommendations for commercial growth."
        ),
        markdown_cell(
            "## Key Questions\n\n"
            "- How does revenue change by month and season?\n"
            "- Which products and derived product categories generate the most revenue?\n"
            "- How much revenue comes from new versus repeat customers?\n"
            "- Which customer segments deserve retention or upsell attention based on RFM analysis?"
        ),
        code_cell(
            "from pathlib import Path\n"
            "import sys\n"
            "import json\n"
            "\n"
            "import numpy as np\n"
            "import pandas as pd\n"
            "\n"
            "BASE_DIR = Path.cwd()\n"
            "if BASE_DIR.name == 'notebooks':\n"
            "    BASE_DIR = BASE_DIR.parent\n"
            "sys.path.append(str(BASE_DIR))\n"
            "\n"
            "from src.data.build_retail_assets import (\n"
            "    load_raw_data,\n"
            "    clean_transactions,\n"
            "    build_sales_fact,\n"
            "    build_returns_fact,\n"
            "    build_customer_features,\n"
            "    build_product_dimension,\n"
            "    build_date_dimension,\n"
            "    add_date_keys,\n"
            ")\n"
        ),
        code_cell(
            "raw_df = load_raw_data()\n"
            "raw_df.head()"
        ),
        code_cell(
            "raw_df.shape, raw_df.columns.tolist()"
        ),
        markdown_cell("## Data Cleaning"),
        code_cell(
            "cleaned_df, quality_report = clean_transactions(raw_df)\n"
            "quality_report"
        ),
        code_cell(
            "sales_fact = build_sales_fact(cleaned_df)\n"
            "returns_fact = build_returns_fact(cleaned_df)\n"
            "sales_fact, customer_dim = build_customer_features(sales_fact)\n"
            "sales_fact = add_date_keys(sales_fact)\n"
            "returns_fact = add_date_keys(returns_fact)\n"
            "product_dim = build_product_dimension(sales_fact)\n"
            "date_dim = build_date_dimension(cleaned_df)\n"
            "\n"
            "print('fact_sales:', sales_fact.shape)\n"
            "print('fact_returns:', returns_fact.shape)\n"
            "print('dim_customer_rfm:', customer_dim.shape)\n"
            "print('dim_product:', product_dim.shape)\n"
            "print('dim_date:', date_dim.shape)"
        ),
        markdown_cell("## KPI Snapshot"),
        code_cell(
            "kpi_snapshot = {\n"
            "    'total_revenue': round(float(sales_fact['line_revenue'].sum()), 2),\n"
            "    'orders': int(sales_fact['invoice_no'].nunique()),\n"
            "    'active_customers': int(sales_fact['customer_id'].nunique(dropna=True)),\n"
            "    'average_order_value': round(float(sales_fact.groupby('invoice_no')['line_revenue'].sum().mean()), 2),\n"
            "    'return_amount': round(float(returns_fact['return_amount'].sum()), 2),\n"
            "}\n"
            "kpi_snapshot"
        ),
        markdown_cell("## Monthly Revenue Trend"),
        code_cell(
            "monthly_revenue = (\n"
            "    sales_fact.groupby('invoice_month_start', as_index=False)\n"
            "    .agg(revenue=('line_revenue', 'sum'), orders=('invoice_no', 'nunique'))\n"
            "    .sort_values('invoice_month_start')\n"
            ")\n"
            "monthly_revenue['aov'] = monthly_revenue['revenue'] / monthly_revenue['orders']\n"
            "monthly_revenue"
        ),
        markdown_cell("## Product and Category Performance"),
        code_cell(
            "top_categories = (\n"
            "    sales_fact.groupby('product_category', as_index=False)['line_revenue']\n"
            "    .sum()\n"
            "    .sort_values('line_revenue', ascending=False)\n"
            ")\n"
            "top_categories.head(10)"
        ),
        code_cell(
            "top_products = (\n"
            "    sales_fact.loc[sales_fact['line_type'] == 'Merchandise']\n"
            "    .groupby(['stock_code', 'description'], as_index=False)\n"
            "    .agg(revenue=('line_revenue', 'sum'), units=('quantity', 'sum'))\n"
            "    .sort_values('revenue', ascending=False)\n"
            "    .head(10)\n"
            ")\n"
            "top_products"
        ),
        markdown_cell("## Customer Segmentation (RFM)"),
        code_cell(
            "rfm_distribution = (\n"
            "    customer_dim.groupby('rfm_segment', as_index=False)\n"
            "    .agg(customers=('customer_id', 'nunique'), revenue=('monetary_value', 'sum'))\n"
            "    .sort_values('revenue', ascending=False)\n"
            ")\n"
            "rfm_distribution"
        ),
        code_cell(
            "new_vs_repeat = (\n"
            "    sales_fact.loc[sales_fact['customer_order_type'].isin(['New', 'Repeat'])]\n"
            "    .groupby('customer_order_type', as_index=False)['line_revenue']\n"
            "    .sum()\n"
            ")\n"
            "new_vs_repeat"
        ),
        markdown_cell(
            "## Files Created by the Pipeline\n\n"
            "The supporting Python pipeline writes clean datasets, dimensional tables, SQL-ready SQLite tables, and SVG report assets to the repository. "
            "Those outputs are used by the README and Power BI build instructions."
        ),
        code_cell(
            "summary_path = BASE_DIR / 'data' / 'processed' / 'analytics_summary.json'\n"
            "summary = json.loads(summary_path.read_text())\n"
            "summary['kpis']"
        ),
        markdown_cell(
            "## Conclusion\n\n"
            "The dataset shows strong Q4 seasonality, a heavy concentration of revenue in the United Kingdom, and a meaningful dependence on repeat customers and high-value RFM segments. "
            "These outputs provide a strong foundation for stakeholder storytelling inside Power BI."
        ),
    ]

    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": "3.11"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def main() -> None:
    NOTEBOOK_PATH.parent.mkdir(parents=True, exist_ok=True)
    notebook = build_notebook()
    NOTEBOOK_PATH.write_text(json.dumps(notebook, indent=2), encoding="utf-8")
    print(f"Notebook written to {NOTEBOOK_PATH}")


if __name__ == "__main__":
    main()
