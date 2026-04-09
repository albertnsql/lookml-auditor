# warehouses.view.lkml
# Warehouse / fulfilment centre reference data.

view: warehouses {
  sql_table_name: `product.warehouses` ;;

  # ── Primary Key ─────────────────────────────────────────────────────────────
  dimension: id {
    primary_key: yes
    type: number
    sql: ${TABLE}.id ;;
    label: "Warehouse ID"
    description: "Unique identifier for the warehouse"
  }

  # ── Dimensions ───────────────────────────────────────────────────────────────
  dimension: name {
    type: string
    sql: ${TABLE}.name ;;
    label: "Warehouse Name"
    description: "Human-readable name of the warehouse or fulfilment centre"
  }

  dimension: code {
    type: string
    sql: ${TABLE}.code ;;
    label: "Warehouse Code"
    description: "Short code used internally to identify the warehouse (e.g. SFO-01)"
  }

  dimension: region {
    type: string
    sql: ${TABLE}.region ;;
    label: "Region"
    description: "Geographic region: NA, EU, APAC, LATAM"
  }

  dimension: country {
    type: string
    sql: ${TABLE}.country ;;
    label: "Country"
    description: "Country where the warehouse is located"
    map_layer_name: countries
  }

  dimension: city {
    type: string
    sql: ${TABLE}.city ;;
    label: "City"
    description: "City where the warehouse is located"
  }

  dimension: capacity_units {
    type: number
    sql: ${TABLE}.capacity_units ;;
    label: "Capacity (units)"
    description: "Maximum storage capacity in units"
  }

  dimension: is_active {
    type: yesno
    sql: ${TABLE}.is_active ;;
    label: "Is Active"
    description: "Whether the warehouse is currently operational"
  }

  dimension: is_primary {
    type: yesno
    sql: ${TABLE}.is_primary ;;
    label: "Is Primary"
    description: "Whether this is the primary fulfilment warehouse for its region"
  }

  dimension: operator {
    type: string
    sql: ${TABLE}.operator ;;
    label: "Operator"
    description: "Company operating the warehouse (in-house or 3PL provider)"
  }

  # ── Dimension Groups ─────────────────────────────────────────────────────────
  dimension_group: opened {
    type: time
    timeframes: [raw, date, month, year]
    sql: ${TABLE}.opened_at ;;
    label: "Opened"
    description: "When the warehouse began operations"
    datatype: date
  }

  # ── Measures ─────────────────────────────────────────────────────────────────
  measure: count {
    type: count
    label: "Warehouse Count"
    description: "Total number of warehouses"
  }

  measure: count_active {
    type: count
    filters: [is_active: "yes"]
    label: "Active Warehouses"
    description: "Count of currently operational warehouses"
  }

  measure: total_capacity {
    type: sum
    sql: ${capacity_units} ;;
    label: "Total Capacity (units)"
    description: "Sum of storage capacity across all warehouses"
  }

  measure: avg_capacity {
    type: average
    sql: ${capacity_units} ;;
    label: "Average Capacity"
    description: "Mean storage capacity per warehouse"
  }
}
