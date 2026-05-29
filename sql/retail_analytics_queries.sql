-- Retail Sales Performance & Customer Insights Dashboard
-- Target database: SQLite file at data/processed/online_retail_analytics.db

-- 1. Monthly revenue, orders, and average order value
SELECT
    strftime('%Y-%m', invoice_date) AS year_month,
    ROUND(SUM(line_revenue), 2) AS revenue,
    COUNT(DISTINCT invoice_no) AS orders,
    ROUND(SUM(line_revenue) / COUNT(DISTINCT invoice_no), 2) AS average_order_value
FROM fact_sales
GROUP BY 1
ORDER BY 1;

-- 2. Seasonal revenue trend by quarter
SELECT
    invoice_year,
    invoice_quarter,
    ROUND(SUM(line_revenue), 2) AS revenue,
    COUNT(DISTINCT invoice_no) AS orders
FROM fact_sales
GROUP BY 1, 2
ORDER BY 1, 2;

-- 3. Top 10 merchandise products by revenue
SELECT
    stock_code,
    description,
    ROUND(SUM(line_revenue), 2) AS revenue,
    SUM(quantity) AS units_sold
FROM fact_sales
WHERE line_type = 'Merchandise'
GROUP BY stock_code, description
ORDER BY revenue DESC
LIMIT 10;

-- 4. Category revenue mix
SELECT
    product_category,
    ROUND(SUM(line_revenue), 2) AS revenue,
    ROUND(100.0 * SUM(line_revenue) / (SELECT SUM(line_revenue) FROM fact_sales), 2) AS revenue_share_pct
FROM fact_sales
GROUP BY product_category
ORDER BY revenue DESC;

-- 5. Country performance
SELECT
    country,
    ROUND(SUM(line_revenue), 2) AS revenue,
    COUNT(DISTINCT invoice_no) AS orders,
    ROUND(SUM(line_revenue) / COUNT(DISTINCT invoice_no), 2) AS average_order_value
FROM fact_sales
GROUP BY country
ORDER BY revenue DESC
LIMIT 10;

-- 6. New vs repeat customer revenue by month
SELECT
    strftime('%Y-%m', invoice_date) AS year_month,
    customer_order_type,
    ROUND(SUM(line_revenue), 2) AS revenue
FROM fact_sales
WHERE customer_order_type IN ('New', 'Repeat')
GROUP BY 1, 2
ORDER BY 1, 2;

-- 7. RFM segment summary
SELECT
    rfm_segment,
    COUNT(*) AS customers,
    ROUND(SUM(monetary_value), 2) AS revenue,
    ROUND(AVG(avg_order_value), 2) AS average_order_value,
    ROUND(AVG(recency_days), 1) AS avg_recency_days
FROM dim_customer_rfm
GROUP BY rfm_segment
ORDER BY revenue DESC;

-- 8. Monthly return amount
SELECT
    strftime('%Y-%m', invoice_date) AS year_month,
    ROUND(SUM(return_amount), 2) AS return_amount,
    COUNT(DISTINCT invoice_no) AS return_orders
FROM fact_returns
GROUP BY 1
ORDER BY 1;

-- 9. High-value customers for account-management targeting
SELECT
    customer_id,
    primary_country,
    orders,
    ROUND(monetary_value, 2) AS lifetime_revenue,
    ROUND(avg_order_value, 2) AS average_order_value,
    recency_days,
    rfm_segment
FROM dim_customer_rfm
WHERE rfm_segment IN ('Champions', 'Loyal Customers', 'Big Spenders')
ORDER BY lifetime_revenue DESC
LIMIT 25;

-- 10. Customer segment share of known-customer revenue
WITH segment_summary AS (
    SELECT
        rfm_segment,
        SUM(monetary_value) AS revenue
    FROM dim_customer_rfm
    GROUP BY rfm_segment
)
SELECT
    rfm_segment,
    ROUND(revenue, 2) AS revenue,
    ROUND(100.0 * revenue / SUM(revenue) OVER (), 2) AS revenue_share_pct
FROM segment_summary
ORDER BY revenue DESC;