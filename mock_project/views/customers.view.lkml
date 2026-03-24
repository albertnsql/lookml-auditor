view: customers {
  sql_table_name: "public.customers" ;;

  dimension: id {
    type: number
    sql: ${TABLE}.id ;;
    primary_key: yes
  }

  dimension: name {
    type: string
    sql: ${TABLE}.name ;;
  }

  dimension: email {
    type: string
    sql: ${TABLE}.email ;;
  }

  dimension: country {
    type: string
    sql: ${TABLE}.country ;;
  }

  # intentionally unused dimension
  dimension: internal_notes {
    type: string
    sql: ${TABLE}.internal_notes ;;
    hidden: yes
  }

  measure: count {
    type: count
  }

  measure: total_revenue {
    type: sum
    sql: ${TABLE}.lifetime_value ;;
  }
}
