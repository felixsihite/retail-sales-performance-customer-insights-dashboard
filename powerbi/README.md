# Power BI Build Notes

This folder contains the prepared assets needed to build the dashboard in Power BI Desktop:

- `../data/processed/fact_sales.csv`
- `../data/processed/fact_returns.csv`
- `../data/processed/dim_date.csv`
- `../data/processed/dim_product.csv`
- `../data/processed/dim_customer_rfm.csv`
- `dax_measures.dax`
- `dashboard_spec.md`
- `Retail_Sales_Performance_Customer_Insights.pbix`

## Import order
1. Load all processed CSV files into Power BI Desktop.
2. Create the model relationships listed in `dashboard_spec.md`.
3. Add the DAX measures from `dax_measures.dax`.
4. Build the four report pages using the recommended visuals.

## Why no `.pbix` binary is committed here
For GitHub portfolios, text-based assets are easier to review and version than a large binary Power BI file. This repository therefore includes:

- Power BI-ready fact and dimension tables
- DAX measures
- Visual requirements
- A reproducible build guide