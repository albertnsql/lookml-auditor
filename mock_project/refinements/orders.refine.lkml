# orders.refine.lkml
# Refinement of the orders view.
# Adds tags, hides internal fields, and extends the orders set
# without modifying the base orders.view.lkml file.
# This demonstrates the LookML refinement pattern (+: syntax).

view: +orders {
  # Add a computed dimension not in the base view
  dimension: days_to_ship {
    type: number
    sql: DATEDIFF(day, ${TABLE}.created_at, ${TABLE}.shipped_at) ;;
    label: "Days to Ship"
    description: "Number of days between order placement and shipment"
  }

  dimension: is_express_shipping {
    type: yesno
    sql: DATEDIFF(day, ${TABLE}.created_at, ${TABLE}.shipped_at) <= 1 ;;
    label: "Is Express Shipping"
    description: "Whether the order shipped within 1 day of being placed"
  }

  dimension: order_size_tier {
    type: string
    sql:
      CASE
        WHEN ${TABLE}.amount >= 500  THEN 'Large'
        WHEN ${TABLE}.amount >= 100  THEN 'Medium'
        WHEN ${TABLE}.amount >= 25   THEN 'Small'
        ELSE 'Micro'
      END
    ;;
    label: "Order Size Tier"
    description: "Categorises orders by amount: Micro / Small / Medium / Large"
  }

  # Hide the internal billing_account_id from the UI
  # (it should be joined via billing_accounts view, not exposed raw)
  dimension: billing_account_id {
    hidden: yes
  }

  # Add a shipping performance measure
  measure: avg_days_to_ship {
    type: average
    sql: DATEDIFF(day, ${TABLE}.created_at, ${TABLE}.shipped_at) ;;
    label: "Avg Days to Ship"
    description: "Average number of days between order creation and shipment"
    value_format_name: decimal_1
  }

  measure: count_express {
    type: count
    filters: [is_express_shipping: "yes"]
    label: "Express Shipments"
    description: "Count of orders that shipped within 1 day"
  }

  # Extend the order_fields set to include the new refinement dimensions
  set: order_fields {
    fields: [
      id,
      customer_id,
      status,
      source,
      region,
      order_size_tier,
      days_to_ship,
      is_express_shipping,
      created_date,
      shipped_date,
      total_amount,
      count,
      avg_days_to_ship
    ]
  }
}
