# inventory_items.view.lkml
# Inventory item records — tracks stock levels per product per warehouse.
# INTENTIONAL ISSUES:
#   - obsolete_inventory view defined in same file (orphan view)
#   - total_cost measure has no label
#   - quantity_on_hand dimension has no description

view: inventory_items {
  sql_table_name: `product.inventory_items` ;;

  # ── Primary Key ─────────────────────────────────────────────────────────────
  dimension: id {
    primary_key: yes
    type: number
    sql: ${TABLE}.id ;;
    label: "Inventory Item ID"
    description: "Unique identifier for this inventory record"
  }

  # ── Foreign Keys ─────────────────────────────────────────────────────────────
  dimension: product_id {
    type: number
    sql: ${TABLE}.product_id ;;
    label: "Product ID"
    description: "Foreign key to the product catalog"
    hidden: yes
  }

  dimension: warehouse_id {
    type: number
    sql: ${TABLE}.warehouse_id ;;
    label: "Warehouse ID"
    description: "Foreign key to the warehouse holding this item"
    hidden: yes
  }

  # ── Dimensions ───────────────────────────────────────────────────────────────
  dimension: cost {
    type: number
    sql: ${TABLE}.cost ;;
    label: "Unit Cost"
    description: "Cost per unit of this inventory item"
    value_format_name: usd
  }

  dimension: quantity_on_hand {
    type: number
    sql: ${TABLE}.quantity_on_hand ;;
    label: "Quantity On Hand"
    # INTENTIONAL ISSUE: no description
  }

  dimension: quantity_reserved {
    type: number
    sql: ${TABLE}.quantity_reserved ;;
    label: "Quantity Reserved"
    description: "Units reserved for pending orders"
  }

  dimension: quantity_available {
    type: number
    sql: ${TABLE}.quantity_on_hand - ${TABLE}.quantity_reserved ;;
    label: "Quantity Available"
    description: "Net available stock (on hand minus reserved)"
  }

  dimension: reorder_point {
    type: number
    sql: ${TABLE}.reorder_point ;;
    label: "Reorder Point"
    description: "Stock level at which a reorder is triggered"
  }

  dimension: is_low_stock {
    type: yesno
    sql: ${TABLE}.quantity_on_hand < ${TABLE}.reorder_point ;;
    label: "Is Low Stock"
    description: "Whether the current stock level is below the reorder threshold"
  }

  dimension: condition {
    type: string
    sql: ${TABLE}.condition ;;
    label: "Item Condition"
    description: "Physical condition: new, used, refurbished, damaged"
  }

  dimension_group: created {
    type: time
    timeframes: [raw, date, week, month, year]
    sql: ${TABLE}.created_at ;;
    label: "Received"
    description: "When the inventory item was received into the warehouse"
    datatype: timestamp
  }

  dimension_group: last_counted {
    type: time
    timeframes: [raw, date, month]
    sql: ${TABLE}.last_counted_at ;;
    label: "Last Counted"
    description: "When the most recent physical inventory count was performed"
    datatype: timestamp
  }

  # ── Measures ─────────────────────────────────────────────────────────────────
  # INTENTIONAL ISSUE: no label — defaults to "Total Cost"
  measure: total_cost {
    type: sum
    sql: ${cost} ;;
    description: "Total cost value of all inventory items"
    value_format_name: usd
  }

  measure: total_quantity_on_hand {
    type: sum
    sql: ${quantity_on_hand} ;;
    label: "Total Units On Hand"
    description: "Sum of all units currently in inventory"
  }

  measure: total_quantity_available {
    type: sum
    sql: ${quantity_available} ;;
    label: "Total Units Available"
    description: "Sum of available (unreserved) units"
  }

  measure: count_low_stock_items {
    type: count
    filters: [is_low_stock: "yes"]
    label: "Low Stock Items"
    description: "Count of inventory records below the reorder threshold"
  }

  measure: count {
    type: count
    label: "Inventory Record Count"
    description: "Total number of inventory item records"
  }

  measure: avg_cost {
    type: average
    sql: ${cost} ;;
    label: "Average Unit Cost"
    description: "Mean cost per inventory unit"
    value_format_name: usd
  }
}

# ─────────────────────────────────────────────────────────────────────────────
# INTENTIONAL ISSUE: orphan view defined in the same file — never referenced by any explore
# ─────────────────────────────────────────────────────────────────────────────
view: obsolete_inventory {
  sql_table_name: `product.obsolete_inventory` ;;

  dimension: id {
    primary_key: yes
    type: string
    sql: ${TABLE}.id ;;
    label: "Legacy Item ID"
    description: "ID from the old inventory system — deprecated"
  }

  dimension: legacy_sku {
    type: string
    sql: ${TABLE}.legacy_sku ;;
    label: "Legacy SKU"
    # INTENTIONAL ISSUE: no description
  }

  measure: count {
    type: count
    label: "Legacy Item Count"
    description: "Count of items still in the obsolete inventory system"
  }
}
