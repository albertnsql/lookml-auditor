# INTENTIONAL: This view is never referenced by any explore
view: staging_temp {
  sql_table_name: "staging.temp_data" ;;

  dimension: id {
    type: number
    sql: ${TABLE}.id ;;
  }

  dimension: raw_payload {
    type: string
    sql: ${TABLE}.payload ;;
  }

  measure: count {
    type: count
  }
}
