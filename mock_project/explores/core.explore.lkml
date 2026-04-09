# core.explore.lkml
# Transactional explores for the ecommerce model.
# Contains intentional LookML issues for auditor testing.

# ─────────────────────────────────────────────────────────────────────────────
# EXPLORE: orders
# Main explore for order-level analysis. Joins customers, items, payments,
# returns, refunds, and products.
# ISSUES: fanout join on returns, missing sql_on on payments
# ─────────────────────────────────────────────────────────────────────────────
explore: orders {
  label: "Orders & Customers"
  description: "Core transactional explore for orders, customers, payments, and returns"
  group_label: "E-Commerce"

  join: customers {
    type: left_outer
    sql_on: ${orders.customer_id} = ${customers.id} ;;
    relationship: many_to_one
  }

  join: users {
    type: left_outer
    sql_on: ${customers.id} = ${users.user_id} ;;
    relationship: many_to_one
  }

  join: order_items {
    type: left_outer
    sql_on: ${orders.id} = ${order_items.order_id} ;;
    relationship: one_to_many
  }

  join: products {
    type: left_outer
    sql_on: ${order_items.product_id} = ${products.id} ;;
    relationship: many_to_one
  }

  join: inventory_items {
    type: left_outer
    sql_on: ${order_items.product_id} = ${inventory_items.product_id} ;;
    # INTENTIONAL ISSUE: one_to_many join on both sides causes fanout
    relationship: one_to_many
  }

  # INTENTIONAL ISSUE: returns joined with many_to_many — causes fanout
  join: returns {
    type: left_outer
    sql_on: ${orders.id} = ${returns.order_id} ;;
    relationship: many_to_many
  }

  join: refunds {
    type: left_outer
    sql_on: ${orders.id} = ${refunds.order_id} ;;
    relationship: one_to_many
  }

  # INTENTIONAL ISSUE: join with no sql_on — will break at query time
  join: payments {
    type: left_outer
    relationship: many_to_one
  }

  # INTENTIONAL ISSUE: join references a view that doesn't exist
  join: missing_inventory {
    type: left_outer
    sql_on: ${orders.id} = ${missing_inventory.order_id} ;;
    relationship: one_to_many
  }
}

# ─────────────────────────────────────────────────────────────────────────────
# EXPLORE: customers
# Customer-centric explore for cohort and lifetime value analysis.
# ISSUES: missing relationship on orders join
# ─────────────────────────────────────────────────────────────────────────────
explore: customers {
  label: "Customer Overview"
  description: "Customer-centric explore including order history and lifetime value"
  group_label: "E-Commerce"

  join: orders {
    type: left_outer
    sql_on: ${customers.id} = ${orders.customer_id} ;;
    # INTENTIONAL ISSUE: missing relationship — required in Looker
  }

  join: orders_summary {
    type: left_outer
    sql_on: ${customers.id} = ${orders_summary.customer_id} ;;
    relationship: one_to_one
  }

  join: customer_lifetime_value {
    type: left_outer
    sql_on: ${customers.id} = ${customer_lifetime_value.customer_id} ;;
    relationship: one_to_one
  }

  join: payments {
    type: left_outer
    sql_on: ${orders.id} = ${payments.order_id} ;;
    relationship: one_to_many
  }
}

# ─────────────────────────────────────────────────────────────────────────────
# EXPLORE: order_funnel
# Multi-step funnel explore across the full order lifecycle.
# ISSUES: complex fanout potential, chained joins without correct relationships
# ─────────────────────────────────────────────────────────────────────────────
explore: order_funnel {
  label: "Order Funnel Analysis"
  description: "End-to-end funnel from customer acquisition through order completion"
  group_label: "E-Commerce"
  from: orders

  join: customers {
    type: left_outer
    sql_on: ${order_funnel.customer_id} = ${customers.id} ;;
    relationship: many_to_one
  }

  join: order_items {
    type: left_outer
    sql_on: ${order_funnel.id} = ${order_items.order_id} ;;
    relationship: one_to_many
  }

  join: refunds {
    type: left_outer
    sql_on: ${order_funnel.id} = ${refunds.order_id} ;;
    # INTENTIONAL ISSUE: one_to_many on both order_items and refunds causes measure inflation
    relationship: one_to_many
  }

  join: returns {
    type: left_outer
    sql_on: ${order_funnel.id} = ${returns.order_id} ;;
    relationship: one_to_many
  }

  join: payments {
    type: left_outer
    sql_on: ${order_funnel.id} = ${payments.order_id} ;;
    relationship: one_to_many
  }

  join: products {
    type: left_outer
    sql_on: ${order_items.product_id} = ${products.id} ;;
    relationship: many_to_one
  }
}

# ─────────────────────────────────────────────────────────────────────────────
# EXPLORE: ghost_explore
# INTENTIONAL ISSUE: from references a view that does not exist in the project
# ─────────────────────────────────────────────────────────────────────────────
explore: ghost_explore {
  label: "Ghost Explore"
  description: "Demo of a broken explore referencing a non-existent view"
  from: non_existent_view

  join: orders {
    type: left_outer
    sql_on: ${non_existent_view.id} = ${orders.customer_id} ;;
    relationship: many_to_one
  }
}

# ─────────────────────────────────────────────────────────────────────────────
# EXPLORE: product_inventory
# Product and inventory analysis.
# ─────────────────────────────────────────────────────────────────────────────
explore: product_inventory {
  label: "Product & Inventory"
  description: "Explore for product catalog and warehouse inventory management"
  group_label: "Supply Chain"
  from: products

  join: inventory_items {
    type: left_outer
    sql_on: ${product_inventory.id} = ${inventory_items.product_id} ;;
    relationship: one_to_many
  }

  join: warehouses {
    type: left_outer
    sql_on: ${inventory_items.warehouse_id} = ${warehouses.id} ;;
    relationship: many_to_one
  }

  join: product_metrics {
    type: left_outer
    sql_on: ${product_inventory.id} = ${product_metrics.product_id} ;;
    relationship: one_to_one
  }
}
