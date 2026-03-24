explore: orders {
  label: "Orders & Customers"
  description: "Core transactional explore for orders, customers, and payments"

  join: customers {
    type: left_outer
    sql_on: ${orders.customer_id} = ${customers.id} ;;
    relationship: many_to_one
  }

  join: order_items {
    type: left_outer
    sql_on: ${orders.id} = ${order_items.order_id} ;;
    relationship: one_to_many
  }

  # INTENTIONAL: join references a view that doesn't exist
  join: missing_inventory {
    type: left_outer
    sql_on: ${orders.id} = ${missing_inventory.order_id} ;;
    relationship: one_to_many
  }

  # INTENTIONAL: join with no sql_on or foreign_key
  join: payments {
    type: left_outer
    relationship: many_to_one
  }
}

explore: customers {
  label: "Customer Overview"
  description: "Customer-centric explore"

  join: orders {
    type: left_outer
    sql_on: ${customers.id} = ${orders.customer_id} ;;
    # INTENTIONAL: missing relationship
  }
}

# INTENTIONAL: explore references a non-existent base view
explore: ghost_explore {
  label: "Ghost Explore"
  from: non_existent_view

  join: orders {
    type: left_outer
    sql_on: ${non_existent_view.id} = ${orders.customer_id} ;;
    relationship: many_to_one
  }
}
