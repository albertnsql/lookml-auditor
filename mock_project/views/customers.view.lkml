# customers.view.lkml
# Customer profile view.
# INTENTIONAL ISSUES:
#   - parameter with no allowed_values (region_filter)
#   - measure with no label or description
#   - total_revenue measure references lifetime_value which may be inconsistently populated

view: customers {
  sql_table_name: "public.customers" ;;

  # ── Primary Key ─────────────────────────────────────────────────────────────
  dimension: id {
    type: number
    sql: ${TABLE}.id ;;
    primary_key: yes
    label: "Customer ID"
    description: "Unique identifier for each customer"
    tags: ["key", "pii"]
  }

  # ── Dimensions ───────────────────────────────────────────────────────────────
  dimension: name {
    type: string
    sql: ${TABLE}.name ;;
    label: "Customer Name"
    description: "Full name of the customer"
    tags: ["pii"]
  }

  dimension: email {
    type: string
    sql: ${TABLE}.email ;;
    label: "Email Address"
    description: "Customer email address — contains PII"
    tags: ["pii"]
  }

  dimension: country {
    type: string
    sql: ${TABLE}.country ;;
    label: "Country"
    description: "Country of residence"
    map_layer_name: countries
  }

  dimension: state {
    type: string
    sql: ${TABLE}.state ;;
    label: "State / Province"
    description: "State or province of the customer's primary address"
  }

  dimension: city {
    type: string
    sql: ${TABLE}.city ;;
    label: "City"
    # INTENTIONAL ISSUE: no description
  }

  dimension: postal_code {
    type: zipcode
    sql: ${TABLE}.postal_code ;;
    label: "Postal Code"
    description: "Customer's postal/zip code"
  }

  dimension: customer_tier {
    type: string
    sql: ${TABLE}.tier ;;
    label: "Customer Tier"
    description: "Customer segment tier: Bronze, Silver, Gold, Platinum"
  }

  dimension: acquisition_channel {
    type: string
    sql: ${TABLE}.acquisition_channel ;;
    label: "Acquisition Channel"
    description: "Marketing channel through which the customer was acquired"
  }

  dimension: is_active {
    type: yesno
    sql: ${TABLE}.is_active ;;
    label: "Is Active"
    description: "Whether the customer account is currently active"
  }

  # INTENTIONAL ISSUE: hidden field but still referenced in other measures — confusing
  dimension: internal_notes {
    type: string
    sql: ${TABLE}.internal_notes ;;
    label: "Internal Notes"
    hidden: yes
    # This field is never surfaced in the UI but still exists in SQL
  }

  dimension: lifetime_value {
    type: number
    sql: ${TABLE}.lifetime_value ;;
    label: "Lifetime Value"
    description: "Predicted or measured customer lifetime value in USD"
    value_format_name: usd
  }

  # ── Dimension Groups ─────────────────────────────────────────────────────────
  dimension_group: created {
    type: time
    timeframes: [raw, date, week, month, quarter, year]
    sql: ${TABLE}.created_at ;;
    label: "Customer Created"
    description: "Timestamp when the customer account was created"
    datatype: timestamp
  }

  dimension_group: first_order {
    type: time
    timeframes: [raw, date, week, month, quarter, year]
    sql: ${TABLE}.first_order_at ;;
    label: "First Order"
    description: "Timestamp of the customer's first order"
    datatype: timestamp
  }

  dimension_group: last_order {
    type: time
    timeframes: [raw, date, week, month, year]
    sql: ${TABLE}.last_order_at ;;
    label: "Last Order"
    description: "Timestamp of the customer's most recent order"
    datatype: timestamp
  }

  # ── Parameters ───────────────────────────────────────────────────────────────
  # INTENTIONAL ISSUE: parameter with no allowed_values — open-ended string injection risk
  parameter: region_filter {
    type: string
    label: "Region Filter"
    description: "Filter customers by region — no allowed_values defined"
  }

  # ── Measures ─────────────────────────────────────────────────────────────────
  measure: count {
    type: count
    label: "Number of Customers"
    description: "Total distinct customer count"
    drill_fields: [id, name, email, country, customer_tier]
  }

  measure: total_revenue {
    type: sum
    sql: ${TABLE}.lifetime_value ;;
    label: "Total Lifetime Revenue"
    description: "Sum of lifetime value across all customers"
    value_format_name: usd
  }

  measure: average_lifetime_value {
    type: average
    sql: ${lifetime_value} ;;
    label: "Average Lifetime Value"
    description: "Average customer lifetime value"
    value_format_name: usd
  }

  # INTENTIONAL ISSUE: no label or description on measure
  measure: count_active {
    type: count
    filters: [is_active: "yes"]
  }

  measure: count_by_country {
    type: count_distinct
    sql: ${country} ;;
    label: "Count of Countries"
    description: "Number of distinct countries with customers — note: count_distinct on a dimension, not a key"
  }

  # ── Sets ─────────────────────────────────────────────────────────────────────
  set: customer_detail_fields {
    fields: [
      id,
      name,
      email,
      country,
      state,
      city,
      customer_tier,
      acquisition_channel,
      is_active,
      created_date,
      first_order_date,
      lifetime_value,
      count
    ]
  }
}
