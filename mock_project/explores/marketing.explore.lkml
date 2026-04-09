# marketing.explore.lkml
# Marketing and growth explores.
# Contains intentional LookML issues for auditor testing.

include: "/views/marketing/*.view.lkml"
include: "/views/finance/*.view.lkml"
include: "/views/product/*.view.lkml"
include: "/views/customers.view.lkml"
include: "/views/orders.view.lkml"

# ─────────────────────────────────────────────────────────────────────────────
# EXPLORE: marketing_performance
# Campaign performance with ad spend breakdowns.
# ISSUES: cross join on products (no ON clause), one_to_many on both sides
# ─────────────────────────────────────────────────────────────────────────────
explore: marketing_performance {
  label: "Marketing Performance"
  description: "Campaign-level performance metrics including spend, clicks, and attributed revenue"
  group_label: "Marketing"
  from: campaigns

  join: ad_spend {
    type: left_outer
    relationship: one_to_many
    sql_on: ${marketing_performance.id} = ${ad_spend.campaign_id} ;;
  }

  join: attribution {
    type: left_outer
    relationship: one_to_many
    sql_on: ${marketing_performance.id} = ${attribution.campaign_id} ;;
  }

  join: email_events {
    type: left_outer
    relationship: one_to_many
    sql_on: ${marketing_performance.id} = ${email_events.campaign_id} ;;
  }

  # INTENTIONAL ISSUE: cross join with no ON clause — will fan out
  join: products {
    type: cross
    relationship: many_to_many
  }

  join: customers {
    type: left_outer
    relationship: many_to_one
    sql_on: ${attribution.customer_id} = ${customers.id} ;;
  }
}

# ─────────────────────────────────────────────────────────────────────────────
# EXPLORE: accounting
# Finance accounting explore.
# ISSUES: sql_where used instead of sql_on for join condition
# ─────────────────────────────────────────────────────────────────────────────
explore: accounting {
  label: "Finance Accounting"
  description: "Invoice and billing account reconciliation"
  group_label: "Finance"
  from: invoices

  # INTENTIONAL ISSUE: sql_where used as a join condition instead of sql_on
  join: campaigns {
    type: left_outer
    relationship: many_to_one
    sql_where: ${invoices.amount} > 1000 ;;
  }

  join: billing_accounts {
    type: left_outer
    relationship: many_to_one
    sql_on: ${accounting.billing_account_id} = ${billing_accounts.id} ;;
  }

  join: customers {
    type: left_outer
    # INTENTIONAL ISSUE: incorrect relationship — invoices are many per customer
    relationship: one_to_one
    sql_on: ${accounting.customer_id} = ${customers.id} ;;
  }
}

# ─────────────────────────────────────────────────────────────────────────────
# EXPLORE: email_campaign_analysis
# Email campaign engagement metrics.
# ─────────────────────────────────────────────────────────────────────────────
explore: email_campaign_analysis {
  label: "Email Campaign Analysis"
  description: "Email open, click, and conversion metrics by campaign"
  group_label: "Marketing"
  from: email_events

  join: campaigns {
    type: left_outer
    relationship: many_to_one
    sql_on: ${email_campaign_analysis.campaign_id} = ${campaigns.id} ;;
  }

  join: customers {
    type: left_outer
    relationship: many_to_one
    sql_on: ${email_campaign_analysis.customer_id} = ${customers.id} ;;
  }

  join: orders {
    type: left_outer
    relationship: one_to_many
    sql_on: ${customers.id} = ${orders.customer_id} ;;
  }
}
