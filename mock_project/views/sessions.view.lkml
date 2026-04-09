# sessions.view.lkml
# Web session PDT — each row represents one user session.
# INTENTIONAL ISSUES:
#   - SELECT * in derived table SQL
#   - No primary key defined
#   - No persistence strategy (no datagroup_trigger or persist_for)

view: sessions {
  derived_table: {
    # INTENTIONAL ISSUE: SELECT * — fragile, pulls all columns from source
    # This will break if upstream schema changes
    sql:
      SELECT
        *,
        ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY session_start_at) AS session_number
      FROM analytics.sessions
      WHERE session_start_at >= DATEADD(day, -180, CURRENT_DATE)
    ;;
    # INTENTIONAL ISSUE: No datagroup_trigger or persist_for — ephemeral PDT
  }

  # INTENTIONAL ISSUE: No primary_key: yes on any dimension
  dimension: session_id {
    type: string
    sql: ${TABLE}.session_id ;;
    label: "Session ID"
    description: "Unique identifier for the session"
    # primary_key: yes  ← intentionally omitted
  }

  dimension: user_id {
    type: number
    sql: ${TABLE}.user_id ;;
    label: "User ID"
    description: "User associated with this session"
  }

  dimension: session_number {
    type: number
    sql: ${TABLE}.session_number ;;
    label: "Session Number"
    description: "Ordinal position of this session for the user (1 = first session)"
  }

  dimension: device_type {
    type: string
    sql: ${TABLE}.device_type ;;
    label: "Device Type"
    description: "Device category: desktop, mobile, tablet"
  }

  dimension: browser {
    type: string
    sql: ${TABLE}.browser ;;
    label: "Browser"
    description: "Browser used during session"
  }

  dimension: landing_page {
    type: string
    sql: ${TABLE}.landing_page ;;
    label: "Landing Page"
    description: "First page visited in the session"
  }

  dimension: exit_page {
    type: string
    sql: ${TABLE}.exit_page ;;
    label: "Exit Page"
    # INTENTIONAL ISSUE: no description
  }

  dimension: channel {
    type: string
    sql: ${TABLE}.channel ;;
    label: "Traffic Channel"
    description: "Marketing channel: organic, paid, email, direct, referral"
  }

  dimension: is_bounce {
    type: yesno
    sql: ${TABLE}.is_bounce ;;
    label: "Is Bounce"
    description: "Whether the session had only a single page view"
  }

  dimension: page_views {
    type: number
    sql: ${TABLE}.page_views ;;
    label: "Page Views"
    description: "Total number of pages viewed in this session"
  }

  dimension: duration_seconds {
    type: number
    sql: ${TABLE}.duration_seconds ;;
    label: "Session Duration (sec)"
    description: "Total session duration in seconds"
  }

  # ── Dimension Groups ─────────────────────────────────────────────────────────
  dimension_group: session_start {
    type: time
    timeframes: [raw, time, date, week, month, quarter, year]
    sql: ${TABLE}.session_start_at ;;
    label: "Session Start"
    description: "When the session began"
    datatype: timestamp
  }

  # ── Measures ─────────────────────────────────────────────────────────────────
  measure: count {
    type: count
    label: "Number of Sessions"
    description: "Total count of web sessions"
  }

  measure: count_bounces {
    type: count
    filters: [is_bounce: "yes"]
    label: "Bounce Count"
    description: "Count of sessions where the user left after viewing one page"
  }

  measure: bounce_rate {
    type: number
    sql: ${count_bounces} / NULLIF(${count}, 0) ;;
    label: "Bounce Rate"
    description: "Percentage of sessions that resulted in a bounce"
    value_format_name: percent_2
  }

  measure: avg_page_views {
    type: average
    sql: ${page_views} ;;
    label: "Avg Pages Per Session"
    description: "Average number of pages viewed per session"
    value_format_name: decimal_1
  }

  measure: avg_duration_seconds {
    type: average
    sql: ${duration_seconds} ;;
    label: "Avg Session Duration (sec)"
    description: "Average session length in seconds"
  }

  measure: count_unique_users {
    type: count_distinct
    sql: ${user_id} ;;
    label: "Unique Users"
    description: "Count of distinct users with at least one session"
  }
}
