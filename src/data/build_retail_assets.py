from __future__ import annotations

import json
import sqlite3
from html import escape
from pathlib import Path

import numpy as np
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[2]
RAW_DATA_PATH = BASE_DIR / "data" / "raw" / "Online_Retail.csv"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
FIGURES_DIR = BASE_DIR / "reports" / "figures"
SQLITE_PATH = PROCESSED_DIR / "online_retail_analytics.db"

NON_MERCH_STOCK_CODES = {
    "AMAZONFEE",
    "B",
    "BANK CHARGES",
    "C2",
    "CRUK",
    "D",
    "DOT",
    "M",
    "PADS",
    "POST",
    "S",
}

CATEGORY_RULES: list[tuple[str, list[str]]] = [
    ("Holiday & Seasonal", ["CHRISTMAS", "XMAS", "EASTER", "HALLOWEEN", "ADVENT", "SANTA", "SNOW"]),
    ("Home Decor & Lighting", ["LANTERN", "LIGHT", "LAMP", "CANDLE", "T-LIGHT", "VOTIVE", "FRAME", "WREATH", "MIRROR", "CLOCK", "HEART", "DOORMAT", "SIGN", "BOARD", "SLATE", "MEMOBOARD", "CHEST", "HOTTIE", "WICKER"]),
    ("Kitchen & Dining", ["MUG", "CUP", "PLATE", "BOWL", "JUG", "GLASS", "TEA", "TEAPOT", "TRAY", "CUTLERY", "SPOON", "FORK", "KNIFE", "NAPKIN", "JAR", "BOTTLE", "CAKESTAND", "CAKE STAND", "JAM MAKING", "BAKING", "POPCORN"]),
    ("Storage & Organization", ["BOX", "TIN", "BASKET", "STORAGE", "ORGANISER", "ORGANIZER", "DRAWER", "HANGER", "HOOK", "CASE", "BAG", "SHOPPER"]),
    ("Stationery & Crafts", ["CARD", "PAPER", "NOTEBOOK", "PENCIL", "PEN", "ENVELOPE", "RIBBON", "WRAP", "WRAPPING", "STAMP", "STICKER", "CRAFT"]),
    ("Party & Gift", ["GIFT", "PARTY", "CELEBRATION", "BABUSHKA", "BUNTING", "DECORATION", "ORNAMENT"]),
    ("Toys & Kids", ["TOY", "DOLL", "BABY", "TEDDY", "KIDS", "CHILD", "PUZZLE", "GAME"]),
    ("Accessories & Fashion", ["JEWELLERY", "NECKLACE", "BRACELET", "RING", "PURSE", "HANDBAG", "WALLET", "UMBRELLA", "SCARF"]),
    ("Garden & Outdoor", ["GARDEN", "OUTDOOR", "BIRD", "PLANT", "FLOWER", "PICNIC", "WATERING", "PARASOL"]),
]


def ensure_directories() -> None:
    for path in (PROCESSED_DIR, FIGURES_DIR):
        path.mkdir(parents=True, exist_ok=True)


def load_raw_data() -> pd.DataFrame:
    df = pd.read_csv(RAW_DATA_PATH, encoding="ISO-8859-1", low_memory=False)
    return df.rename(
        columns={
            "InvoiceNo": "invoice_no",
            "StockCode": "stock_code",
            "Description": "description",
            "Quantity": "quantity",
            "InvoiceDate": "invoice_date",
            "UnitPrice": "unit_price",
            "CustomerID": "customer_id",
            "Country": "country",
        }
    )


def assign_category(stock_code: str, description: str) -> str:
    stock_code = "" if pd.isna(stock_code) else str(stock_code).strip().upper()
    description = "" if pd.isna(description) else str(description).strip().upper()

    if stock_code in NON_MERCH_STOCK_CODES or any(
        keyword in description
        for keyword in ["POSTAGE", "CARRIAGE", "MANUAL", "DISCOUNT", "BANK CHARGES", "AMAZON FEE", "SAMPLES"]
    ):
        return "Fees & Adjustments"

    for category, keywords in CATEGORY_RULES:
        if any(keyword in description for keyword in keywords):
            return category

    return "Miscellaneous"


