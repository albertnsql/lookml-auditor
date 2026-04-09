# revenue_rollup.view.lkml
# Aggregated revenue PDT — rolls up invoice and payment data by billing account and month.
# Uses persist_for for simplicity (no sql_trigger — intentional anti-pattern documented below).
# INTENTIONAL ISSUES:
#   - persist_for without sql_trigger — may serve stale data silently

view: revenue_rollup {
  derived_table: {
    # INTENTIONAL ISSUE: persist_for without a sql_trigger — no guarantee of freshness
    persist_for: "24 hours"
    sql:
      SELECT
        i.billing_account_id,
        DATE_TRUNC('month', i.issued_at)                                    AS revenue_month,
        COUNT(DISTINCT i.id)                                                AS invoice_count,
        SUM(i.amount_usd)                                                   AS gross_revenue,
        SUM(CASE WHEN i.status = 'paid'    THEN i.amount_usd ELSE 0 END)   AS paid_revenue,
        SUM(CASE WHEN i.status = 'overdue' THEN i.amount_usd ELSE 0 END)   AS overdue_revenue,
        COUNT(DISTINCT CASE WHEN i.status = 'paid' THEN i.id END)          AS paid_invoice_count,
        AVG(i.amount_usd)                                                   AS avg_invoice_amount,
        MAX(i.issued_at)                                                    AS last_invoice_at
      FROM finance.invoices i
      WHERE i.issued_at >= DATEADD(year, -2, CURRENT_DATE)
      GROUP BY 1, 2
    ;;
  }

  # ── Primary Key ─────────────────────────────────────────────────────────────
  # INTENTIONAL ISSUE: composite key not declared — could cause join issues
  dimension: billing_account_id {
    type: string
    sql: ${TABLE}.billing_account_id ;;
    label: "Billing Account ID"
    description: "Billing account for this revenue record"
    # primary_key: yes on a composite key requires a concat trick — not done here
  }

  dimension_group: revenue_month {
    type: time
    timeframes: [raw, month, quarter, year]
    sql: ${TABLE}.revenue_month ;;
    label: "Revenue Month"
    description: "Month for this revenue rollup row"
    datatype: timestamp
  }

  # ── Measures ─────────────────────────────────────────────────────────────────
  measure: total_gross_revenue {
    type: sum
    sql: ${TABLE}.gross_revenue ;;
    label: "Gross Revenue"
    description: "Total invoiced amount across all statuses"
    value_format_name: usd
  }

  measure: total_paid_revenue {
    type: sum
    sql: ${TABLE}.paid_revenue ;;
    label: "Paid Revenue"
    description: "Total amount from paid invoices"
    value_format_name: usd
  }

  measure: total_overdue_revenue {
    type: sum
    sql: ${TABLE}.overdue_revenue ;;
    label: "Overdue Revenue"
    description: "Total amount from overdue invoices"
    value_format_name: usd
  }

  measure: total_invoice_count {
    type: sum
    sql: ${TABLE}.invoice_count ;;
    label: "Total Invoice Count"
    description: "Sum of invoice count across rollup rows — use with caution (pre-aggregated)"
  }

  measure: avg_invoice_amount {
    type: average
    sql: ${TABLE}.avg_invoice_amount ;;
    label: "Avg Invoice Amount"
    description: "Average invoice value across rollup rows"
    value_format_name: usd
  }

  measure: payment_rate {
    type: number
    sql: ${total_paid_revenue} / NULLIF(${total_gross_revenue}, 0) ;;
    label: "Payment Rate"
    description: "Fraction of invoiced revenue that has been collected"
    value_format_name: percent_2
  }
}
