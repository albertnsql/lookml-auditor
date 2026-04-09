# billing_accounts.view.lkml
# Billing account records — links customers to their billing configuration.

view: billing_accounts {
  sql_table_name: `finance.billing_accounts` ;;

  # ── Primary Key ─────────────────────────────────────────────────────────────
  dimension: id {
    type: string
    sql: ${TABLE}.id ;;
    primary_key: yes
    label: "Billing Account ID"
    description: "Unique identifier for the billing account"
  }

  # ── Foreign Keys ─────────────────────────────────────────────────────────────
  dimension: customer_id {
    type: string
    sql: ${TABLE}.customer_id ;;
    label: "Customer ID"
    description: "Customer linked to this billing account"
    hidden: yes
  }

  # ── Dimensions ───────────────────────────────────────────────────────────────
  dimension: account_name {
    type: string
    sql: ${TABLE}.account_name ;;
    label: "Billing Account Name"
    description: "Friendly name for the billing account"
  }

  dimension: billing_email {
    type: string
    sql: ${TABLE}.billing_email ;;
    label: "Billing Email"
    description: "Email address for invoice delivery — PII"
    tags: ["pii"]
  }

  dimension: plan_type {
    type: string
    sql: ${TABLE}.plan_type ;;
    label: "Plan Type"
    description: "Subscription plan: monthly, annual, enterprise"
  }

  dimension: payment_method {
    type: string
    sql: ${TABLE}.payment_method ;;
    label: "Payment Method"
    description: "Default payment method: credit_card, bank_transfer, invoice"
  }

  dimension: currency {
    type: string
    sql: ${TABLE}.currency ;;
    label: "Billing Currency"
    description: "Currency for invoicing (ISO 4217)"
  }

  dimension: is_tax_exempt {
    type: yesno
    sql: ${TABLE}.is_tax_exempt ;;
    label: "Is Tax Exempt"
    description: "Whether the account is exempt from sales tax"
  }

  dimension: credit_limit {
    type: number
    sql: ${TABLE}.credit_limit ;;
    label: "Credit Limit"
    description: "Maximum outstanding balance allowed for this account"
    value_format_name: usd
  }

  dimension: country {
    type: string
    sql: ${TABLE}.country ;;
    label: "Billing Country"
    description: "Country of the billing address"
  }

  # ── Dimension Groups ─────────────────────────────────────────────────────────
  dimension_group: created {
    type: time
    timeframes: [raw, date, week, month, quarter, year]
    sql: ${TABLE}.created_at ;;
    label: "Account Created"
    description: "When the billing account was established"
    datatype: timestamp
  }

  dimension_group: closed {
    type: time
    timeframes: [raw, date, month, year]
    sql: ${TABLE}.closed_at ;;
    label: "Account Closed"
    description: "When the billing account was closed (null if still active)"
    datatype: timestamp
  }

  # ── Measures ─────────────────────────────────────────────────────────────────
  measure: count {
    type: count
    label: "Number of Billing Accounts"
    description: "Total count of billing accounts"
  }

  measure: count_active {
    type: count
    filters: [closed_raw: "NULL"]
    label: "Active Billing Accounts"
    description: "Count of accounts that have not been closed"
  }

  measure: total_credit_limit {
    type: sum
    sql: ${credit_limit} ;;
    label: "Total Credit Limit"
    description: "Sum of credit limits across all accounts"
    value_format_name: usd
  }

  measure: avg_credit_limit {
    type: average
    sql: ${credit_limit} ;;
    label: "Average Credit Limit"
    description: "Average credit limit per billing account"
    value_format_name: usd
  }
}
