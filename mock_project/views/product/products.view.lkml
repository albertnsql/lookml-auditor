view: products {
  sql_table_name: `product.products` ;;

  dimension: id {
    primary_key: yes
    type: number
    sql: ${TABLE}.id ;;
  }

  dimension: sku {
    type: string
    sql: ${TABLE}.sku ;;
    description: "Stock Keeping Unit"
  }

  dimension: name {
    type: string
    sql: ${TABLE}.name ;;
  }

  dimension: category {
    type: string
    sql: ${TABLE}.category ;;
  }

  dimension: price {
    type: number
    sql: ${TABLE}.price ;;
  }

  measure: average_price {
    type: average
    sql: ${price} ;;
  }

  measure: count {
    type: count
  }
}
