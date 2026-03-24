view: orders_summary {
  derived_table: {
    sql:
      SELECT
        customer_id,
        COUNT(*) AS order_count,
        SUM(amount) AS total_spent
      FROM public.orders
      GROUP BY 1
    ;;
  }

  dimension: customer_id {
    type: number
    sql: ${TABLE}.customer_id ;;
    primary_key: yes
    label: "Customer ID"
    description: "Customer identifier from orders"
  }

  measure: order_count {
    type: sum
    sql: ${TABLE}.order_count ;;
    label: "Order Count"
    description: "Number of orders per customer"
  }

  measure: total_spent {
    type: sum
    sql: ${TABLE}.total_spent ;;
    # no label or description — intentional
  }
}
