# orders.view.lkml
# Core order transactional view.
# INTENTIONAL ISSUES:
#   - Duplicate 'status' dimension
#   - average_order_value measure type is wrong (averaging a string field)
#   - Several fields missing label/description
#   - parameter with no allowed_values

view: orders {
  sql_table_name: "public.orders" ;;

  # ── Primary Key ─────────────────────────────────────────────────────────────
  dimension: id {
    type: number
    sql: ${TABLE}.id ;;
    primary_key: yes
    label: "Order ID"
    description: "Unique identifier for each order"
    tags: ["key", "transactional"]
  }

  # ── Foreign Keys ─────────────────────────────────────────────────────────────
  dimension: customer_id {
    type: number
    sql: ${TABLE}.customer_id ;;
    # INTENTIONAL ISSUE: no label or description on a foreign key
  }

  # ── Dimensions ───────────────────────────────────────────────────────────────
  dimension: status {
    type: string
    sql: ${TABLE}.status ;;
    label: "Order Status"
    description: "Current fulfillment status of the order"
    # No allowed_values constraint or case expression
  }

  # INTENTIONAL ISSUE: duplicate dimension name within the same view
  dimension: status {
    type: string
    sql: ${TABLE}.order_status ;;
    # This conflicts with the status dimension above
  }

  dimension: source {
    type: string
    sql: ${TABLE}.source ;;
    label: "Order Source"
    description: "Channel through which the order was placed (web, app, phone)"
  }

  dimension: region {
    type: string
    sql: ${TABLE}.region ;;
    label: "Region"
    # INTENTIONAL ISSUE: no description
  }

  dimension: is_returned {
    type: yesno
    sql: ${TABLE}.is_returned ;;
    label: "Is Returned"
    description: "Flag indicating whether any items in the order were returned"
  }

  dimension: shipping_method {
    type: string
    sql: ${TABLE}.shipping_method ;;
    label: "Shipping Method"
    description: "Shipping carrier and service level used for the order"
  }

  dimension: billing_account_id {
    type: number
    sql: ${TABLE}.billing_account_id ;;
    label: "Billing Account ID"
    hidden: yes
  }

  # ── Dimension Groups ─────────────────────────────────────────────────────────
  dimension_group: created {
    type: time
    timeframes: [raw, time, date, week, month, quarter, year, fiscal_quarter, fiscal_year]
    sql: ${TABLE}.created_at ;;
    label: "Order Created"
    description: "Timestamp when the order was created"
    datatype: timestamp
  }

  dimension_group: shipped {
    type: time
    timeframes: [raw, date, week, month, quarter, year]
    sql: ${TABLE}.shipped_at ;;
    label: "Order Shipped"
    description: "Timestamp when the order was shipped to the customer"
    datatype: timestamp
  }

  dimension_group: completed {
    type: time
    timeframes: [raw, date, week, month, year]
    sql: ${TABLE}.completed_at ;;
    label: "Order Completed"
    description: "Timestamp when the order was marked complete"
    datatype: timestamp
  }

  # ── Parameters ───────────────────────────────────────────────────────────────
  # INTENTIONAL ISSUE: parameter with no allowed_values — allows arbitrary user input
  parameter: status_filter {
    type: string
    label: "Status Filter"
    description: "Filter orders by status — note: no allowed_values constraint"
  }

  parameter: date_granularity {
    type: unquoted
    label: "Date Granularity"
    description: "Select the time granularity for date grouping"
    allowed_value: { label: "Day" value: "date" }
    allowed_value: { label: "Week" value: "week" }
    allowed_value: { label: "Month" value: "month" }
    allowed_value: { label: "Quarter" value: "quarter" }
    allowed_value: { label: "Year" value: "year" }
    default_value: "month"
  }

  # ── Measures ─────────────────────────────────────────────────────────────────
  measure: count {
    type: count
    label: "Number of Orders"
    description: "Total count of orders"
    drill_fields: [id, customer_id, status, created_date]
  }

  measure: total_amount {
    type: sum
    sql: ${TABLE}.amount ;;
    label: "Total Order Amount"
    description: "Sum of all order amounts"
    value_format_name: usd
  }

  measure: average_order_value {
    type: average
    sql: ${TABLE}.amount ;;
    label: "Average Order Value"
    description: "Average order amount"
    value_format_name: usd
  }

  # INTENTIONAL ISSUE: type:average applied to status (a string field) — nonsensical
  measure: average_status {
    type: average
    sql: ${TABLE}.status ;;
    label: "Average Status"
    # This measure is semantically incorrect
  }

  measure: total_returned_amount {
    type: sum
    sql: CASE WHEN ${is_returned} THEN ${TABLE}.amount ELSE 0 END ;;
    label: "Total Returned Amount"
    description: "Total value of returned orders"
    value_format_name: usd
  }

  # INTENTIONAL ISSUE: measure with no label or description
  measure: count_distinct_customers {
    type: count_distinct
    sql: ${customer_id} ;;
  }

  # ── Sets ─────────────────────────────────────────────────────────────────────
  set: order_fields {
    fields: [
      id,
      customer_id,
      status,
      source,
      region,
      created_date,
      shipped_date,
      total_amount,
      count
    ]
  }

  set: order_export_fields {
    fields: [
      id,
      customer_id,
      status,
      created_date,
      shipped_date,
      total_amount
    ]
  }
}
