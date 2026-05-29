from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[2]
PROCESSED_DIR = BASE_DIR / "data" / "processed"
CLEANED_DIR = BASE_DIR / "data" / "cleaned"


def ensure_dirs() -> None:
    CLEANED_DIR.mkdir(parents=True, exist_ok=True)


def load_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict]:
    sales = pd.read_csv(
        PROCESSED_DIR / "fact_sales.csv",
        usecols=[
            "invoice_no",
            "stock_code",
            "description",
            "quantity",
            "unit_price",
            "customer_id",
            "country",
            "invoice_month_start",
            "product_category",
            "line_type",
            "line_revenue",
            "customer_order_type",
        ],
        low_memory=False,
    )
    returns = pd.read_csv(
        PROCESSED_DIR / "fact_returns.csv",
        usecols=[
            "invoice_no",
            "quantity",
            "unit_price",
            "country",
            "invoice_month_start",
            "product_category",
            "return_amount",
        ],
        low_memory=False,
    )
    customers = pd.read_csv(PROCESSED_DIR / "dim_customer_rfm.csv", low_memory=False)
    summary = json.loads((PROCESSED_DIR / "analytics_summary.json").read_text(encoding="utf-8"))

    sales["invoice_month_start"] = pd.to_datetime(sales["invoice_month_start"])
    returns["invoice_month_start"] = pd.to_datetime(returns["invoice_month_start"])
    customers["first_purchase_date"] = pd.to_datetime(customers["first_purchase_date"])
    customers["last_purchase_date"] = pd.to_datetime(customers["last_purchase_date"])
    return sales, returns, customers, summary


def build_sales_monthly(sales: pd.DataFrame) -> pd.DataFrame:
    return (
        sales.groupby(
            ["invoice_month_start", "country", "product_category", "customer_order_type"],
            as_index=False,
        )
        .agg(
            revenue=("line_revenue", "sum"),
            orders=("invoice_no", "nunique"),
            quantity=("quantity", "sum"),
            active_customers=("customer_id", lambda values: values.dropna().nunique()),
        )
        .sort_values(["invoice_month_start", "country", "product_category", "customer_order_type"])
    )


def build_product_monthly(sales: pd.DataFrame) -> pd.DataFrame:
    merchandise = sales.loc[sales["line_type"] == "Merchandise"].copy()
    return (
        merchandise.groupby(
            ["invoice_month_start", "country", "product_category", "stock_code", "description"],
            as_index=False,
        )
        .agg(
            revenue=("line_revenue", "sum"),
            quantity=("quantity", "sum"),
            orders=("invoice_no", "nunique"),
            unit_price=("unit_price", "median"),
        )
        .sort_values(["invoice_month_start", "revenue"], ascending=[True, False])
    )


def build_returns_monthly(returns: pd.DataFrame) -> pd.DataFrame:
    return (
        returns.groupby(["invoice_month_start", "country", "product_category"], as_index=False)
        .agg(
            return_amount=("return_amount", "sum"),
            return_orders=("invoice_no", "nunique"),
            return_units=("quantity", lambda values: values.abs().sum()),
        )
        .sort_values(["invoice_month_start", "return_amount"], ascending=[True, False])
    )


def build_country_monthly(sales: pd.DataFrame) -> pd.DataFrame:
    return (
        sales.groupby(["invoice_month_start", "country"], as_index=False)
        .agg(
            revenue=("line_revenue", "sum"),
            orders=("invoice_no", "nunique"),
            customers=("customer_id", lambda values: values.dropna().nunique()),
            quantity=("quantity", "sum"),
        )
        .sort_values(["invoice_month_start", "revenue"], ascending=[True, False])
    )


def build_category_monthly(sales: pd.DataFrame) -> pd.DataFrame:
    merchandise = sales.loc[sales["line_type"] == "Merchandise"].copy()
    return (
        merchandise.groupby(["invoice_month_start", "product_category"], as_index=False)
        .agg(revenue=("line_revenue", "sum"), quantity=("quantity", "sum"))
        .sort_values(["invoice_month_start", "revenue"], ascending=[True, False])
    )


