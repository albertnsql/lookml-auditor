view: inventory_items {
  sql_table_name: `product.inventory_items` ;;

  dimension: id {
    primary_key: yes
    type: number
    sql: ${TABLE}.id ;;
  }

  dimension: product_id {
    type: number
    sql: ${TABLE}.product_id ;;
  }

  dimension: warehouse_id {
    type: number
    sql: ${TABLE}.warehouse_id ;;
  }

  dimension: cost {
    type: number
    sql: ${TABLE}.cost ;;
  }

  dimension: created_at {
    type: time
    timeframes: [raw, date, week, month, year]
    sql: ${TABLE}.created_at ;;
  }

  measure: total_cost {
    type: sum
    sql: ${cost} ;;
  }

  measure: count {
    type: count
  }
}

# Unreferenced / Orphan View (Intentional error)
view: obsolete_inventory {
  sql_table_name: `product.obsolete_inventory` ;;
  dimension: id { primary_key: yes type: string sql: ${TABLE}.id ;; }
}