def clean_transactions(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, int | str]]:
    cleaned = df.copy()

    for column in ["invoice_no", "stock_code", "description", "country"]:
        cleaned[column] = cleaned[column].astype(str).str.strip()
        cleaned.loc[cleaned[column].isin(["", "nan", "None"]), column] = pd.NA

    cleaned["stock_code"] = cleaned["stock_code"].str.upper()

    cleaned["invoice_date"] = pd.to_datetime(cleaned["invoice_date"], format="%m/%d/%y %H:%M")
    cleaned["customer_id"] = pd.to_numeric(cleaned["customer_id"], errors="coerce").astype("Int64")
    cleaned["quantity"] = pd.to_numeric(cleaned["quantity"], errors="coerce")
    cleaned["unit_price"] = pd.to_numeric(cleaned["unit_price"], errors="coerce")

    cleaned["invoice_year"] = cleaned["invoice_date"].dt.year
    cleaned["invoice_month"] = cleaned["invoice_date"].dt.month
    cleaned["invoice_month_name"] = cleaned["invoice_date"].dt.strftime("%b")
    cleaned["invoice_month_start"] = cleaned["invoice_date"].dt.to_period("M").dt.to_timestamp()
    cleaned["invoice_quarter"] = "Q" + cleaned["invoice_date"].dt.quarter.astype(str)
    cleaned["invoice_weekday"] = cleaned["invoice_date"].dt.day_name()
    cleaned["invoice_hour"] = cleaned["invoice_date"].dt.hour
    cleaned["year_month"] = cleaned["invoice_date"].dt.strftime("%Y-%m")

    cleaned["is_cancelled_invoice"] = cleaned["invoice_no"].fillna("").str.startswith("C")
    cleaned["is_return"] = cleaned["is_cancelled_invoice"] | (cleaned["quantity"] < 0)
    cleaned["has_customer_id"] = cleaned["customer_id"].notna()
    cleaned["product_category"] = [
        assign_category(stock_code, description)
        for stock_code, description in zip(cleaned["stock_code"], cleaned["description"], strict=False)
    ]
    cleaned["line_type"] = np.where(cleaned["product_category"] == "Fees & Adjustments", "Non-Merchandise", "Merchandise")
    cleaned["line_revenue"] = cleaned["quantity"] * cleaned["unit_price"]
    cleaned["abs_revenue"] = cleaned["line_revenue"].abs()
    cleaned["abs_quantity"] = cleaned["quantity"].abs()

    quality_report = {
        "raw_rows": int(len(df)),
        "missing_description_rows": int(df["description"].isna().sum()),
        "missing_customer_rows": int(df["customer_id"].isna().sum()),
        "return_rows": int(cleaned["is_return"].sum()),
        "zero_or_negative_price_rows": int((cleaned["unit_price"] <= 0).sum()),
        "countries": int(cleaned["country"].nunique(dropna=True)),
        "date_min": str(cleaned["invoice_date"].min()),
        "date_max": str(cleaned["invoice_date"].max()),
    }

    return cleaned, quality_report


def build_sales_fact(cleaned: pd.DataFrame) -> pd.DataFrame:
    sales = cleaned.loc[
        (~cleaned["is_return"])
        & (cleaned["quantity"] > 0)
        & (cleaned["unit_price"] > 0)
        & cleaned["description"].notna()
    ].copy()

    sales["country_group"] = np.where(sales["country"].eq("United Kingdom"), "United Kingdom", "International")
    return sales


def build_returns_fact(cleaned: pd.DataFrame) -> pd.DataFrame:
    returns = cleaned.loc[cleaned["is_return"] | (cleaned["quantity"] < 0)].copy()
    returns["return_amount"] = returns["abs_revenue"]
    return returns


