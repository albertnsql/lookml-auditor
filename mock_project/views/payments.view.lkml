# payments.view.lkml
# Payment transaction records view.
# INTENTIONAL ISSUES:
#   - count measure has no description
#   - total_amount has no label

view: payments {
  sql_table_name: "public.payments" ;;

  # ── Primary Key ─────────────────────────────────────────────────────────────
  dimension: id {
    type: number
    sql: ${TABLE}.id ;;
    primary_key: yes
    label: "Payment ID"
    description: "Unique identifier for each payment transaction"
  }

  # ── Foreign Keys ─────────────────────────────────────────────────────────────
  dimension: order_id {
    type: number
    sql: ${TABLE}.order_id ;;
    label: "Order ID"
    description: "Foreign key to the associated order"
  }

  dimension: customer_id {
    type: number
    sql: ${TABLE}.customer_id ;;
    label: "Customer ID"
    description: "Foreign key to the paying customer"
    hidden: yes
  }

  # ── Dimensions ───────────────────────────────────────────────────────────────
  dimension: amount {
    type: number
    sql: ${TABLE}.amount ;;
    label: "Payment Amount"
    description: "Amount charged in this payment transaction"
    value_format_name: usd
  }

  dimension: payment_method {
    type: string
    sql: ${TABLE}.method ;;
    label: "Payment Method"
    description: "Method used for payment: credit_card, paypal, bank_transfer, etc."
  }

  dimension: currency {
    type: string
    sql: ${TABLE}.currency ;;
    label: "Currency"
    description: "Currency code for this payment (ISO 4217)"
  }

  dimension: status {
    type: string
    sql: ${TABLE}.status ;;
    label: "Payment Status"
    description: "Current status: pending, completed, failed, refunded"
  }

  dimension: gateway {
    type: string
    sql: ${TABLE}.gateway ;;
    label: "Payment Gateway"
    description: "Payment processor used (Stripe, PayPal, Adyen, etc.)"
  }

  dimension: is_refunded {
    type: yesno
    sql: ${TABLE}.is_refunded ;;
    label: "Is Refunded"
    description: "Whether this payment was subsequently refunded"
  }

  # ── Dimension Groups ─────────────────────────────────────────────────────────
  dimension_group: processed {
    type: time
    timeframes: [raw, date, week, month, quarter, year]
    sql: ${TABLE}.processed_at ;;
    label: "Payment Processed"
    description: "Timestamp when the payment was processed"
    datatype: timestamp
  }

  # ── Measures ─────────────────────────────────────────────────────────────────
  measure: count {
    type: count
    label: "Number of Payments"
    # INTENTIONAL ISSUE: no description on count measure
  }

  # INTENTIONAL ISSUE: no label — defaults to field name
  measure: total_amount {
    type: sum
    sql: ${amount} ;;
    description: "Total amount across all payments"
    value_format_name: usd
  }

  measure: average_payment {
    type: average
    sql: ${amount} ;;
    label: "Average Payment Amount"
    description: "Average transaction value"
    value_format_name: usd
  }

  measure: count_refunded {
    type: count
    filters: [is_refunded: "yes"]
    label: "Refunded Payments"
    description: "Count of payments that have been refunded"
  }

  measure: total_refunded_amount {
    type: sum
    sql: CASE WHEN ${is_refunded} THEN ${amount} ELSE 0 END ;;
    label: "Total Refunded Amount"
    description: "Total value of refunded payments"
    value_format_name: usd
  }
}
