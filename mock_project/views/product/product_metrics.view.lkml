# product_metrics.view.lkml
# Aggregated product performance metrics PDT.
# Rolls up sales, returns, and inventory data per product.
# INTENTIONAL ISSUES:
#   - persist_for without sql_trigger (same anti-pattern as revenue_rollup)
#   - sell_through_rate can be >1 due to returns not being excluded

view: product_metrics {
  derived_table: {
    # INTENTIONAL ISSUE: persist_for only — no sql_trigger for freshness guarantee
    persist_for: "12 hours"
    sql:
      WITH sales AS (
        SELECT
          oi.product_id,
          COUNT(DISTINCT oi.id)                          AS units_sold,
          SUM(oi.sale_price)                             AS gross_revenue,
          SUM(oi.discount_amount)                        AS total_discounts,
          COUNT(DISTINCT oi.order_id)                    AS orders_containing,
          AVG(oi.sale_price)                             AS avg_selling_price
        FROM public.order_items oi
        WHERE oi.created_at >= DATEADD(day, -90, CURRENT_DATE)
        GROUP BY 1
      ),
      returns AS (
        SELECT
          r.product_id,
          COUNT(r.return_id)                             AS units_returned,
          SUM(rf.amount)                                 AS total_refunded
        FROM public.returns r
        LEFT JOIN public.refunds rf
          ON r.order_id = rf.order_id
        GROUP BY 1
      ),
      inventory AS (
        SELECT
          ii.product_id,
          SUM(ii.quantity_on_hand)                       AS total_stock,
          AVG(ii.cost)                                   AS avg_cost
        FROM product.inventory_items ii
        GROUP BY 1
      )
      SELECT
        p.id                                             AS product_id,
        p.name                                           AS product_name,
        p.category,
        p.brand,
        COALESCE(s.units_sold, 0)                        AS units_sold,
        COALESCE(s.gross_revenue, 0)                     AS gross_revenue,
        COALESCE(s.total_discounts, 0)                   AS total_discounts,
        COALESCE(s.orders_containing, 0)                 AS orders_containing,
        COALESCE(s.avg_selling_price, 0)                 AS avg_selling_price,
        COALESCE(r.units_returned, 0)                    AS units_returned,
        COALESCE(r.total_refunded, 0)                    AS total_refunded,
        COALESCE(i.total_stock, 0)                       AS total_stock,
        COALESCE(i.avg_cost, 0)                          AS avg_cost,
        -- Margin: avg_selling_price minus avg_cost
        COALESCE(s.avg_selling_price, 0)
          - COALESCE(i.avg_cost, 0)                      AS unit_margin,
        -- Sell-through: units_sold / (units_sold + total_stock)
        -- INTENTIONAL ISSUE: can exceed 1 if returns not excluded from denominator
        CASE
          WHEN COALESCE(s.units_sold, 0) + COALESCE(i.total_stock, 0) = 0 THEN 0
          ELSE COALESCE(s.units_sold, 0) * 1.0
               / (COALESCE(s.units_sold, 0) + COALESCE(i.total_stock, 0))
        END                                              AS sell_through_rate
      FROM product.products p
      LEFT JOIN sales s    ON p.id = s.product_id
      LEFT JOIN returns r  ON p.id = r.product_id
      LEFT JOIN inventory i ON p.id = i.product_id
    ;;
  }

  # ── Primary Key ─────────────────────────────────────────────────────────────
  dimension: product_id {
    primary_key: yes
    type: number
    sql: ${TABLE}.product_id ;;
    label: "Product ID"
    description: "Product identifier — one row per product in this PDT"
  }

  # ── Dimensions ───────────────────────────────────────────────────────────────
  dimension: product_name {
    type: string
    sql: ${TABLE}.product_name ;;
    label: "Product Name"
    description: "Name of the product from the catalog"
  }

  dimension: category {
    type: string
    sql: ${TABLE}.category ;;
    label: "Category"
    description: "Product category"
  }

  dimension: brand {
    type: string
    sql: ${TABLE}.brand ;;
    label: "Brand"
    description: "Product brand"
  }

  dimension: unit_margin {
    type: number
    sql: ${TABLE}.unit_margin ;;
    label: "Unit Margin"
    description: "Difference between average selling price and average cost"
    value_format_name: usd
  }

  dimension: sell_through_rate_dim {
    type: number
    sql: ${TABLE}.sell_through_rate ;;
    label: "Sell-Through Rate"
    description: "Fraction of inventory sold (units_sold / units_sold + stock) — may exceed 1 due to return handling"
    value_format_name: percent_2
  }

  dimension: total_stock {
    type: number
    sql: ${TABLE}.total_stock ;;
    label: "Total Stock"
    description: "Units currently in inventory across all warehouses"
  }

  # ── Measures ─────────────────────────────────────────────────────────────────
  measure: total_units_sold {
    type: sum
    sql: ${TABLE}.units_sold ;;
    label: "Total Units Sold"
    description: "Sum of units sold across all products (last 90 days)"
  }

  measure: total_gross_revenue {
    type: sum
    sql: ${TABLE}.gross_revenue ;;
    label: "Gross Revenue (90d)"
    description: "Total revenue from product sales in the last 90 days"
    value_format_name: usd
  }

  measure: total_discounts {
    type: sum
    sql: ${TABLE}.total_discounts ;;
    label: "Total Discounts Given"
    description: "Sum of all discounts applied to products"
    value_format_name: usd
  }

  measure: total_units_returned {
    type: sum
    sql: ${TABLE}.units_returned ;;
    label: "Total Units Returned"
    description: "Sum of units returned across all products"
  }

  measure: avg_unit_margin {
    type: average
    sql: ${TABLE}.unit_margin ;;
    label: "Avg Unit Margin"
    description: "Mean margin per product"
    value_format_name: usd
  }

  measure: avg_sell_through {
    type: average
    sql: ${TABLE}.sell_through_rate ;;
    label: "Avg Sell-Through Rate"
    description: "Mean sell-through rate across products"
    value_format_name: percent_2
  }

  measure: count_products {
    type: count
    label: "Products in Metrics"
    description: "Count of products included in this metrics PDT"
  }
}
