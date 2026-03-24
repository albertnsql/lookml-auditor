view: payments {
  sql_table_name: "public.payments" ;;

  dimension: id {
    type: number
    sql: ${TABLE}.id ;;
    primary_key: yes
  }

  dimension: order_id {
    type: number
    sql: ${TABLE}.order_id ;;
  }

  dimension: amount {
    type: number
    sql: ${TABLE}.amount ;;
  }

  dimension: payment_method {
    type: string
    sql: ${TABLE}.method ;;
  }

  measure: count {
    type: count
  }
}