def build_customer_features(sales: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    customer_sales = sales.loc[sales["customer_id"].notna()].copy()

    first_purchase = customer_sales.groupby("customer_id", as_index=False)["invoice_date"].min().rename(
        columns={"invoice_date": "first_purchase_date"}
    )
    customer_sales = customer_sales.merge(first_purchase, on="customer_id", how="left")
    customer_sales["customer_order_type"] = np.where(
        customer_sales["invoice_month_start"] == customer_sales["first_purchase_date"].dt.to_period("M").dt.to_timestamp(),
        "New",
        "Repeat",
    )

    sales = sales.merge(first_purchase, on="customer_id", how="left")
    sales["customer_order_type"] = np.where(
        sales["customer_id"].isna(),
        "Unknown",
        np.where(
            sales["invoice_month_start"] == sales["first_purchase_date"].dt.to_period("M").dt.to_timestamp(),
            "New",
            "Repeat",
        ),
    )

    snapshot_date = customer_sales["invoice_date"].max() + pd.Timedelta(days=1)
    customer_dim = (
        customer_sales.groupby("customer_id")
        .agg(
            first_purchase_date=("invoice_date", "min"),
            last_purchase_date=("invoice_date", "max"),
            orders=("invoice_no", "nunique"),
            total_units=("quantity", "sum"),
            monetary_value=("line_revenue", "sum"),
            primary_country=("country", lambda values: values.mode().iat[0] if not values.mode().empty else pd.NA),
        )
        .reset_index()
    )
    customer_dim["recency_days"] = (snapshot_date - customer_dim["last_purchase_date"]).dt.days
    customer_dim["tenure_days"] = (snapshot_date - customer_dim["first_purchase_date"]).dt.days
    customer_dim["avg_order_value"] = customer_dim["monetary_value"] / customer_dim["orders"]

    customer_dim["r_score"] = quintile_score(customer_dim["recency_days"], higher_is_better=False)
    customer_dim["f_score"] = quintile_score(customer_dim["orders"], higher_is_better=True)
    customer_dim["m_score"] = quintile_score(customer_dim["monetary_value"], higher_is_better=True)
    customer_dim["rfm_score"] = (
        customer_dim["r_score"].astype(str) + customer_dim["f_score"].astype(str) + customer_dim["m_score"].astype(str)
    )
    customer_dim["rfm_segment"] = customer_dim.apply(segment_customer, axis=1)

    return sales, customer_dim


def quintile_score(series: pd.Series, higher_is_better: bool) -> pd.Series:
    pct_rank = series.rank(method="first", pct=True, ascending=higher_is_better)
    return np.ceil(pct_rank * 5).clip(1, 5).astype(int)


def segment_customer(row: pd.Series) -> str:
    r_score = int(row["r_score"])
    f_score = int(row["f_score"])
    m_score = int(row["m_score"])

    if r_score >= 4 and f_score >= 4 and m_score >= 4:
        return "Champions"
    if r_score >= 3 and f_score >= 4:
        return "Loyal Customers"
    if r_score >= 4 and f_score >= 2 and m_score >= 2:
        return "Potential Loyalists"
    if r_score == 5 and f_score == 1:
        return "New Customers"
    if r_score <= 2 and f_score >= 3 and m_score >= 3:
        return "At Risk"
    if r_score <= 2 and f_score <= 2:
        return "Hibernating"
    if m_score >= 4:
        return "Big Spenders"
    if r_score == 3:
        return "Need Attention"
    return "Promising"


def build_date_dimension(cleaned: pd.DataFrame) -> pd.DataFrame:
    date_range = pd.date_range(cleaned["invoice_date"].min().normalize(), cleaned["invoice_date"].max().normalize(), freq="D")
    date_dim = pd.DataFrame({"date": date_range})
    date_dim["date_key"] = date_dim["date"].dt.strftime("%Y%m%d").astype(int)
    date_dim["year"] = date_dim["date"].dt.year
    date_dim["quarter"] = "Q" + date_dim["date"].dt.quarter.astype(str)
    date_dim["month"] = date_dim["date"].dt.month
    date_dim["month_name"] = date_dim["date"].dt.strftime("%b")
    date_dim["year_month"] = date_dim["date"].dt.strftime("%Y-%m")
    date_dim["week_of_year"] = date_dim["date"].dt.isocalendar().week.astype(int)
    date_dim["weekday_name"] = date_dim["date"].dt.day_name()
    date_dim["is_weekend"] = date_dim["weekday_name"].isin(["Saturday", "Sunday"])
    return date_dim


def build_product_dimension(sales: pd.DataFrame) -> pd.DataFrame:
    product_dim = (
        sales.sort_values("invoice_date")
        .groupby("stock_code")
        .agg(
            description=("description", "first"),
            product_category=("product_category", "first"),
            line_type=("line_type", "first"),
            unit_price=("unit_price", "median"),
        )
        .reset_index()
    )
    return product_dim


def add_date_keys(fact_df: pd.DataFrame) -> pd.DataFrame:
    fact_df = fact_df.copy()
    fact_df["invoice_date_key"] = fact_df["invoice_date"].dt.strftime("%Y%m%d").astype(int)
    fact_df["invoice_date_only"] = fact_df["invoice_date"].dt.normalize()
    return fact_df


def save_outputs(
    cleaned: pd.DataFrame,
    sales: pd.DataFrame,
    returns: pd.DataFrame,
    customer_dim: pd.DataFrame,
    product_dim: pd.DataFrame,
    date_dim: pd.DataFrame,
    quality_report: dict[str, int | str],
) -> dict[str, object]:
    cleaned.to_csv(PROCESSED_DIR / "online_retail_clean.csv", index=False)
    sales.to_csv(PROCESSED_DIR / "fact_sales.csv", index=False)
    returns.to_csv(PROCESSED_DIR / "fact_returns.csv", index=False)
    customer_dim.to_csv(PROCESSED_DIR / "dim_customer_rfm.csv", index=False)
    product_dim.to_csv(PROCESSED_DIR / "dim_product.csv", index=False)
    date_dim.to_csv(PROCESSED_DIR / "dim_date.csv", index=False)

    sales_summary = build_sales_summary(sales, customer_dim, returns)
    sales_summary["data_quality"] = quality_report

    with open(PROCESSED_DIR / "analytics_summary.json", "w", encoding="utf-8") as file_handle:
        json.dump(sales_summary, file_handle, indent=2)

    with open(PROCESSED_DIR / "data_quality_report.json", "w", encoding="utf-8") as file_handle:
        json.dump(quality_report, file_handle, indent=2)

    with sqlite3.connect(SQLITE_PATH) as connection:
        cleaned.to_sql("retail_clean", connection, if_exists="replace", index=False)
        sales.to_sql("fact_sales", connection, if_exists="replace", index=False)
        returns.to_sql("fact_returns", connection, if_exists="replace", index=False)
        customer_dim.to_sql("dim_customer_rfm", connection, if_exists="replace", index=False)
        product_dim.to_sql("dim_product", connection, if_exists="replace", index=False)
        date_dim.to_sql("dim_date", connection, if_exists="replace", index=False)

    create_figures(sales, customer_dim)
    return sales_summary


def build_sales_summary(sales: pd.DataFrame, customer_dim: pd.DataFrame, returns: pd.DataFrame) -> dict[str, object]:
    merchandise_sales = sales.loc[sales["line_type"] == "Merchandise"].copy()
    monthly_revenue = (
        sales.groupby("invoice_month_start", as_index=False)
        .agg(revenue=("line_revenue", "sum"), orders=("invoice_no", "nunique"))
        .sort_values("invoice_month_start")
    )
    monthly_revenue["aov"] = monthly_revenue["revenue"] / monthly_revenue["orders"]

    category_revenue = (
        sales.groupby("product_category", as_index=False)["line_revenue"]
        .sum()
        .sort_values("line_revenue", ascending=False)
    )
    top_products = (
        merchandise_sales.groupby(["stock_code", "description"], as_index=False)
        .agg(revenue=("line_revenue", "sum"), units=("quantity", "sum"))
        .sort_values("revenue", ascending=False)
        .head(10)
    )
    top_countries = (
        sales.groupby("country", as_index=False)["line_revenue"]
        .sum()
        .sort_values("line_revenue", ascending=False)
        .head(10)
    )
    repeat_new = (
        sales.loc[sales["customer_order_type"].isin(["New", "Repeat"])]
        .groupby("customer_order_type", as_index=False)["line_revenue"]
        .sum()
    )
    rfm_distribution = (
        customer_dim.groupby("rfm_segment", as_index=False)
        .agg(customers=("customer_id", "nunique"), revenue=("monetary_value", "sum"))
        .sort_values("revenue", ascending=False)
    )

    peak_month = monthly_revenue.loc[monthly_revenue["revenue"].idxmax()]
    lowest_month = monthly_revenue.loc[monthly_revenue["revenue"].idxmin()]
    average_order_value = sales.groupby("invoice_no")["line_revenue"].sum().mean()

    return {
        "kpis": {
            "total_revenue": round(float(sales["line_revenue"].sum()), 2),
            "total_orders": int(sales["invoice_no"].nunique()),
            "active_customers": int(sales["customer_id"].nunique(dropna=True)),
            "average_order_value": round(float(average_order_value), 2),
            "return_amount": round(float(returns["return_amount"].sum()), 2),
            "return_rows": int(len(returns)),
        },
        "peak_month": {
            "month": str(peak_month["invoice_month_start"].date()),
            "revenue": round(float(peak_month["revenue"]), 2),
        },
        "lowest_month": {
            "month": str(lowest_month["invoice_month_start"].date()),
            "revenue": round(float(lowest_month["revenue"]), 2),
        },
        "top_category": {
            "category": str(category_revenue.iloc[0]["product_category"]),
            "revenue": round(float(category_revenue.iloc[0]["line_revenue"]), 2),
        },
        "top_country": {
            "country": str(top_countries.iloc[0]["country"]),
            "revenue": round(float(top_countries.iloc[0]["line_revenue"]), 2),
        },
        "monthly_revenue": monthly_revenue.assign(
            invoice_month_start=monthly_revenue["invoice_month_start"].dt.strftime("%Y-%m-%d")
        ).to_dict(orient="records"),
        "top_products": top_products.to_dict(orient="records"),
        "top_countries": top_countries.to_dict(orient="records"),
        "category_revenue": category_revenue.to_dict(orient="records"),
        "repeat_vs_new_revenue": repeat_new.to_dict(orient="records"),
        "rfm_distribution": rfm_distribution.to_dict(orient="records"),
    }


def create_figures(sales: pd.DataFrame, customer_dim: pd.DataFrame) -> None:
    monthly_revenue = (
        sales.groupby("invoice_month_start", as_index=False)["line_revenue"].sum().sort_values("invoice_month_start")
    )
    category_revenue = (
        sales.groupby("product_category", as_index=False)["line_revenue"]
        .sum()
        .sort_values("line_revenue", ascending=False)
        .head(8)
    )
    rfm_distribution = (
        customer_dim.groupby("rfm_segment", as_index=False)["customer_id"]
        .nunique()
        .rename(columns={"customer_id": "customers"})
        .sort_values("customers", ascending=False)
    )

    save_line_chart(
        x_values=monthly_revenue["invoice_month_start"].dt.strftime("%Y-%m").tolist(),
        y_values=monthly_revenue["line_revenue"].round(2).tolist(),
        title="Monthly Revenue Trend",
        file_path=FIGURES_DIR / "monthly_revenue_trend.svg",
        y_axis_label="Revenue",
    )
    save_horizontal_bar_chart(
        labels=category_revenue["product_category"].tolist(),
        values=category_revenue["line_revenue"].round(2).tolist(),
        title="Top Product Categories by Revenue",
        file_path=FIGURES_DIR / "top_categories_revenue.svg",
        value_label="Revenue",
        bar_color="#2ca02c",
    )
    save_vertical_bar_chart(
        labels=rfm_distribution["rfm_segment"].tolist(),
        values=rfm_distribution["customers"].tolist(),
        title="Customer Count by RFM Segment",
        file_path=FIGURES_DIR / "rfm_segment_distribution.svg",
        y_axis_label="Customers",
        bar_color="#ff7f0e",
    )


def save_line_chart(
    x_values: list[str],
    y_values: list[float],
    title: str,
    file_path: Path,
    y_axis_label: str,
    line_color: str = "#1f77b4",
) -> None:
    width, height = 960, 460
    left, top, right, bottom = 90, 50, 40, 85
    plot_width = width - left - right
    plot_height = height - top - bottom
    max_y = max(y_values) if y_values else 1
    step_x = plot_width / max(len(x_values) - 1, 1)

    points: list[tuple[float, float]] = []
    for index, value in enumerate(y_values):
        x_pos = left + index * step_x
        y_pos = top + plot_height - (value / max_y * plot_height if max_y else 0)
        points.append((x_pos, y_pos))

    path_points = " ".join(f"{x_pos:.2f},{y_pos:.2f}" for x_pos, y_pos in points)

    x_labels = []
    for index, label in enumerate(x_values):
        if len(x_values) <= 7 or index % 2 == 0 or index == len(x_values) - 1:
            x_pos = left + index * step_x
            x_labels.append(
                f"<text x='{x_pos:.2f}' y='{height - 30}' font-size='12' text-anchor='middle' fill='#444'>{escape(label)}</text>"
            )

    y_ticks = []
    for tick in range(0, 6):
        value = max_y * tick / 5
        y_pos = top + plot_height - (plot_height * tick / 5)
        y_ticks.append(f"<line x1='{left}' y1='{y_pos:.2f}' x2='{width-right}' y2='{y_pos:.2f}' stroke='#e5e7eb' />")
        y_ticks.append(
            f"<text x='{left - 10}' y='{y_pos + 4:.2f}' font-size='12' text-anchor='end' fill='#666'>{format_short_number(value)}</text>"
        )

    circles = "".join(
        f"<circle cx='{x_pos:.2f}' cy='{y_pos:.2f}' r='4' fill='{line_color}' />" for x_pos, y_pos in points
    )

    svg = f"""<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{height}' viewBox='0 0 {width} {height}'>
<rect width='100%' height='100%' fill='white' />
<text x='{width/2:.0f}' y='24' font-size='22' text-anchor='middle' fill='#111827' font-family='Segoe UI'>{escape(title)}</text>
<line x1='{left}' y1='{top + plot_height}' x2='{width-right}' y2='{top + plot_height}' stroke='#9ca3af' />
<line x1='{left}' y1='{top}' x2='{left}' y2='{top + plot_height}' stroke='#9ca3af' />
{''.join(y_ticks)}
<polyline fill='none' stroke='{line_color}' stroke-width='3' points='{path_points}' />
{circles}
{''.join(x_labels)}
<text x='24' y='{top + plot_height / 2:.2f}' font-size='12' transform='rotate(-90 24,{top + plot_height / 2:.2f})' fill='#444'>{escape(y_axis_label)}</text>
</svg>"""
    file_path.write_text(svg, encoding="utf-8")


def save_horizontal_bar_chart(
    labels: list[str],
    values: list[float],
    title: str,
    file_path: Path,
    value_label: str,
    bar_color: str,
) -> None:
    width = 960
    row_height = 42
    height = max(420, 90 + len(labels) * row_height)
    left, top, right, bottom = 220, 55, 80, 40
    plot_width = width - left - right
    max_value = max(values) if values else 1

    bars = []
    for index, (label, value) in enumerate(zip(labels, values, strict=False)):
        y_pos = top + index * row_height
        bar_width = (value / max_value) * plot_width if max_value else 0
        label_text = escape(label[:28] + ("..." if len(label) > 28 else ""))
        bars.append(f"<text x='{left - 10}' y='{y_pos + 18}' font-size='12' text-anchor='end' fill='#444'>{label_text}</text>")
        bars.append(f"<rect x='{left}' y='{y_pos + 3}' width='{bar_width:.2f}' height='20' rx='3' fill='{bar_color}' />")
        bars.append(
            f"<text x='{left + bar_width + 8:.2f}' y='{y_pos + 18}' font-size='12' fill='#444'>{format_short_number(value)}</text>"
        )

    svg = f"""<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{height}' viewBox='0 0 {width} {height}'>
<rect width='100%' height='100%' fill='white' />
<text x='{width/2:.0f}' y='26' font-size='22' text-anchor='middle' fill='#111827' font-family='Segoe UI'>{escape(title)}</text>
<text x='{width-right}' y='{height - 12}' font-size='12' text-anchor='end' fill='#666'>{escape(value_label)}</text>
{''.join(bars)}
</svg>"""
    file_path.write_text(svg, encoding="utf-8")


def save_vertical_bar_chart(
    labels: list[str],
    values: list[float],
    title: str,
    file_path: Path,
    y_axis_label: str,
    bar_color: str,
) -> None:
    width, height = 960, 480
    left, top, right, bottom = 90, 50, 40, 105
    plot_width = width - left - right
    plot_height = height - top - bottom
    max_value = max(values) if values else 1
    bar_width = plot_width / max(len(labels), 1) * 0.7
    gap = plot_width / max(len(labels), 1) * 0.3

    bars = []
    for index, (label, value) in enumerate(zip(labels, values, strict=False)):
        x_pos = left + index * (bar_width + gap) + gap / 2
        bar_height = (value / max_value) * plot_height if max_value else 0
        y_pos = top + plot_height - bar_height
        bars.append(f"<rect x='{x_pos:.2f}' y='{y_pos:.2f}' width='{bar_width:.2f}' height='{bar_height:.2f}' rx='3' fill='{bar_color}' />")
        bars.append(
            f"<text x='{x_pos + bar_width/2:.2f}' y='{height - 50}' font-size='11' text-anchor='end' transform='rotate(-30 {x_pos + bar_width/2:.2f},{height - 50})' fill='#444'>{escape(label)}</text>"
        )
        bars.append(
            f"<text x='{x_pos + bar_width/2:.2f}' y='{y_pos - 8:.2f}' font-size='12' text-anchor='middle' fill='#444'>{int(value)}</text>"
        )

    y_ticks = []
    for tick in range(0, 6):
        value = max_value * tick / 5
        y_pos = top + plot_height - (plot_height * tick / 5)
        y_ticks.append(f"<line x1='{left}' y1='{y_pos:.2f}' x2='{width-right}' y2='{y_pos:.2f}' stroke='#e5e7eb' />")
        y_ticks.append(
            f"<text x='{left - 10}' y='{y_pos + 4:.2f}' font-size='12' text-anchor='end' fill='#666'>{format_short_number(value)}</text>"
        )

    svg = f"""<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{height}' viewBox='0 0 {width} {height}'>
<rect width='100%' height='100%' fill='white' />
<text x='{width/2:.0f}' y='24' font-size='22' text-anchor='middle' fill='#111827' font-family='Segoe UI'>{escape(title)}</text>
<line x1='{left}' y1='{top + plot_height}' x2='{width-right}' y2='{top + plot_height}' stroke='#9ca3af' />
<line x1='{left}' y1='{top}' x2='{left}' y2='{top + plot_height}' stroke='#9ca3af' />
{''.join(y_ticks)}
{''.join(bars)}
<text x='24' y='{top + plot_height / 2:.2f}' font-size='12' transform='rotate(-90 24,{top + plot_height / 2:.2f})' fill='#444'>{escape(y_axis_label)}</text>
</svg>"""
    file_path.write_text(svg, encoding="utf-8")


def format_short_number(value: float) -> str:
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"{value / 1_000:.1f}K"
    return f"{value:.0f}"


def main() -> None:
    ensure_directories()
    raw_df = load_raw_data()
    cleaned_df, quality_report = clean_transactions(raw_df)
    sales_fact = build_sales_fact(cleaned_df)
    returns_fact = build_returns_fact(cleaned_df)
    sales_fact, customer_dim = build_customer_features(sales_fact)
    sales_fact = add_date_keys(sales_fact)
    returns_fact = add_date_keys(returns_fact)
    product_dim = build_product_dimension(sales_fact)
    date_dim = build_date_dimension(cleaned_df)
    summary = save_outputs(cleaned_df, sales_fact, returns_fact, customer_dim, product_dim, date_dim, quality_report)
    print(json.dumps(summary["kpis"], indent=2))


if __name__ == "__main__":
    main()
