# INTENTIONAL DUPLICATE: customers view defined again
view: customers {
  sql_table_name: "analytics.customers_v2" ;;

  dimension: id {
    type: number
    sql: ${TABLE}.customer_id ;;
    primary_key: yes
  }

  dimension: name {
    type: string
    sql: ${TABLE}.full_name ;;
  }

  measure: count {
    type: count
  }
}
