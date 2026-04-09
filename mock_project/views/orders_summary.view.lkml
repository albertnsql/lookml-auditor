# orders_summary.view.lkml
# Persistent Derived Table summarising lifetime order metrics per customer.
# INTENTIONAL ISSUES:
#   - order_count measure uses type:sum instead of type:count (semantically wrong)
#   - total_spent has no label or description

view: orders_summary {
  derived_table: {
    datagroup_trigger: daily_refresh
    sql:
      SELECT
        o.customer_id                                   AS customer_id,
        COUNT(o.id)                                     AS order_count,
        SUM(o.amount)                                   AS total_spent,
        AVG(o.amount)                                   AS avg_order_value,
        MIN(o.created_at)                               AS first_order_at,
        MAX(o.created_at)                               AS last_order_at,
        COUNT(DISTINCT o.region)                        AS distinct_regions,
        SUM(CASE WHEN o.is_returned THEN 1 ELSE 0 END)  AS return_count,
        MAX(o.status)                                   AS last_status
      FROM public.orders o
      WHERE o.created_at >= DATEADD(year, -3, CURRENT_DATE)
      GROUP BY 1
    ;;
  }

  # ── Primary Key ─────────────────────────────────────────────────────────────
  dimension: customer_id {
    type: number
    sql: ${TABLE}.customer_id ;;
    primary_key: yes
    label: "Customer ID"
    description: "Customer identifier — aggregation key for this summary PDT"
  }

  # ── Dimensions ───────────────────────────────────────────────────────────────
  dimension: last_status {
    type: string
    sql: ${TABLE}.last_status ;;
    label: "Last Order Status"
    description: "Status of the customer's most recent order"
  }

  dimension_group: first_order {
    type: time
    timeframes: [raw, date, week, month, year]
    sql: ${TABLE}.first_order_at ;;
    label: "First Order"
    description: "Date of the customer's first ever order"
    datatype: timestamp
  }

  dimension_group: last_order {
    type: time
    timeframes: [raw, date, week, month, year]
    sql: ${TABLE}.last_order_at ;;
    label: "Last Order"
    description: "Date of the customer's most recent order"
    datatype: timestamp
  }

  dimension: distinct_regions {
    type: number
    sql: ${TABLE}.distinct_regions ;;
    label: "Distinct Regions Ordered From"
    description: "Number of distinct regions from which the customer has ordered"
  }

  # ── Measures ─────────────────────────────────────────────────────────────────
  # INTENTIONAL ISSUE: type:sum used for a pre-aggregated COUNT field
  # This double-counts when multiple rows exist (though PDT is keyed by customer_id)
  measure: order_count {
    type: sum
    sql: ${TABLE}.order_count ;;
    label: "Order Count"
    description: "Number of orders per customer — NOTE: uses type:sum instead of type:number"
  }

  # INTENTIONAL ISSUE: no label or description
  measure: total_spent {
    type: sum
    sql: ${TABLE}.total_spent ;;
  }

  measure: avg_order_value {
    type: average
    sql: ${TABLE}.avg_order_value ;;
    label: "Average Order Value"
    description: "Average order value calculated in the derived table"
    value_format_name: usd
  }

  measure: total_returns {
    type: sum
    sql: ${TABLE}.return_count ;;
    label: "Total Returns"
    description: "Total number of returned orders per customer"
  }
}
