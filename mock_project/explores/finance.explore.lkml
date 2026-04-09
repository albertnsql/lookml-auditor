# finance.explore.lkml
# Finance and billing explores.
# Contains intentional LookML issues for auditor testing.

include: "/views/finance/*.view.lkml"
include: "/views/customers.view.lkml"
include: "/views/orders.view.lkml"
include: "/views/payments.view.lkml"

# ─────────────────────────────────────────────────────────────────────────────
# EXPLORE: billing
# Invoice and billing account reconciliation.
# ISSUES: wrong relationship on invoices join (should be one_to_many)
# ─────────────────────────────────────────────────────────────────────────────
explore: billing {
  label: "Billing & Invoices"
  description: "Comprehensive billing explore covering accounts, invoices, and revenue rollups"
  group_label: "Finance"
  from: billing_accounts

  # INTENTIONAL ISSUE: invoices should be one_to_many, declared as many_to_one
  join: invoices {
    type: left_outer
    sql_on: ${billing.id} = ${invoices.billing_account_id} ;;
    relationship: many_to_one
  }

  join: revenue_rollup {
    type: left_outer
    sql_on: ${billing.id} = ${revenue_rollup.billing_account_id} ;;
    relationship: one_to_one
  }

  join: customers {
    type: left_outer
    sql_on: ${billing.customer_id} = ${customers.id} ;;
    relationship: many_to_one
  }

  join: payments {
    type: left_outer
    sql_on: ${invoices.invoice_id} = ${payments.order_id} ;;
    # INTENTIONAL ISSUE: joining on mismatched column types (invoice_id vs order_id)
    relationship: one_to_many
  }
}

# ─────────────────────────────────────────────────────────────────────────────
# EXPLORE: revenue_analysis
# Aggregated revenue reporting explore.
# ─────────────────────────────────────────────────────────────────────────────
explore: revenue_analysis {
  label: "Revenue Analysis"
  description: "Rolled-up revenue metrics across billing accounts and time periods"
  group_label: "Finance"
  from: revenue_rollup

  join: billing_accounts {
    type: left_outer
    sql_on: ${revenue_analysis.billing_account_id} = ${billing_accounts.id} ;;
    relationship: many_to_one
  }

  join: customers {
    type: left_outer
    sql_on: ${billing_accounts.customer_id} = ${customers.id} ;;
    relationship: many_to_one
  }

  join: orders {
    type: left_outer
    sql_on: ${customers.id} = ${orders.customer_id} ;;
    # INTENTIONAL ISSUE: chained join causes fanout with revenue metrics
    relationship: one_to_many
  }
}
