# refunds.view.lkml
# Refund transaction records.
# INTENTIONAL ISSUES:
#   - total_refunded measure has no label
#   - refund_rate measure is a calculated field that can be misleading

view: refunds {
  sql_table_name: "public.refunds" ;;

  # ── Primary Key ─────────────────────────────────────────────────────────────
  dimension: id {
    type: number
    sql: ${TABLE}.id ;;
    primary_key: yes
    label: "Refund ID"
    description: "Unique identifier for each refund transaction"
  }

  # ── Foreign Keys ─────────────────────────────────────────────────────────────
  dimension: order_id {
    type: number
    sql: ${TABLE}.order_id ;;
    label: "Order ID"
    description: "Order that was refunded"
  }

  dimension: customer_id {
    type: number
    sql: ${TABLE}.customer_id ;;
    label: "Customer ID"
    description: "Customer who received the refund"
    hidden: yes
  }

  dimension: payment_id {
    type: number
    sql: ${TABLE}.payment_id ;;
    label: "Payment ID"
    description: "Original payment being refunded"
    hidden: yes
  }

  # ── Dimensions ───────────────────────────────────────────────────────────────
  dimension: amount {
    type: number
    sql: ${TABLE}.amount ;;
    label: "Refund Amount"
    description: "Amount refunded to the customer"
    value_format_name: usd
  }

  dimension: reason {
    type: string
    sql: ${TABLE}.reason ;;
    label: "Refund Reason"
    description: "Categorised reason for the refund: defective, wrong_item, not_as_described, other"
  }

  dimension: status {
    type: string
    sql: ${TABLE}.status ;;
    label: "Refund Status"
    description: "Processing status: pending, processed, denied"
  }

  dimension: is_full_refund {
    type: yesno
    sql: ${TABLE}.is_full_refund ;;
    label: "Is Full Refund"
    description: "Whether the entire order amount was refunded"
  }

  # ── Dimension Groups ─────────────────────────────────────────────────────────
  dimension_group: created {
    type: time
    timeframes: [raw, date, week, month, quarter, year]
    sql: ${TABLE}.created_at ;;
    label: "Refund Requested"
    description: "Timestamp when the refund was requested"
    datatype: timestamp
  }

  dimension_group: processed {
    type: time
    timeframes: [raw, date, week, month]
    sql: ${TABLE}.processed_at ;;
    label: "Refund Processed"
    description: "Timestamp when the refund was completed"
    datatype: timestamp
  }

  # ── Measures ─────────────────────────────────────────────────────────────────
  measure: count {
    type: count
    label: "Number of Refunds"
    description: "Total count of refund transactions"
  }

  # INTENTIONAL ISSUE: no label — defaults to field name "total_refunded"
  measure: total_refunded {
    type: sum
    sql: ${amount} ;;
    description: "Total dollar amount refunded to customers"
    value_format_name: usd
  }

  measure: count_full_refunds {
    type: count
    filters: [is_full_refund: "yes"]
    label: "Full Refund Count"
    description: "Count of orders that received a complete refund"
  }

  measure: avg_refund_amount {
    type: average
    sql: ${amount} ;;
    label: "Average Refund Amount"
    description: "Average value of refund transactions"
    value_format_name: usd
  }
}
