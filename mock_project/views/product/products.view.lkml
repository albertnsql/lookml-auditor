# products.view.lkml
# Product catalog view.
# INTENTIONAL ISSUES:
#   - average_price uses ${price} dimension reference but price has no label
#   - count measure has no description

view: products {
  sql_table_name: `product.products` ;;

  # ── Primary Key ─────────────────────────────────────────────────────────────
  dimension: id {
    primary_key: yes
    type: number
    sql: ${TABLE}.id ;;
    label: "Product ID"
    description: "Unique identifier for the product"
  }

  # ── Dimensions ───────────────────────────────────────────────────────────────
  dimension: sku {
    type: string
    sql: ${TABLE}.sku ;;
    label: "SKU"
    description: "Stock Keeping Unit — unique product code used in inventory management"
  }

  dimension: name {
    type: string
    sql: ${TABLE}.name ;;
    label: "Product Name"
    description: "Display name of the product"
  }

  dimension: category {
    type: string
    sql: ${TABLE}.category ;;
    label: "Category"
    description: "Top-level product category"
  }

  dimension: subcategory {
    type: string
    sql: ${TABLE}.subcategory ;;
    label: "Subcategory"
    description: "Product subcategory within the main category"
  }

  dimension: brand {
    type: string
    sql: ${TABLE}.brand ;;
    label: "Brand"
    description: "Brand name of the product"
  }

  dimension: price {
    type: number
    sql: ${TABLE}.price ;;
    label: "List Price"
    description: "Standard retail price before any discounts"
    value_format_name: usd
  }

  dimension: cost {
    type: number
    sql: ${TABLE}.cost ;;
    label: "Unit Cost"
    description: "Cost of goods for one unit"
    value_format_name: usd
  }

  dimension: margin {
    type: number
    sql: ${TABLE}.price - ${TABLE}.cost ;;
    label: "Gross Margin"
    description: "Difference between list price and unit cost"
    value_format_name: usd
  }

  dimension: is_active {
    type: yesno
    sql: ${TABLE}.is_active ;;
    label: "Is Active"
    description: "Whether the product is currently available for sale"
  }

  dimension: is_featured {
    type: yesno
    sql: ${TABLE}.is_featured ;;
    label: "Is Featured"
    description: "Whether the product is displayed in featured sections"
  }

  dimension: weight_kg {
    type: number
    sql: ${TABLE}.weight_kg ;;
    label: "Weight (kg)"
    # INTENTIONAL ISSUE: no description
  }

  dimension: supplier_id {
    type: number
    sql: ${TABLE}.supplier_id ;;
    label: "Supplier ID"
    description: "Foreign key to the supplier providing this product"
    hidden: yes
  }

  # ── Dimension Groups ─────────────────────────────────────────────────────────
  dimension_group: created {
    type: time
    timeframes: [raw, date, week, month, year]
    sql: ${TABLE}.created_at ;;
    label: "Product Created"
    description: "When the product was added to the catalog"
    datatype: timestamp
  }

  dimension_group: discontinued {
    type: time
    timeframes: [raw, date, month, year]
    sql: ${TABLE}.discontinued_at ;;
    label: "Discontinued"
    description: "When the product was removed from the catalog (null if still active)"
    datatype: timestamp
  }

  # ── Parameters ───────────────────────────────────────────────────────────────
  parameter: category_filter {
    type: string
    label: "Category Filter"
    description: "Filter products by category"
    allowed_value: { label: "Electronics" value: "electronics" }
    allowed_value: { label: "Apparel" value: "apparel" }
    allowed_value: { label: "Home & Garden" value: "home_garden" }
    allowed_value: { label: "Sports" value: "sports" }
    allowed_value: { label: "Books" value: "books" }
    allowed_value: { label: "All" value: "%" }
  }

  # ── Measures ─────────────────────────────────────────────────────────────────
  # INTENTIONAL ISSUE: no description on count
  measure: count {
    type: count
    label: "Product Count"
  }

  measure: average_price {
    type: average
    sql: ${price} ;;
    label: "Average List Price"
    description: "Mean list price across products"
    value_format_name: usd
  }

  measure: average_margin {
    type: average
    sql: ${margin} ;;
    label: "Average Margin"
    description: "Mean gross margin per product"
    value_format_name: usd
  }

  measure: count_active {
    type: count
    filters: [is_active: "yes"]
    label: "Active Products"
    description: "Count of products currently available for purchase"
  }

  measure: total_catalog_value {
    type: sum
    sql: ${price} ;;
    label: "Total Catalog Value"
    description: "Sum of list prices across all products (not weighted by volume)"
    value_format_name: usd
  }

  # ── Sets ─────────────────────────────────────────────────────────────────────
  set: product_fields {
    fields: [
      id,
      sku,
      name,
      category,
      subcategory,
      brand,
      price,
      cost,
      margin,
      is_active,
      count
    ]
  }

  set: product_catalog_export {
    fields: [
      id,
      sku,
      name,
      category,
      brand,
      price,
      is_active
    ]
  }
}
