from __future__ import annotations

import json
from pathlib import Path

import altair as alt
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


PAGE_TITLE = "Retail Sales Performance & Customer Insights"
REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data" / "cleaned"

COLORS = {
    "bg": "#0B1120",
    "panel": "#111A2E",
    "panel_alt": "#131F36",
    "text": "#E2E8F0",
    "muted": "#94A3B8",
    "cyan": "#22D3EE",
    "blue": "#60A5FA",
    "purple": "#8B5CF6",
    "pink": "#EC4899",
    "emerald": "#34D399",
    "amber": "#F59E0B",
    "red": "#F43F5E",
}


def apply_custom_css() -> None:
    st.markdown(
        f"""
        <style>
            .stApp {{
                background:
                    radial-gradient(circle at top right, rgba(139, 92, 246, 0.16), transparent 28%),
                    radial-gradient(circle at top left, rgba(34, 211, 238, 0.14), transparent 24%),
                    linear-gradient(180deg, #08101f 0%, #0b1120 52%, #0a1020 100%);
                color: {COLORS['text']};
            }}
            [data-testid="stSidebar"] {{
                background: linear-gradient(180deg, rgba(15, 23, 42, 0.98) 0%, rgba(17, 24, 39, 0.98) 100%);
                border-right: 1px solid rgba(148, 163, 184, 0.18);
            }}
            .block-container {{
                padding-top: 2.35rem;
                padding-bottom: 2rem;
                max-width: 1380px;
            }}
            .page-hero {{
                padding: 0.78rem 1.55rem 1.1rem;
                border: 1px solid rgba(255,255,255,0.08);
                border-radius: 20px;
                background: linear-gradient(135deg, rgba(15, 23, 42, 0.86), rgba(30, 41, 59, 0.72));
                box-shadow: 0 18px 55px rgba(2, 6, 23, 0.34);
                margin-top: 0.72rem;
                margin-bottom: 1.15rem;
                min-height: 124px;
                display: flex;
                flex-direction: column;
                justify-content: flex-end;
                align-items: flex-start;
            }}
            .hero-kicker {{
                text-transform: uppercase;
                letter-spacing: 0.08em;
                font-size: 0.8rem;
                color: {COLORS['cyan']};
                margin-bottom: 0.25rem;
                font-weight: 700;
            }}
            .hero-title {{
                font-size: 2.15rem;
                line-height: 1.04;
                font-weight: 800;
                color: #F8FAFC;
                margin-bottom: 0.35rem;
            }}
            .hero-subtitle {{
                color: {COLORS['muted']};
                font-size: 0.98rem;
                line-height: 1.42;
                margin-bottom: 0;
                max-width: 90%;
            }}
            .metric-card {{
                background: linear-gradient(180deg, rgba(17, 26, 46, 0.88), rgba(15, 23, 42, 0.88));
                border: 1px solid rgba(255,255,255,0.08);
                border-radius: 18px;
                padding: 1rem 1.1rem 0.95rem;
                min-height: 160px;
                box-shadow: 0 16px 40px rgba(2, 6, 23, 0.3);
                position: relative;
                overflow: hidden;
            }}
            .metric-card::after {{
                content: "";
                position: absolute;
                inset: 0 auto auto 0;
                width: 100%;
                height: 3px;
                background: var(--accent, {COLORS['purple']});
            }}
            .metric-label {{
                color: {COLORS['muted']};
                font-size: 0.95rem;
                margin-bottom: 0.6rem;
                font-weight: 600;
            }}
            .metric-value {{
                color: #F8FAFC;
                font-size: clamp(1.9rem, 2.6vw, 2.7rem);
                font-weight: 800;
                line-height: 1.05;
                word-break: break-word;
            }}
            .metric-note {{
                color: {COLORS['muted']};
                font-size: 0.86rem;
                margin-top: 0.45rem;
            }}
            .filter-helper {{
                color: {COLORS['muted']};
                font-size: 0.82rem;
                margin-top: -0.35rem;
                margin-bottom: 0.4rem;
            }}
            .section-caption {{
                color: {COLORS['muted']};
                font-size: 0.9rem;
                margin: 0.2rem 0 1rem;
            }}
            .download-box {{
                padding: 0.9rem 1rem;
                border: 1px solid rgba(255,255,255,0.08);
                border-radius: 16px;
                background: rgba(15, 23, 42, 0.66);
                margin-top: 0.75rem;
            }}
            div[data-testid="stPlotlyChart"], div[data-testid="stAltairChart"], div[data-testid="stDataFrame"] {{
                border: 1px solid rgba(255,255,255,0.08);
                border-radius: 18px;
                background: rgba(17, 26, 46, 0.8);
                box-shadow: 0 16px 36px rgba(2, 6, 23, 0.25);
                padding: 0.35rem;
            }}
            .chart-title {{
                color: #F8FAFC;
                font-size: 1.05rem;
                font-weight: 700;
                margin: 0.25rem 0 0.7rem;
            }}
            div[data-baseweb="select"] > div,
            div[data-baseweb="input"] > div,
            .stDateInput > div {{
                border-radius: 12px !important;
            }}
            @media (max-width: 1200px) {{
                .block-container {{
                    padding-top: 2.05rem;
                }}
                .page-hero {{
                    min-height: 120px;
                    padding-top: 0.72rem;
                    padding-bottom: 1rem;
                    margin-top: 0.55rem;
                }}
                .metric-card {{
                    min-height: 148px;
                }}
            }}
            @media (max-width: 900px) {{
                .block-container {{
                    padding-top: 1.72rem;
                }}
                .hero-title {{
                    font-size: 1.8rem;
                }}
                .hero-subtitle {{
                    max-width: 100%;
                }}
                .page-hero {{
                    min-height: 128px;
                    padding: 0.8rem 1.15rem 1rem;
                    margin-top: 0.45rem;
                    margin-bottom: 1rem;
                }}
                .metric-card {{
                    min-height: 138px;
                }}
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_data(show_spinner=False)
def load_assets() -> dict[str, object]:
    sales = pd.read_parquet(DATA_DIR / "streamlit_sales.parquet")
    returns = pd.read_parquet(DATA_DIR / "streamlit_returns.parquet")
    customers = pd.read_csv(DATA_DIR / "streamlit_customer_rfm.csv", low_memory=False)
    summary = json.loads((DATA_DIR / "streamlit_summary.json").read_text(encoding="utf-8"))
    insights_text = (DATA_DIR / "streamlit_insights.txt").read_text(encoding="utf-8")

    sales["invoice_month_start"] = pd.to_datetime(sales["invoice_month_start"])
    returns["invoice_month_start"] = pd.to_datetime(returns["invoice_month_start"])
    customers["first_purchase_date"] = pd.to_datetime(customers["first_purchase_date"])
    customers["last_purchase_date"] = pd.to_datetime(customers["last_purchase_date"])
    customers["customer_id"] = customers["customer_id"].astype("Int64")
    return {
        "sales": sales,
        "returns": returns,
        "customers": customers,
        "summary": summary,
        "insights_text": insights_text,
    }


def compact_number(value: float, currency: bool = False) -> str:
    prefix = "$" if currency else ""
    abs_value = abs(value)
    if abs_value >= 1_000_000:
        return f"{prefix}{value / 1_000_000:.2f}M"
    if abs_value >= 1_000:
        return f"{prefix}{value / 1_000:.1f}K"
    if currency:
        return f"{prefix}{value:,.2f}"
    if float(value).is_integer():
        return f"{int(value):,}"
    return f"{value:,.2f}"


def pct(value: float) -> str:
    return f"{value * 100:.2f}%"


def create_metric_card(label: str, value: str, note: str, accent: str) -> str:
    return f"""
    <div class="metric-card" style="--accent:{accent}">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        <div class="metric-note">{note}</div>
    </div>
    """


def multiselect_with_toggle(
    label: str,
    options: list[str],
    key_prefix: str,
    helper_text: str,
) -> list[str]:
    toggle = st.sidebar.checkbox(f"All {label.lower()}", value=True, key=f"{key_prefix}_all")
    st.sidebar.markdown(f'<div class="filter-helper">{helper_text}</div>', unsafe_allow_html=True)
    if toggle:
        return options
    return st.sidebar.multiselect(label, options, default=options[: min(5, len(options))], key=f"{key_prefix}_picker")


def build_sidebar_filters(sales: pd.DataFrame, insights_text: str) -> dict[str, object]:
    st.sidebar.markdown("## Explore the dashboard")
    min_date = sales["invoice_month_start"].min().date()
    max_date = sales["invoice_month_start"].max().date()
    default_dates = (min_date, max_date)
    selected_dates = st.sidebar.date_input("Date range", value=default_dates, min_value=min_date, max_value=max_date)
    if len(selected_dates) == 1:
        selected_dates = (selected_dates[0], selected_dates[0])

    countries = sorted(sales["country"].dropna().unique().tolist())
    categories = sorted(sales["product_category"].dropna().unique().tolist())
    order_types = sorted(sales["customer_order_type"].dropna().unique().tolist())

    selected_countries = multiselect_with_toggle(
        "Country",
        countries,
        "country",
        "Keep all countries selected for a full-market view, or narrow to a few focus markets.",
    )
    selected_categories = multiselect_with_toggle(
        "Product category",
        categories,
        "category",
        "Use product categories to focus the dashboard on a specific revenue mix.",
    )
    selected_order_types = multiselect_with_toggle(
        "Customer order type",
        order_types,
        "order_type",
        "Switch between all orders or only new/repeat customer behavior.",
    )

    st.sidebar.markdown('<div class="download-box">', unsafe_allow_html=True)
    st.sidebar.markdown("### Export")
    st.sidebar.caption("Download an executive insight summary or the filtered monthly view.")
    st.sidebar.download_button(
        "Download insight summary",
        insights_text,
        file_name="retail_insights_summary.txt",
        mime="text/plain",
        use_container_width=True,
    )
    st.sidebar.markdown("</div>", unsafe_allow_html=True)

    return {
        "date_start": pd.Timestamp(selected_dates[0]),
        "date_end": pd.Timestamp(selected_dates[1]),
        "countries": selected_countries,
        "categories": selected_categories,
        "order_types": selected_order_types,
    }


def filter_sales(sales: pd.DataFrame, filters: dict[str, object]) -> pd.DataFrame:
    mask = (
        sales["invoice_month_start"].between(filters["date_start"], filters["date_end"])
        & sales["country"].isin(filters["countries"])
        & sales["product_category"].isin(filters["categories"])
        & sales["customer_order_type"].isin(filters["order_types"])
    )
    return sales.loc[mask].copy()


def filter_returns(returns: pd.DataFrame, filters: dict[str, object]) -> pd.DataFrame:
    mask = (
        returns["invoice_month_start"].between(filters["date_start"], filters["date_end"])
        & returns["country"].isin(filters["countries"])
        & returns["product_category"].isin(filters["categories"])
    )
    return returns.loc[mask].copy()


def filter_customers(customers: pd.DataFrame, filters: dict[str, object]) -> pd.DataFrame:
    filtered = customers.copy()
    if filters["countries"]:
        filtered = filtered.loc[filtered["primary_country"].isin(filters["countries"])]
    return filtered


def build_plotly_template() -> str:
    template = go.layout.Template()
    template.layout = go.Layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=COLORS["text"], family="Segoe UI"),
        margin=dict(l=16, r=16, t=36, b=16),
        xaxis=dict(gridcolor="rgba(148, 163, 184, 0.18)", zeroline=False),
        yaxis=dict(gridcolor="rgba(148, 163, 184, 0.18)", zeroline=False),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
    )
    pio_template_name = "retail_streamlit"
    import plotly.io as pio

    pio.templates[pio_template_name] = template
    return pio_template_name


def page_header(title: str, subtitle: str, kicker: str) -> None:
    st.markdown(
        f"""
        <div class="page-hero">
            <div class="hero-kicker">{kicker}</div>
            <div class="hero-title">{title}</div>
            <p class="hero-subtitle">{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def build_insight_text(filtered_sales: pd.DataFrame, filtered_returns: pd.DataFrame, filtered_customers: pd.DataFrame) -> str:
    total_revenue = filtered_sales["line_revenue"].sum()
    total_orders = filtered_sales["invoice_no"].nunique()
    total_customers = filtered_sales["customer_id"].dropna().nunique()
    return_amount = filtered_returns["return_amount"].sum()
    top_country = filtered_sales.groupby("country")["line_revenue"].sum().sort_values(ascending=False)
    top_category = filtered_sales.groupby("product_category")["line_revenue"].sum().sort_values(ascending=False)
    top_segment = filtered_customers.groupby("rfm_segment")["monetary_value"].sum().sort_values(ascending=False)

    lines = [
        "Filtered Retail Dashboard Summary",
        "",
        f"Revenue: {total_revenue:,.2f}",
        f"Orders: {total_orders:,}",
        f"Customers: {total_customers:,}",
        f"Return amount: {return_amount:,.2f}",
    ]
    if not top_country.empty:
        lines.append(f"Top country: {top_country.index[0]} ({top_country.iloc[0]:,.2f})")
    if not top_category.empty:
        lines.append(f"Top category: {top_category.index[0]} ({top_category.iloc[0]:,.2f})")
    if not top_segment.empty:
        lines.append(f"Top customer segment: {top_segment.index[0]} ({top_segment.iloc[0]:,.2f})")
    return "\n".join(lines)


def render_executive_overview(filtered_sales: pd.DataFrame, filtered_returns: pd.DataFrame, template: str) -> None:
    page_header(
        "Executive KPI Storyboard",
        "A leadership-ready snapshot of revenue, demand, retention mix, and return leakage.",
        "Executive Overview",
    )

    total_revenue = filtered_sales["line_revenue"].sum()
    total_orders = filtered_sales["invoice_no"].nunique()
    active_customers = filtered_sales["customer_id"].dropna().nunique()
    aov = total_revenue / total_orders if total_orders else 0
    return_amount = filtered_returns["return_amount"].sum()
    return_rate = return_amount / total_revenue if total_revenue else 0

    cards = [
        ("Total Revenue", compact_number(total_revenue, currency=True), "Positive sales value", COLORS["cyan"]),
        ("Total Orders", compact_number(total_orders), "Distinct invoices", COLORS["emerald"]),
        ("Average Order Value", compact_number(aov, currency=True), "Revenue per order", COLORS["amber"]),
        ("Active Customers", compact_number(active_customers), "Known customers only", COLORS["purple"]),
        ("Return Amount", compact_number(return_amount, currency=True), "Potential leakage", COLORS["pink"]),
        ("Return Rate", pct(return_rate), "Returns as % of revenue", COLORS["blue"]),
    ]
    first_row = st.columns(3, gap="medium")
    second_row = st.columns(3, gap="medium")
    for col, card in zip(first_row, cards[:3], strict=False):
        with col:
            st.markdown(create_metric_card(*card), unsafe_allow_html=True)
    for col, card in zip(second_row, cards[3:], strict=False):
        with col:
            st.markdown(create_metric_card(*card), unsafe_allow_html=True)

    monthly = (
        filtered_sales.groupby("invoice_month_start", as_index=False)["line_revenue"]
        .sum()
        .rename(columns={"line_revenue": "revenue"})
        .sort_values("invoice_month_start")
    )
    country = (
        filtered_sales.groupby("country", as_index=False)["line_revenue"]
        .sum()
        .rename(columns={"line_revenue": "revenue"})
        .sort_values("revenue", ascending=False)
        .head(10)
    )
    categories = (
        filtered_sales.groupby("product_category", as_index=False)["line_revenue"]
        .sum()
        .rename(columns={"line_revenue": "revenue"})
        .sort_values("revenue", ascending=False)
        .head(8)
    )
    new_repeat = (
        filtered_sales.loc[filtered_sales["customer_order_type"].isin(["New", "Repeat"])]
        .groupby("customer_order_type", as_index=False)["line_revenue"]
        .sum()
        .rename(columns={"line_revenue": "revenue"})
    )

    chart_col1, chart_col2 = st.columns((1.45, 1))
    with chart_col1:
        st.markdown('<div class="chart-title">Revenue Trend Over Time</div>', unsafe_allow_html=True)
        trend_fig = px.line(
            monthly,
            x="invoice_month_start",
            y="revenue",
            markers=True,
            color_discrete_sequence=[COLORS["cyan"]],
            template=template,
        )
        trend_fig.update_traces(line=dict(width=4))
        trend_fig.update_layout(yaxis_title="Revenue", xaxis_title="")
        st.plotly_chart(trend_fig, use_container_width=True)

    with chart_col2:
        st.markdown('<div class="chart-title">Revenue by Country</div>', unsafe_allow_html=True)
        country_fig = px.bar(
            country.sort_values("revenue"),
            x="revenue",
            y="country",
            orientation="h",
            color_discrete_sequence=[COLORS["blue"]],
            template=template,
        )
        country_fig.update_layout(xaxis_title="Revenue", yaxis_title="")
        st.plotly_chart(country_fig, use_container_width=True)

    chart_col3, chart_col4 = st.columns((1.1, 1))
    with chart_col3:
        st.markdown('<div class="chart-title">Revenue by Product Category</div>', unsafe_allow_html=True)
        category_fig = px.bar(
            categories.sort_values("revenue"),
            x="revenue",
            y="product_category",
            orientation="h",
            color_discrete_sequence=[COLORS["emerald"]],
            template=template,
        )
        category_fig.update_layout(xaxis_title="Revenue", yaxis_title="")
        st.plotly_chart(category_fig, use_container_width=True)

    with chart_col4:
        st.markdown('<div class="chart-title">New vs Repeat Revenue Mix</div>', unsafe_allow_html=True)
        donut_fig = px.pie(
            new_repeat,
            names="customer_order_type",
            values="revenue",
            hole=0.58,
            color="customer_order_type",
            color_discrete_map={"New": COLORS["amber"], "Repeat": COLORS["cyan"]},
            template=template,
        )
        donut_fig.update_layout(showlegend=True)
        st.plotly_chart(donut_fig, use_container_width=True)


def render_customer_insights(filtered_sales: pd.DataFrame, filtered_customers: pd.DataFrame, template: str) -> None:
    page_header(
        "Customer Segmentation & Value",
        "Understand who drives revenue, how often they buy, and which RFM groups deserve attention.",
        "Customer Insights",
    )

    segment_options = sorted(filtered_customers["rfm_segment"].dropna().unique().tolist())
    selected_segments = st.multiselect("Focus RFM segments", segment_options, default=segment_options)
    customer_view = filtered_customers.loc[filtered_customers["rfm_segment"].isin(selected_segments)].copy()

    segment_bar = (
        customer_view.groupby("rfm_segment", as_index=False)["customer_id"]
        .nunique()
        .rename(columns={"customer_id": "customers"})
        .sort_values("customers", ascending=False)
    )
    segment_table = (
        customer_view.groupby("rfm_segment", as_index=False)
        .agg(
            segment_customers=("customer_id", "nunique"),
            segment_revenue=("monetary_value", "sum"),
            average_order_value=("avg_order_value", "mean"),
            avg_recency_days=("recency_days", "mean"),
        )
        .sort_values("segment_revenue", ascending=False)
    )
    new_repeat_trend = (
        filtered_sales.loc[filtered_sales["customer_order_type"].isin(["New", "Repeat"])]
        .groupby(["invoice_month_start", "customer_order_type"], as_index=False)["line_revenue"]
        .sum()
        .rename(columns={"line_revenue": "revenue"})
    )
    top_customers = customer_view.sort_values("monetary_value", ascending=False).head(10)[
        ["customer_id", "primary_country", "orders", "avg_order_value", "monetary_value", "rfm_segment"]
    ]

    row1_col1, row1_col2 = st.columns((1.05, 1.2))
    with row1_col1:
        st.markdown('<div class="chart-title">Customer Count by RFM Segment</div>', unsafe_allow_html=True)
        segment_fig = px.bar(
            segment_bar.sort_values("customers"),
            x="customers",
            y="rfm_segment",
            orientation="h",
            color_discrete_sequence=[COLORS["cyan"]],
            template=template,
        )
        segment_fig.update_layout(xaxis_title="Customers", yaxis_title="")
        st.plotly_chart(segment_fig, use_container_width=True)

    with row1_col2:
        st.markdown('<div class="chart-title">RFM Segment Performance</div>', unsafe_allow_html=True)
        st.dataframe(
            segment_table,
            use_container_width=True,
            hide_index=True,
            column_config={
                "segment_revenue": st.column_config.NumberColumn("Segment Revenue", format="$%.2f"),
                "average_order_value": st.column_config.NumberColumn("Average Order Value", format="$%.2f"),
                "avg_recency_days": st.column_config.NumberColumn("Avg Recency Days", format="%.1f"),
            },
        )

    row2_col1, row2_col2 = st.columns((1.2, 1))
    with row2_col1:
        st.markdown('<div class="chart-title">Monthly Revenue by Customer Order Type</div>', unsafe_allow_html=True)
        stacked_fig = px.bar(
            new_repeat_trend,
            x="invoice_month_start",
            y="revenue",
            color="customer_order_type",
            barmode="stack",
            color_discrete_map={"New": COLORS["amber"], "Repeat": COLORS["pink"]},
            template=template,
        )
        stacked_fig.update_layout(xaxis_title="", yaxis_title="Revenue")
        st.plotly_chart(stacked_fig, use_container_width=True)

    with row2_col2:
        st.markdown('<div class="chart-title">Top Customers by Lifetime Value</div>', unsafe_allow_html=True)
        st.dataframe(
            top_customers,
            use_container_width=True,
            hide_index=True,
            column_config={
                "avg_order_value": st.column_config.NumberColumn("Avg Order Value", format="$%.2f"),
                "monetary_value": st.column_config.NumberColumn("Customer Lifetime Value", format="$%.2f"),
            },
        )


def render_product_performance(filtered_sales: pd.DataFrame, template: str) -> None:
    page_header(
        "Merchandise Performance",
        "Track which products, categories, and quantity leaders create the biggest commercial impact.",
        "Product Performance",
    )

    product_view = filtered_sales.loc[filtered_sales["line_type"] == "Merchandise"].copy()
    products = (
        product_view.groupby(["stock_code", "description", "product_category"], as_index=False)
        .agg(revenue=("line_revenue", "sum"), quantity=("quantity", "sum"), orders=("invoice_no", "nunique"))
        .sort_values("revenue", ascending=False)
    )
    top_revenue = products.head(10)
    top_quantity = products.sort_values("quantity", ascending=False).head(10)
    category_mix = (
        product_view.groupby("product_category", as_index=False)["line_revenue"]
        .sum()
        .rename(columns={"line_revenue": "revenue"})
        .sort_values("revenue", ascending=False)
    )
    scatter = products.head(20)

    row1_col1, row1_col2, row1_col3 = st.columns((1, 1, 1))
    with row1_col1:
        st.markdown('<div class="chart-title">Top 10 Products by Revenue</div>', unsafe_allow_html=True)
        fig = px.bar(
            top_revenue.sort_values("revenue"),
            x="revenue",
            y="description",
            orientation="h",
            color_discrete_sequence=[COLORS["cyan"]],
            template=template,
        )
        fig.update_layout(xaxis_title="Revenue", yaxis_title="")
        st.plotly_chart(fig, use_container_width=True)

    with row1_col2:
        st.markdown('<div class="chart-title">Top 10 Products by Quantity Sold</div>', unsafe_allow_html=True)
        fig = px.bar(
            top_quantity.sort_values("quantity"),
            x="quantity",
            y="description",
            orientation="h",
            color_discrete_sequence=[COLORS["emerald"]],
            template=template,
        )
        fig.update_layout(xaxis_title="Quantity", yaxis_title="")
        st.plotly_chart(fig, use_container_width=True)

    with row1_col3:
        st.markdown('<div class="chart-title">Revenue Contribution by Category</div>', unsafe_allow_html=True)
        fig = px.pie(
            category_mix,
            names="product_category",
            values="revenue",
            hole=0.55,
            template=template,
            color_discrete_sequence=[
                COLORS["blue"],
                COLORS["purple"],
                COLORS["pink"],
                COLORS["cyan"],
                COLORS["amber"],
                COLORS["emerald"],
            ],
        )
        st.plotly_chart(fig, use_container_width=True)

    row2_col1, row2_col2 = st.columns((1.2, 1))
    with row2_col1:
        st.markdown('<div class="chart-title">Revenue vs Quantity for Top 20 Products</div>', unsafe_allow_html=True)
        fig = px.scatter(
            scatter,
            x="quantity",
            y="revenue",
            size="orders",
            color="product_category",
            hover_data=["stock_code", "description"],
            template=template,
            color_discrete_sequence=[COLORS["cyan"], COLORS["purple"], COLORS["pink"], COLORS["emerald"], COLORS["amber"]],
        )
        fig.update_layout(xaxis_title="Quantity Sold", yaxis_title="Merchandise Revenue")
        st.plotly_chart(fig, use_container_width=True)

    with row2_col2:
        st.markdown('<div class="chart-title">Top Product Detail Table</div>', unsafe_allow_html=True)
        st.dataframe(
            top_revenue[["stock_code", "description", "product_category", "quantity", "revenue"]],
            use_container_width=True,
            hide_index=True,
            column_config={
                "quantity": st.column_config.NumberColumn("Quantity", format="%d"),
                "revenue": st.column_config.NumberColumn("Merchandise Revenue", format="$%.2f"),
            },
        )


def render_geographic_analysis(filtered_sales: pd.DataFrame, filtered_customers: pd.DataFrame, template: str) -> None:
    page_header(
        "Geographic Revenue Footprint",
        "See where demand is concentrated and how customer reach changes by country.",
        "Geographic Analysis",
    )

    country_summary = (
        filtered_sales.groupby("country", as_index=False)
        .agg(
            revenue=("line_revenue", "sum"),
            orders=("invoice_no", "nunique"),
            customers=("customer_id", lambda values: values.dropna().nunique()),
            quantity=("quantity", "sum"),
        )
        .sort_values("revenue", ascending=False)
    )
    top_countries = country_summary.head(15)

    country_map = {
        "EIRE": "Ireland",
        "USA": "United States",
        "RSA": "South Africa",
        "Czech Republic": "Czechia",
        "Channel Islands": "Jersey",
    }
    map_df = country_summary.copy()
    map_df["country_display"] = map_df["country"].replace(country_map)
    map_df = map_df.loc[~map_df["country_display"].isin(["Unspecified", "European Community"])]

    row1_col1, row1_col2 = st.columns((1.2, 1))
    with row1_col1:
        st.markdown('<div class="chart-title">Revenue by Country</div>', unsafe_allow_html=True)
        fig = px.bar(
            top_countries.sort_values("revenue"),
            x="revenue",
            y="country",
            orientation="h",
            color="customers",
            color_continuous_scale=[[0, COLORS["blue"]], [1, COLORS["cyan"]]],
            template=template,
        )
        fig.update_layout(xaxis_title="Revenue", yaxis_title="")
        st.plotly_chart(fig, use_container_width=True)

    with row1_col2:
        st.markdown('<div class="chart-title">Customer Distribution by Country</div>', unsafe_allow_html=True)
        fig = px.treemap(
            top_countries.head(12),
            path=[px.Constant("Countries"), "country"],
            values="customers",
            color="revenue",
            color_continuous_scale=[[0, COLORS["purple"]], [1, COLORS["cyan"]]],
            template=template,
        )
        st.plotly_chart(fig, use_container_width=True)

    st.markdown('<div class="chart-title">Global Revenue Map</div>', unsafe_allow_html=True)
    geo = px.choropleth(
        map_df,
        locations="country_display",
        locationmode="country names",
        color="revenue",
        hover_name="country",
        color_continuous_scale=[[0, "#1D4ED8"], [0.5, "#7C3AED"], [1, "#22D3EE"]],
        template=template,
    )
    geo.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        geo=dict(bgcolor="rgba(0,0,0,0)", lakecolor="rgba(0,0,0,0)", showframe=False, projection_type="equirectangular"),
    )
    st.plotly_chart(geo, use_container_width=True)


def render_sales_trend_and_forecasting(filtered_sales: pd.DataFrame, template: str) -> None:
    page_header(
        "Trend, Seasonality & Forecasting",
        "Use recent momentum and seasonal signals to understand what the next quarter might look like.",
        "Sales Trend & Forecasting",
    )

    monthly = (
        filtered_sales.groupby("invoice_month_start", as_index=False)["line_revenue"]
        .sum()
        .rename(columns={"line_revenue": "revenue"})
        .sort_values("invoice_month_start")
    )
    monthly["rolling_3m"] = monthly["revenue"].rolling(3, min_periods=1).mean()
    monthly["month_name"] = monthly["invoice_month_start"].dt.strftime("%b")
    monthly["year"] = monthly["invoice_month_start"].dt.year.astype(str)

    x_idx = np.arange(len(monthly))
    slope, intercept = np.polyfit(x_idx, monthly["revenue"], 1)
    future_idx = np.arange(len(monthly), len(monthly) + 3)
    future_dates = pd.date_range(monthly["invoice_month_start"].max() + pd.offsets.MonthBegin(1), periods=3, freq="MS")
    forecast = pd.DataFrame(
        {
            "invoice_month_start": future_dates,
            "revenue": slope * future_idx + intercept,
            "series": "Forecast",
        }
    )
    actual = monthly[["invoice_month_start", "revenue"]].copy()
    actual["series"] = "Actual"
    forecast_chart = pd.concat([actual, forecast], ignore_index=True)

    row1_col1, row1_col2 = st.columns((1.2, 1))
    with row1_col1:
        st.markdown('<div class="chart-title">Actual Revenue vs 3-Month Forecast</div>', unsafe_allow_html=True)
        fig = px.line(
            forecast_chart,
            x="invoice_month_start",
            y="revenue",
            color="series",
            markers=True,
            color_discrete_map={"Actual": COLORS["cyan"], "Forecast": COLORS["amber"]},
            template=template,
        )
        fig.update_layout(xaxis_title="", yaxis_title="Revenue")
        st.plotly_chart(fig, use_container_width=True)

    with row1_col2:
        st.markdown('<div class="chart-title">Trend Decomposition</div>', unsafe_allow_html=True)
        trend_fig = go.Figure()
        trend_fig.add_trace(go.Scatter(x=monthly["invoice_month_start"], y=monthly["revenue"], name="Actual", line=dict(color=COLORS["pink"], width=3)))
        trend_fig.add_trace(go.Scatter(x=monthly["invoice_month_start"], y=monthly["rolling_3m"], name="3M Rolling Avg", line=dict(color=COLORS["cyan"], width=3)))
        trend_fig.update_layout(template=template, margin=dict(l=16, r=16, t=16, b=16), xaxis_title="", yaxis_title="Revenue")
        st.plotly_chart(trend_fig, use_container_width=True)

    st.markdown('<div class="chart-title">Seasonal Revenue Heatmap</div>', unsafe_allow_html=True)
    heatmap = alt.Chart(monthly).mark_rect(cornerRadius=6).encode(
        x=alt.X("month_name:N", sort=["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], title="Month"),
        y=alt.Y("year:N", title="Year"),
        color=alt.Color("revenue:Q", scale=alt.Scale(range=[COLORS["panel"], COLORS["purple"], COLORS["cyan"]])),
        tooltip=[
            alt.Tooltip("year:N", title="Year"),
            alt.Tooltip("month_name:N", title="Month"),
            alt.Tooltip("revenue:Q", title="Revenue", format=",.2f"),
        ],
    ).properties(height=220)
    st.altair_chart(heatmap, use_container_width=True)


def main() -> None:
    st.set_page_config(page_title=PAGE_TITLE, page_icon=":bar_chart:", layout="wide")
    apply_custom_css()
    template = build_plotly_template()
    assets = load_assets()

    sales = assets["sales"]
    returns = assets["returns"]
    customers = assets["customers"]

    page = st.sidebar.radio(
        "Navigation",
        [
            "Executive Overview",
            "Customer Insights",
            "Product Performance",
            "Geographic Analysis",
            "Sales Trend & Forecasting",
        ],
    )
    filters = build_sidebar_filters(sales, assets["insights_text"])
    filtered_sales = filter_sales(sales, filters)
    filtered_returns = filter_returns(returns, filters)
    filtered_customers = filter_customers(customers, filters)

    filtered_monthly = (
        filtered_sales.groupby(["invoice_month_start", "country", "product_category", "customer_order_type"], as_index=False)
        .agg(revenue=("line_revenue", "sum"), quantity=("quantity", "sum"))
    )
    st.sidebar.download_button(
        "Download filtered monthly data",
        filtered_monthly.to_csv(index=False).encode("utf-8"),
        file_name="filtered_retail_monthly_summary.csv",
        mime="text/csv",
        use_container_width=True,
    )
    st.sidebar.download_button(
        "Download filtered insights",
        build_insight_text(filtered_sales, filtered_returns, filtered_customers),
        file_name="filtered_dashboard_insights.txt",
        mime="text/plain",
        use_container_width=True,
    )

    if filtered_sales.empty:
        st.warning("No sales records match the current filters. Expand the selections in the sidebar to continue.")
        return

    if page == "Executive Overview":
        render_executive_overview(filtered_sales, filtered_returns, template)
    elif page == "Customer Insights":
        render_customer_insights(filtered_sales, filtered_customers, template)
    elif page == "Product Performance":
        render_product_performance(filtered_sales, template)
    elif page == "Geographic Analysis":
        render_geographic_analysis(filtered_sales, filtered_customers, template)
    else:
        render_sales_trend_and_forecasting(filtered_sales, template)


if __name__ == "__main__":
    main()