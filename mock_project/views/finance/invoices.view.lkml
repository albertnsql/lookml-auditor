view: invoices {
  sql_table_name: `finance.invoices` ;;

  # Intentional error: Missing primary key

  dimension: invoice_id {
    type: string
    sql: ${TABLE}.id ;;
  }

  dimension: order_id {
    type: string
    sql: ${TABLE}.order_id ;;
  }

  dimension: amount {
    type: number
    sql: ${TABLE}.amount ;;
  }

  dimension: amount { # Intentional duplicate
    type: number
    sql: ${TABLE}.amount_usd ;;
  }

  dimension: status {
    type: string
    sql: ${TABLE}.status ;;
    description: "Invoice status: paid, unpaid, cancelled"
  }

  measure: total_amount {
    type: sum
    sql: ${amount} ;;
  }
}