def build_customer_export(customers: pd.DataFrame) -> pd.DataFrame:
    export = customers.copy()
    export["customer_id"] = export["customer_id"].astype("Int64")
    export["customer_lifetime_value"] = export["monetary_value"]
    export["purchase_frequency"] = export["orders"]
    return export.sort_values("monetary_value", ascending=False)


def build_downloadable_insights(summary: dict) -> str:
    kpis = summary["kpis"]
    lines = [
        "Retail Sales Performance & Customer Insights Dashboard",
        "",
        f"Total Revenue: {kpis['total_revenue']:.2f}",
        f"Total Orders: {kpis['total_orders']}",
        f"Active Customers: {kpis['active_customers']}",
        f"Average Order Value: {kpis['average_order_value']:.2f}",
        f"Return Amount: {kpis['return_amount']:.2f}",
        "",
        "Top insights:",
        f"- Peak month: {summary['peak_month']['month']} ({summary['peak_month']['revenue']:.2f})",
        f"- Lowest month: {summary['lowest_month']['month']} ({summary['lowest_month']['revenue']:.2f})",
        f"- Top category: {summary['top_category']['category']} ({summary['top_category']['revenue']:.2f})",
        f"- Top country: {summary['top_country']['country']} ({summary['top_country']['revenue']:.2f})",
    ]
    return "\n".join(lines)


def main() -> None:
    ensure_dirs()
    sales, returns, customers, summary = load_data()

    sales_monthly = build_sales_monthly(sales)
    product_monthly = build_product_monthly(sales)
    returns_monthly = build_returns_monthly(returns)
    country_monthly = build_country_monthly(sales)
    category_monthly = build_category_monthly(sales)
    customer_export = build_customer_export(customers)

    sales_monthly.to_csv(CLEANED_DIR / "streamlit_sales_monthly.csv", index=False)
    product_monthly.to_csv(CLEANED_DIR / "streamlit_product_monthly.csv", index=False)
    returns_monthly.to_csv(CLEANED_DIR / "streamlit_returns_monthly.csv", index=False)
    country_monthly.to_csv(CLEANED_DIR / "streamlit_country_monthly.csv", index=False)
    category_monthly.to_csv(CLEANED_DIR / "streamlit_category_monthly.csv", index=False)
    customer_export.to_csv(CLEANED_DIR / "streamlit_customer_rfm.csv", index=False)
    sales.to_parquet(CLEANED_DIR / "streamlit_sales.parquet", index=False)
    returns.to_parquet(CLEANED_DIR / "streamlit_returns.parquet", index=False)
    (CLEANED_DIR / "streamlit_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (CLEANED_DIR / "streamlit_insights.txt").write_text(build_downloadable_insights(summary), encoding="utf-8")
    (CLEANED_DIR / "README.md").write_text(
        "\n".join(
            [
                "# Streamlit App Data Assets",
                "",
                "This folder stores lightweight aggregated exports used by the Streamlit dashboard.",
                "",
                "- `streamlit_sales.parquet`: line-level sales data with app-safe columns for exact KPI filtering.",
                "- `streamlit_returns.parquet`: line-level returns data for exact return analytics.",
                "- `streamlit_sales_monthly.csv`: monthly revenue, orders, quantity, and active customer metrics by country, category, and customer order type.",
                "- `streamlit_product_monthly.csv`: monthly product revenue and quantity for merchandise products.",
                "- `streamlit_returns_monthly.csv`: monthly returns by country and product category.",
                "- `streamlit_country_monthly.csv`: monthly country performance metrics.",
                "- `streamlit_category_monthly.csv`: monthly product category metrics.",
                "- `streamlit_customer_rfm.csv`: customer-level RFM export for segmentation views.",
                "- `streamlit_summary.json`: KPI and insight summary.",
                "- `streamlit_insights.txt`: downloadable executive narrative.",
            ]
        ),
        encoding="utf-8",
    )
    print("Streamlit assets created in data/cleaned/")


if __name__ == "__main__":
    main()