# customer_lifetime_value.view.lkml
# Complex PDT calculating customer lifetime value metrics.
# Uses datagroup_trigger for daily persistence.
# This is an example of a well-formed production PDT.

view: customer_lifetime_value {
  derived_table: {
    datagroup_trigger: daily_refresh
    sql:
      WITH order_stats AS (
        SELECT
          o.customer_id,
          COUNT(DISTINCT o.id)                                           AS order_count,
          SUM(oi.sale_price)                                             AS total_revenue,
          AVG(oi.sale_price)                                             AS avg_order_value,
          MIN(o.created_at)                                              AS first_order_at,
          MAX(o.created_at)                                              AS last_order_at,
          DATEDIFF(day, MIN(o.created_at), MAX(o.created_at))           AS customer_age_days,
          COUNT(DISTINCT DATE_TRUNC('month', o.created_at))              AS active_months
        FROM public.orders o
        LEFT JOIN public.order_items oi
          ON o.id = oi.order_id
        WHERE o.status NOT IN ('cancelled', 'fraud')
        GROUP BY 1
      ),
      refund_stats AS (
        SELECT
          r.customer_id,
          SUM(r.amount)                                                   AS total_refunded,
          COUNT(r.id)                                                     AS refund_count
        FROM public.refunds r
        GROUP BY 1
      )
      SELECT
        os.customer_id,
        os.order_count,
        os.total_revenue,
        COALESCE(rs.total_refunded, 0)                                   AS total_refunded,
        os.total_revenue - COALESCE(rs.total_refunded, 0)                AS net_revenue,
        os.avg_order_value,
        os.first_order_at,
        os.last_order_at,
        os.customer_age_days,
        os.active_months,
        COALESCE(rs.refund_count, 0)                                     AS refund_count,
        CASE
          WHEN os.total_revenue >= 5000  THEN 'Platinum'
          WHEN os.total_revenue >= 2000  THEN 'Gold'
          WHEN os.total_revenue >= 500   THEN 'Silver'
          ELSE 'Bronze'
        END                                                              AS value_segment
      FROM order_stats os
      LEFT JOIN refund_stats rs
        ON os.customer_id = rs.customer_id
    ;;
  }

  # ── Primary Key ─────────────────────────────────────────────────────────────
  dimension: customer_id {
    type: number
    sql: ${TABLE}.customer_id ;;
    primary_key: yes
    label: "Customer ID"
    description: "Customer identifier — one row per customer in this PDT"
  }

  # ── Dimensions ───────────────────────────────────────────────────────────────
  dimension: value_segment {
    type: string
    sql: ${TABLE}.value_segment ;;
    label: "Value Segment"
    description: "Customer segment based on net revenue: Bronze / Silver / Gold / Platinum"
  }

  dimension: customer_age_days {
    type: number
    sql: ${TABLE}.customer_age_days ;;
    label: "Customer Age (days)"
    description: "Days between first and last order"
  }

  dimension: active_months {
    type: number
    sql: ${TABLE}.active_months ;;
    label: "Active Months"
    description: "Number of distinct months with at least one order"
  }

  dimension_group: first_order {
    type: time
    timeframes: [raw, date, month, year]
    sql: ${TABLE}.first_order_at ;;
    label: "First Order"
    description: "Date of the customer's first order"
    datatype: timestamp
  }

  dimension_group: last_order {
    type: time
    timeframes: [raw, date, month, year]
    sql: ${TABLE}.last_order_at ;;
    label: "Last Order"
    description: "Date of the customer's most recent order"
    datatype: timestamp
  }

  # ── Measures ─────────────────────────────────────────────────────────────────
  measure: total_net_revenue {
    type: sum
    sql: ${TABLE}.net_revenue ;;
    label: "Total Net Revenue"
    description: "Sum of revenue minus refunds across all customers"
    value_format_name: usd
  }

  measure: avg_net_revenue_per_customer {
    type: average
    sql: ${TABLE}.net_revenue ;;
    label: "Avg Net Revenue per Customer"
    description: "Average net revenue per customer"
    value_format_name: usd
  }

  measure: total_refunded {
    type: sum
    sql: ${TABLE}.total_refunded ;;
    label: "Total Refunded"
    description: "Total refund amounts across all customers"
    value_format_name: usd
  }

  measure: avg_order_count {
    type: average
    sql: ${TABLE}.order_count ;;
    label: "Avg Orders per Customer"
    description: "Average number of orders per customer"
    value_format_name: decimal_1
  }

  measure: count_platinum {
    type: count
    filters: [value_segment: "Platinum"]
    label: "Platinum Customers"
    description: "Count of customers in the Platinum value tier"
  }

  measure: count_customers {
    type: count
    label: "Total Customers"
    description: "Count of customers with at least one order"
  }
}
