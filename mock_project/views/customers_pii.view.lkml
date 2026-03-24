# INTENTIONAL: Same sql_table_name as customers.view.lkml — should be flagged
view: customers_pii {
  sql_table_name: "public.customers" ;;

  dimension: id {
    type: number
    sql: ${TABLE}.id ;;
    primary_key: yes
    label: "Customer ID"
    description: "Unique customer identifier"
  }

  dimension: email {
    type: string
    sql: ${TABLE}.email ;;
    label: "Email Address"
    description: "Customer email — handle with care (PII)"
  }

  measure: count {
    type: count
    label: "Customer Count"
    description: "Total number of customers"
  }
}
