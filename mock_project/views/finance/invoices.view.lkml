# invoices.view.lkml
# Finance invoice records.
# INTENTIONAL ISSUES:
#   - Missing primary key (no primary_key: yes)
#   - Duplicate 'amount' dimension
#   - count_distinct_invoices uses type:sum instead of type:count_distinct
#   - billing_account_id has no label

view: invoices {
  sql_table_name: `finance.invoices` ;;

  # INTENTIONAL ISSUE: no primary_key: yes on any field
  dimension: invoice_id {
    type: string
    sql: ${TABLE}.id ;;
    label: "Invoice ID"
    description: "Unique identifier for the invoice"
    # primary_key: yes  ← intentionally omitted
  }

  dimension: order_id {
    type: string
    sql: ${TABLE}.order_id ;;
    label: "Order ID"
    description: "Order associated with this invoice"
  }

  dimension: billing_account_id {
    type: string
    sql: ${TABLE}.billing_account_id ;;
    # INTENTIONAL ISSUE: no label or description
  }

  dimension: customer_id {
    type: string
    sql: ${TABLE}.customer_id ;;
    label: "Customer ID"
    description: "Customer associated with this invoice"
    hidden: yes
  }

  dimension: amount {
    type: number
    sql: ${TABLE}.amount ;;
    label: "Invoice Amount"
    description: "Total amount on this invoice in the source currency"
    value_format_name: usd
  }

  # INTENTIONAL ISSUE: duplicate dimension name within the same view
  dimension: amount {
    type: number
    sql: ${TABLE}.amount_usd ;;
    label: "Invoice Amount (USD)"
    description: "Invoice amount normalised to USD"
  }

  dimension: currency {
    type: string
    sql: ${TABLE}.currency ;;
    label: "Currency"
    description: "Source currency of the invoice"
  }

  dimension: status {
    type: string
    sql: ${TABLE}.status ;;
    label: "Invoice Status"
    description: "Invoice status: draft, sent, paid, overdue, cancelled"
  }

  dimension: payment_terms {
    type: string
    sql: ${TABLE}.payment_terms ;;
    label: "Payment Terms"
    description: "Net-15, Net-30, Net-60, or immediate"
  }

  dimension: line_items_count {
    type: number
    sql: ${TABLE}.line_items_count ;;
    label: "Line Items"
    description: "Number of line items on the invoice"
  }

  # ── Dimension Groups ─────────────────────────────────────────────────────────
  dimension_group: issued {
    type: time
    timeframes: [raw, date, week, month, quarter, year]
    sql: ${TABLE}.issued_at ;;
    label: "Invoice Issued"
    description: "When the invoice was issued to the customer"
    datatype: timestamp
  }

  dimension_group: due {
    type: time
    timeframes: [raw, date, week, month]
    sql: ${TABLE}.due_at ;;
    label: "Invoice Due"
    description: "When payment is due"
    datatype: timestamp
  }

  dimension_group: paid {
    type: time
    timeframes: [raw, date, week, month]
    sql: ${TABLE}.paid_at ;;
    label: "Invoice Paid"
    description: "When the invoice was paid"
    datatype: timestamp
  }

  # ── Measures ─────────────────────────────────────────────────────────────────
  measure: total_amount {
    type: sum
    sql: ${amount} ;;
    label: "Total Invoice Amount"
    description: "Sum of all invoice amounts"
    value_format_name: usd
  }

  # INTENTIONAL ISSUE: type:sum used instead of type:count_distinct
  measure: count_distinct_invoices {
    type: sum
    sql: ${invoice_id} ;;
    label: "Count of Invoices (broken)"
    description: "Should be count_distinct but uses type:sum — will return wrong results"
  }

  measure: count {
    type: count
    label: "Invoice Count"
    description: "Total number of invoices"
  }

  measure: count_paid {
    type: count
    filters: [status: "paid"]
    label: "Paid Invoice Count"
    description: "Count of invoices that have been paid"
  }

  measure: total_overdue {
    type: sum
    sql: CASE WHEN ${status} = 'overdue' THEN ${amount} ELSE 0 END ;;
    label: "Total Overdue Amount"
    description: "Sum of invoice amounts that are past due"
    value_format_name: usd
  }
}
