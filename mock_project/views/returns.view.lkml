# returns.view.lkml
# Product return records.
# INTENTIONAL ISSUES:
#   - Missing primary key
#   - Joined to orders with many_to_many relationship (fanout)
#   - Several measures with no label or description

view: returns {
  sql_table_name: "public.returns" ;;

  # INTENTIONAL ISSUE: No primary_key: yes defined on any dimension
  dimension: return_id {
    type: string
    sql: ${TABLE}.return_id ;;
    label: "Return ID"
    description: "Unique identifier for the return request"
    # primary_key: yes  ← intentionally omitted
  }

  dimension: order_id {
    type: number
    sql: ${TABLE}.order_id ;;
    label: "Order ID"
    description: "Order associated with this return"
  }

  dimension: order_item_id {
    type: number
    sql: ${TABLE}.order_item_id ;;
    label: "Order Item ID"
    description: "Specific item being returned"
  }

  dimension: customer_id {
    type: number
    sql: ${TABLE}.customer_id ;;
    label: "Customer ID"
    description: "Customer initiating the return"
    hidden: yes
  }

  dimension: product_id {
    type: number
    sql: ${TABLE}.product_id ;;
    label: "Product ID"
    description: "Product being returned"
    hidden: yes
  }

  dimension: return_reason {
    type: string
    sql: ${TABLE}.reason ;;
    label: "Return Reason"
    description: "Reason provided by the customer: defective, wrong_size, changed_mind, other"
  }

  dimension: status {
    type: string
    sql: ${TABLE}.status ;;
    label: "Return Status"
    description: "Current processing status: pending, approved, rejected, completed"
  }

  dimension: item_condition {
    type: string
    sql: ${TABLE}.item_condition ;;
    label: "Item Condition on Return"
    # INTENTIONAL ISSUE: no description
  }

  dimension: refund_eligible {
    type: yesno
    sql: ${TABLE}.refund_eligible ;;
    label: "Refund Eligible"
    description: "Whether the return qualifies for a refund"
  }

  # ── Dimension Groups ─────────────────────────────────────────────────────────
  dimension_group: requested {
    type: time
    timeframes: [raw, date, week, month, quarter, year]
    sql: ${TABLE}.requested_at ;;
    label: "Return Requested"
    description: "When the customer submitted the return request"
    datatype: timestamp
  }

  dimension_group: resolved {
    type: time
    timeframes: [raw, date, week, month]
    sql: ${TABLE}.resolved_at ;;
    label: "Return Resolved"
    description: "When the return was approved or rejected"
    datatype: timestamp
  }

  # ── Measures ─────────────────────────────────────────────────────────────────
  measure: count {
    type: count
    label: "Number of Returns"
    description: "Total count of return requests"
  }

  # INTENTIONAL ISSUE: no label or description
  measure: count_approved {
    type: count
    filters: [status: "approved"]
  }

  # INTENTIONAL ISSUE: no label or description
  measure: count_rejected {
    type: count
    filters: [status: "rejected"]
  }

  measure: approval_rate {
    type: number
    sql: ${count_approved} / NULLIF(${count}, 0) ;;
    label: "Return Approval Rate"
    description: "Percentage of returns that were approved"
    value_format_name: percent_2
  }
}
