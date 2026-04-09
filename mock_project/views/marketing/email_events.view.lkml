# email_events.view.lkml
# Email engagement event records.
# INTENTIONAL ISSUES:
#   - Missing primary key
#   - Inconsistent naming convention (camelCase mixed with snake_case)
#   - Several measures without description

view: email_events {
  sql_table_name: `marketing.email_events` ;;

  # INTENTIONAL ISSUE: no primary_key: yes
  dimension: eventId {
    # INTENTIONAL ISSUE: camelCase field name — inconsistent with snake_case naming convention
    type: string
    sql: ${TABLE}.event_id ;;
    label: "Event ID"
    description: "Unique identifier for the email event"
  }

  dimension: campaign_id {
    type: string
    sql: ${TABLE}.campaign_id ;;
    label: "Campaign ID"
    description: "Campaign that sent this email"
    hidden: yes
  }

  dimension: customer_id {
    type: number
    sql: ${TABLE}.customer_id ;;
    label: "Customer ID"
    description: "Recipient customer"
    hidden: yes
  }

  dimension: emailAddress {
    # INTENTIONAL ISSUE: camelCase naming — should be email_address
    type: string
    sql: ${TABLE}.email_address ;;
    label: "Email Address"
    description: "Recipient email address — PII"
    tags: ["pii"]
  }

  dimension: eventType {
    # INTENTIONAL ISSUE: camelCase naming — should be event_type
    type: string
    sql: ${TABLE}.event_type ;;
    label: "Event Type"
    description: "Type of email event: sent, delivered, opened, clicked, bounced, unsubscribed"
  }

  dimension: subject_line {
    type: string
    sql: ${TABLE}.subject_line ;;
    label: "Email Subject"
    description: "Subject line of the email"
  }

  dimension: template_id {
    type: string
    sql: ${TABLE}.template_id ;;
    label: "Template ID"
    # INTENTIONAL ISSUE: no description
  }

  dimension: device_type {
    type: string
    sql: ${TABLE}.device_type ;;
    label: "Device Type"
    description: "Device used to open/click the email"
  }

  dimension: is_unsubscribe {
    type: yesno
    sql: ${TABLE}.event_type = 'unsubscribed' ;;
    label: "Is Unsubscribe"
    description: "Whether this event represents an unsubscribe action"
  }

  # ── Dimension Groups ─────────────────────────────────────────────────────────
  dimension_group: event {
    type: time
    timeframes: [raw, time, date, week, month]
    sql: ${TABLE}.event_timestamp ;;
    label: "Email Event"
    description: "When the email event occurred"
    datatype: timestamp
  }

  # ── Measures ─────────────────────────────────────────────────────────────────
  measure: count {
    type: count
    label: "Email Event Count"
    description: "Total count of email events"
  }

  # INTENTIONAL ISSUE: no label or description
  measure: count_sends {
    type: count
    filters: [eventType: "sent"]
  }

  # INTENTIONAL ISSUE: no description
  measure: count_opens {
    type: count
    filters: [eventType: "opened"]
    label: "Email Opens"
  }

  measure: count_clicks {
    type: count
    filters: [eventType: "clicked"]
    label: "Email Clicks"
    description: "Count of email click events"
  }

  measure: count_unsubscribes {
    type: count
    filters: [is_unsubscribe: "yes"]
    label: "Unsubscribes"
    description: "Count of unsubscribe events"
  }

  measure: open_rate {
    type: number
    sql: ${count_opens} / NULLIF(${count_sends}, 0) ;;
    label: "Open Rate"
    description: "Fraction of sent emails that were opened"
    value_format_name: percent_2
  }

  measure: click_rate {
    type: number
    sql: ${count_clicks} / NULLIF(${count_sends}, 0) ;;
    label: "Click Rate"
    description: "Fraction of sent emails that had at least one click"
    value_format_name: percent_2
  }

  measure: unsubscribe_rate {
    type: number
    sql: ${count_unsubscribes} / NULLIF(${count_sends}, 0) ;;
    label: "Unsubscribe Rate"
    description: "Fraction of sends that resulted in an unsubscribe"
    value_format_name: percent_4
  }
}
