# users.view.lkml
# User account view — distinct from customers, representing authenticated users.
# INTENTIONAL ISSUES:
#   - Missing primary key (no primary_key: yes on any dimension)
#   - Several measures without label or description
#   - Inconsistent naming: user_id vs id convention

view: users {
  sql_table_name: "public.users" ;;

  # INTENTIONAL ISSUE: user_id is the natural PK but primary_key: yes is omitted
  dimension: user_id {
    type: number
    sql: ${TABLE}.user_id ;;
    label: "User ID"
    description: "Unique identifier for the user account"
    # primary_key: yes  ← intentionally commented out
  }

  dimension: username {
    type: string
    sql: ${TABLE}.username ;;
    label: "Username"
    description: "User's chosen display name"
  }

  dimension: email {
    type: string
    sql: ${TABLE}.email ;;
    label: "Email"
    description: "User account email address — PII"
    tags: ["pii"]
  }

  dimension: role {
    type: string
    sql: ${TABLE}.role ;;
    label: "User Role"
    description: "Permission role: admin, analyst, viewer, guest"
  }

  dimension: is_verified {
    type: yesno
    sql: ${TABLE}.is_verified ;;
    label: "Is Verified"
    description: "Whether the user's email address has been verified"
  }

  dimension: plan_type {
    type: string
    sql: ${TABLE}.plan_type ;;
    label: "Plan Type"
    description: "Subscription plan: free, starter, pro, enterprise"
  }

  dimension: preferred_language {
    type: string
    sql: ${TABLE}.preferred_language ;;
    label: "Preferred Language"
    # INTENTIONAL ISSUE: no description
  }

  # ── Dimension Groups ─────────────────────────────────────────────────────────
  dimension_group: signup {
    type: time
    timeframes: [raw, date, week, month, quarter, year]
    sql: ${TABLE}.created_at ;;
    label: "Signup"
    description: "When the user created their account"
    datatype: timestamp
  }

  dimension_group: last_login {
    type: time
    timeframes: [raw, date, week, month]
    sql: ${TABLE}.last_login_at ;;
    label: "Last Login"
    description: "Most recent user login timestamp"
    datatype: timestamp
  }

  dimension_group: last_active {
    type: time
    timeframes: [raw, date, week, month]
    sql: ${TABLE}.last_active_at ;;
    label: "Last Active"
    # INTENTIONAL ISSUE: no description
    datatype: timestamp
  }

  # ── Measures ─────────────────────────────────────────────────────────────────
  measure: count {
    type: count
    label: "Number of Users"
    description: "Total count of user records"
  }

  # INTENTIONAL ISSUE: no label or description
  measure: count_verified {
    type: count
    filters: [is_verified: "yes"]
  }

  measure: count_by_plan {
    type: count_distinct
    sql: ${plan_type} ;;
    label: "Count of Plans"
    description: "Number of distinct plan types — note: count_distinct on non-key"
  }

  # INTENTIONAL ISSUE: no label or description
  measure: count_by_role {
    type: count_distinct
    sql: ${role} ;;
  }
}
