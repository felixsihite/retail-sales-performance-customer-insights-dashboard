# Power BI Dashboard Specification

## Dashboard goal
Create a stakeholder-ready dashboard that explains sales performance, customer quality, and product mix in a way that supports commercial decisions.

## Recommended pages

### 1. Executive Overview
- KPI cards: `Total Revenue`, `Total Orders`, `Average Order Value`, `Active Customers`, `Return Amount`, `Return Rate %`
- Monthly revenue line chart
- Revenue by country bar chart
- Revenue by product category bar chart
- New vs repeat revenue donut or stacked column chart
- Slicers: date, country, product category, customer order type

### 2. Customer Insights
- RFM segment bar chart
- Matrix of `rfm_segment` by `customers`, `revenue`, `avg_order_value`, `recency_days`
- New vs repeat revenue trend by month
- Top customer table with `customer_id`, `monetary_value`, `orders`, `avg_order_value`, `rfm_segment`
- Slicers: country, RFM segment, date

### 3. Product Performance
- Top 10 products by revenue
- Top 10 products by units sold
- Category revenue contribution
- Scatter plot: `units sold` vs `revenue` by product
- Table: `stock_code`, `description`, `product_category`, `revenue`, `quantity`
- Slicers: product category, country, date

### 4. Returns and Risk Monitoring
- Monthly return amount trend
- Return amount by country
- Return amount by category
- At-risk customer segment summary
- Slicers: date, country, product category

## Required data model

### Fact tables
- `fact_sales.csv`
- `fact_returns.csv`

### Dimension tables
- `dim_date.csv`
- `dim_product.csv`
- `dim_customer_rfm.csv`

## Relationships
- `fact_sales[invoice_date_key]` -> `dim_date[date_key]`
- `fact_returns[invoice_date_key]` -> `dim_date[date_key]`
- `fact_sales[stock_code]` -> `dim_product[stock_code]`
- `fact_sales[customer_id]` -> `dim_customer_rfm[customer_id]`

## Essential slicers
- Date range
- Country
- Product category
- Customer order type
- RFM segment
- Line type

## Visual design tips
- Use a light, executive-friendly theme with muted neutrals and one accent color for revenue.
- Keep the first page to 6-8 visuals maximum.
- Use tooltips to show `revenue`, `orders`, `AOV`, and segment metadata without overcrowding the page.
- Filter product visuals to `line_type = Merchandise` when ranking products.

## What must be shown in Power BI
- Revenue trend by month
- Seasonal or quarter-level pattern
- Top countries and category contribution
- Top products by revenue and quantity
- New vs repeat customer behavior
- RFM customer segmentation
- Return amount or return rate to expose revenue leakage
