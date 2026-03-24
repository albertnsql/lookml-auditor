view: orders {
  sql_table_name: "public.orders" ;;

  dimension: id {
    type: number
    sql: ${TABLE}.id ;;
    primary_key: yes
    label: "Order ID"
    description: "Unique identifier for each order"
  }

  dimension: customer_id {
    type: number
    sql: ${TABLE}.customer_id ;;
    # intentionally no label/description
  }

  dimension: status {
    type: string
    sql: ${TABLE}.status ;;
    label: "Order Status"
    # intentionally no description
  }

  dimension: created_date {
    type: date
    sql: ${TABLE}.created_at ;;
    # no label or description
  }

  # INTENTIONAL DUPLICATE field within the same view
  dimension: status {
    type: string
    sql: ${TABLE}.order_status ;;
  }

  measure: count {
    type: count
    label: "Number of Orders"
    description: "Total count of orders"
  }

  measure: total_amount {
    type: sum
    sql: ${TABLE}.amount ;;
    # no label or description
  }
}
