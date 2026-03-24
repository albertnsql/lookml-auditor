view: order_items {
  sql_table_name: "public.order_items" ;;

  dimension: id {
    type: number
    sql: ${TABLE}.id ;;
    primary_key: yes
  }

  dimension: order_id {
    type: number
    sql: ${TABLE}.order_id ;;
  }

  dimension: product_id {
    type: number
    sql: ${TABLE}.product_id ;;
  }

  measure: count {
    type: count
  }

  measure: total_revenue {
    type: sum
    sql: ${TABLE}.revenue ;;
  }
}
