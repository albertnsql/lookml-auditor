# events.view.lkml
# User event stream PDT — each row is a single user interaction event.
# INTENTIONAL ISSUES:
#   - SELECT * in derived table SQL
#   - No primary key defined
#   - No persistence (no datagroup_trigger / persist_for)
#   - Joining this to sessions causes extreme fanout (many events per session)

view: events {
  derived_table: {
    # INTENTIONAL ISSUE: SELECT * — pulls entire events table schema
    sql:
      SELECT
        *
      FROM analytics.events
      WHERE event_date >= DATEADD(day, -90, CURRENT_DATE)
    ;;
    # INTENTIONAL ISSUE: no persistence — this is a huge table queried fresh each time
  }

  # INTENTIONAL ISSUE: no primary_key: yes
  dimension: event_id {
    type: string
    sql: ${TABLE}.event_id ;;
    label: "Event ID"
    description: "Unique identifier for the event"
  }

  dimension: session_id {
    type: string
    sql: ${TABLE}.session_id ;;
    label: "Session ID"
    description: "Session this event belongs to"
  }

  dimension: user_id {
    type: number
    sql: ${TABLE}.user_id ;;
    label: "User ID"
    description: "User who triggered the event"
    hidden: yes
  }

  dimension: event_type {
    type: string
    sql: ${TABLE}.event_type ;;
    label: "Event Type"
    description: "Category of event: page_view, click, form_submit, purchase, etc."
  }

  dimension: event_name {
    type: string
    sql: ${TABLE}.event_name ;;
    label: "Event Name"
    description: "Specific name of the event as tracked"
  }

  dimension: page_url {
    type: string
    sql: ${TABLE}.page_url ;;
    label: "Page URL"
    description: "Full URL of the page where the event occurred"
  }

  dimension: referrer {
    type: string
    sql: ${TABLE}.referrer ;;
    label: "Referrer URL"
    # INTENTIONAL ISSUE: no description
  }

  dimension: element_id {
    type: string
    sql: ${TABLE}.element_id ;;
    label: "Element ID"
    description: "HTML element ID that triggered the event (for clicks)"
  }

  dimension: properties_json {
    type: string
    sql: ${TABLE}.properties ;;
    label: "Event Properties (JSON)"
    description: "Raw JSON payload of event properties — requires parsing"
    hidden: yes
  }

  # ── Dimension Groups ─────────────────────────────────────────────────────────
  dimension_group: event {
    type: time
    timeframes: [raw, time, date, week, month]
    sql: ${TABLE}.event_timestamp ;;
    label: "Event"
    description: "Timestamp when the event occurred"
    datatype: timestamp
  }

  # ── Measures ─────────────────────────────────────────────────────────────────
  measure: count {
    type: count
    label: "Event Count"
    description: "Total number of events"
  }

  measure: count_unique_sessions {
    type: count_distinct
    sql: ${session_id} ;;
    label: "Unique Sessions"
    description: "Count of distinct sessions with at least one event"
  }

  measure: count_unique_users {
    type: count_distinct
    sql: ${user_id} ;;
    label: "Unique Users"
    description: "Count of distinct users who triggered an event"
  }

  # INTENTIONAL ISSUE: no label, no description
  measure: count_page_views {
    type: count
    filters: [event_type: "page_view"]
  }

  measure: count_clicks {
    type: count
    filters: [event_type: "click"]
    label: "Click Count"
    description: "Total number of click events"
  }

  measure: count_form_submits {
    type: count
    filters: [event_type: "form_submit"]
    label: "Form Submissions"
    description: "Count of form submission events"
  }
}
