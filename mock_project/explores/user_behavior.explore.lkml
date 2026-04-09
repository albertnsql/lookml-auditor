# user_behavior.explore.lkml
# Web analytics explores covering sessions and events.
# Contains intentional LookML issues for auditor testing.

include: "/views/sessions.view.lkml"
include: "/views/events.view.lkml"
include: "/views/users.view.lkml"
include: "/views/customers.view.lkml"
include: "/views/orders.view.lkml"

# ─────────────────────────────────────────────────────────────────────────────
# EXPLORE: web_sessions
# Session-level web analytics with event breakdowns.
# ISSUES: events join causes massive fanout (many events per session),
#         users join has wrong relationship
# ─────────────────────────────────────────────────────────────────────────────
explore: web_sessions {
  label: "Web Sessions"
  description: "Session-level explore for web traffic, user behavior, and funnel analysis"
  group_label: "User Behaviour"
  from: sessions

  # INTENTIONAL ISSUE: many_to_one declared but events are one_to_many per session
  join: users {
    type: left_outer
    sql_on: ${web_sessions.user_id} = ${users.user_id} ;;
    relationship: many_to_one
  }

  # INTENTIONAL ISSUE: events fanout — many events per session, measure inflation likely
  join: events {
    type: left_outer
    sql_on: ${web_sessions.session_id} = ${events.session_id} ;;
    relationship: one_to_many
  }

  join: customers {
    type: left_outer
    sql_on: ${users.user_id} = ${customers.id} ;;
    # INTENTIONAL ISSUE: user_id and customers.id may be different types
    relationship: many_to_one
  }

  join: orders {
    type: left_outer
    sql_on: ${customers.id} = ${orders.customer_id} ;;
    relationship: one_to_many
  }
}

# ─────────────────────────────────────────────────────────────────────────────
# EXPLORE: event_stream
# Raw event stream analysis.
# INTENTIONAL ISSUE: no group_label — explore may appear ungrouped in UI
# ─────────────────────────────────────────────────────────────────────────────
explore: event_stream {
  label: "Event Stream"
  description: "Raw event stream for debugging and detailed user path analysis"
  from: events

  join: users {
    type: left_outer
    sql_on: ${event_stream.user_id} = ${users.user_id} ;;
    relationship: many_to_one
  }

  # INTENTIONAL ISSUE: sessions joined here creates circular join potential
  join: sessions {
    type: left_outer
    sql_on: ${event_stream.session_id} = ${sessions.session_id} ;;
    relationship: many_to_one
  }
}
