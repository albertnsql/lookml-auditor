# order_items.view.lkml
# Line-item level order details.
# INTENTIONAL ISSUES:
#   - total_revenue measure with no label or description
#   - sale_price measure references a field via ${TABLE} instead of ${dimension}
#   - measure without filters that could double-count when joined

view: order_items {
  sql_table_name: "public.order_items" ;;

  # ── Primary Key ─────────────────────────────────────────────────────────────
  dimension: id {
    type: number
    sql: ${TABLE}.id ;;
    primary_key: yes
    label: "Order Item ID"
    description: "Unique identifier for each line item in an order"
  }

  # ── Foreign Keys ─────────────────────────────────────────────────────────────
  dimension: order_id {
    type: number
    sql: ${TABLE}.order_id ;;
    label: "Order ID"
    description: "Foreign key to the orders table"
  }

  dimension: product_id {
    type: number
    sql: ${TABLE}.product_id ;;
    label: "Product ID"
    description: "Foreign key to the products table"
  }

  dimension: inventory_item_id {
    type: number
    sql: ${TABLE}.inventory_item_id ;;
    label: "Inventory Item ID"
    description: "Foreign key to the inventory items table"
    hidden: yes
  }

  # ── Dimensions ───────────────────────────────────────────────────────────────
  dimension: status {
    type: string
    sql: ${TABLE}.status ;;
    label: "Item Status"
    description: "Fulfillment status of this specific line item"
  }

  dimension: sale_price {
    type: number
    sql: ${TABLE}.sale_price ;;
    label: "Sale Price"
    description: "Actual price paid for the item after any discounts"
    value_format_name: usd
  }

  dimension: base_price {
    type: number
    sql: ${TABLE}.base_price ;;
    label: "Base Price"
    description: "Original list price before discounts"
    value_format_name: usd
  }

  dimension: discount_amount {
    type: number
    sql: ${TABLE}.discount_amount ;;
    label: "Discount Amount"
    description: "Amount discounted from the base price"
    value_format_name: usd
  }

  dimension: quantity {
    type: number
    sql: ${TABLE}.quantity ;;
    label: "Quantity"
    description: "Number of units of this item ordered"
  }

  dimension: is_returned {
    type: yesno
    sql: ${TABLE}.is_returned ;;
    label: "Is Returned"
    description: "Whether this line item was returned"
  }

  dimension: return_reason {
    type: string
    sql: ${TABLE}.return_reason ;;
    label: "Return Reason"
    # INTENTIONAL ISSUE: no description
  }

  # ── Dimension Groups ─────────────────────────────────────────────────────────
  dimension_group: created {
    type: time
    timeframes: [raw, date, week, month, year]
    sql: ${TABLE}.created_at ;;
    label: "Item Created"
    description: "Timestamp when the line item was created"
    datatype: timestamp
  }

  dimension_group: returned {
    type: time
    timeframes: [raw, date, week, month]
    sql: ${TABLE}.returned_at ;;
    label: "Item Returned"
    description: "Timestamp when the item was returned"
    datatype: timestamp
  }

  # ── Measures ─────────────────────────────────────────────────────────────────
  measure: count {
    type: count
    label: "Number of Items"
    description: "Total count of order line items"
    drill_fields: [id, order_id, product_id, status, sale_price]
  }

  # INTENTIONAL ISSUE: no label or description
  measure: total_revenue {
    type: sum
    sql: ${TABLE}.revenue ;;
  }

  measure: total_sale_price {
    type: sum
    sql: ${sale_price} ;;
    label: "Total Sale Revenue"
    description: "Sum of sale prices across order items"
    value_format_name: usd
  }

  measure: total_discount {
    type: sum
    sql: ${discount_amount} ;;
    label: "Total Discount Given"
    description: "Sum of all discounts applied across line items"
    value_format_name: usd
  }

  measure: average_sale_price {
    type: average
    sql: ${sale_price} ;;
    label: "Average Sale Price"
    description: "Average price per item"
    value_format_name: usd
  }

  measure: count_returned {
    type: count
    filters: [is_returned: "yes"]
    label: "Items Returned"
    description: "Count of returned line items"
  }

  # INTENTIONAL ISSUE: return_rate divides two measures — can produce misleading result
  # when joined in a fanout scenario
  measure: return_rate {
    type: number
    sql: ${count_returned} / NULLIF(${count}, 0) ;;
    label: "Return Rate"
    description: "Fraction of items that were returned — warning: affected by fanout joins"
    value_format_name: percent_2
  }
}
