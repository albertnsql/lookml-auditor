# campaigns.view.lkml
# Marketing campaign records.
# INTENTIONAL ISSUES:
#   - avg_conversion_rate uses type:average on a string field
#   - Several dimensions missing description
#   - count measure has no description

view: campaigns {
  sql_table_name: `marketing.campaigns` ;;

  # ── Primary Key ─────────────────────────────────────────────────────────────
  dimension: id {
    primary_key: yes
    type: string
    sql: ${TABLE}.id ;;
    label: "Campaign ID"
    description: "Unique identifier for the marketing campaign"
  }

  # ── Dimensions ───────────────────────────────────────────────────────────────
  dimension: name {
    type: string
    sql: ${TABLE}.campaign_name ;;
    label: "Campaign Name"
    description: "Human-readable name of the campaign"
  }

  dimension: status {
    type: string
    sql: ${TABLE}.status ;;
    label: "Campaign Status"
    description: "Current status: draft, active, paused, completed, cancelled"
  }

  dimension: channel {
    type: string
    sql: ${TABLE}.channel ;;
    label: "Channel"
    description: "Marketing channel: email, paid_search, social, display, affiliate"
  }

  dimension: campaign_type {
    type: string
    sql: ${TABLE}.campaign_type ;;
    label: "Campaign Type"
    # INTENTIONAL ISSUE: no description
  }

  dimension: target_audience {
    type: string
    sql: ${TABLE}.target_audience ;;
    label: "Target Audience"
    # INTENTIONAL ISSUE: no description
  }

  dimension: budget {
    type: number
    sql: ${TABLE}.budget ;;
    label: "Campaign Budget"
    description: "Total allocated budget for this campaign"
    value_format_name: usd
  }

  dimension: goal_impressions {
    type: number
    sql: ${TABLE}.goal_impressions ;;
    label: "Impression Goal"
    description: "Target number of impressions for the campaign"
  }

  dimension: owner_email {
    type: string
    sql: ${TABLE}.owner_email ;;
    label: "Campaign Owner"
    description: "Email of the team member responsible for this campaign — PII"
    tags: ["pii"]
  }

  # ── Dimension Groups ─────────────────────────────────────────────────────────
  dimension_group: launch {
    type: time
    timeframes: [raw, date, week, month, quarter, year]
    sql: ${TABLE}.start_date ;;
    label: "Campaign Launch"
    description: "Date the campaign started running"
    datatype: date
  }

  dimension_group: end {
    type: time
    timeframes: [raw, date, week, month]
    sql: ${TABLE}.end_date ;;
    label: "Campaign End"
    description: "Date the campaign stopped running"
    datatype: date
  }

  # ── Parameters ───────────────────────────────────────────────────────────────
  parameter: channel_filter {
    type: string
    label: "Channel Filter"
    description: "Filter campaigns by channel"
    allowed_value: { label: "Email" value: "email" }
    allowed_value: { label: "Paid Search" value: "paid_search" }
    allowed_value: { label: "Social" value: "social" }
    allowed_value: { label: "Display" value: "display" }
    allowed_value: { label: "All" value: "%" }
  }

  # ── Measures ─────────────────────────────────────────────────────────────────
  # INTENTIONAL ISSUE: no description on count
  measure: count {
    type: count
    label: "Number of Campaigns"
  }

  measure: total_budget {
    type: sum
    sql: ${budget} ;;
    label: "Total Budget"
    description: "Sum of budgets across all campaigns"
    value_format_name: usd
  }

  measure: avg_budget {
    type: average
    sql: ${budget} ;;
    label: "Average Campaign Budget"
    description: "Average budget per campaign"
    value_format_name: usd
  }

  # INTENTIONAL ISSUE: type:average applied to a string field — semantically nonsensical
  measure: avg_conversion_rate {
    type: average
    sql: ${TABLE}.status ;;
    label: "Avg Conversion Rate (broken)"
    description: "ISSUE: type:average on status string — this will always return NULL or error"
  }

  measure: count_active {
    type: count
    filters: [status: "active"]
    label: "Active Campaigns"
    description: "Count of currently active campaigns"
  }

  # ── Sets ─────────────────────────────────────────────────────────────────────
  set: campaign_summary_fields {
    fields: [
      id,
      name,
      status,
      channel,
      campaign_type,
      budget,
      launch_date,
      end_date,
      count
    ]
  }
}
