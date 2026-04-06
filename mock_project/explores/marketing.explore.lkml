include: "/views/marketing/*.view.lkml"
include: "/views/finance/*.view.lkml"
include: "/views/product/*.view.lkml"

explore: marketing_performance {
  from: campaigns
  view_name: campaigns

  join: ad_spend {
    type: left_outer
    relationship: one_to_many
    sql_on: ${campaigns.id} = ${ad_spend.campaign_id} ;;
  }

  # Intentional error: Missing sql_on or sql_where condition entirely
  join: products {
    type: cross
    relationship: many_to_many
  }
}

explore: accounting {
  from: invoices
  view_name: invoices
  label: "Finance Accounting"

  # Intentional: sql_where join instead of sql_on
  join: campaigns {
    type: left_outer
    relationship: many_to_one
    sql_where: ${invoices.amount} > 1000 ;;
  }
}

explore: product_inventory {
  from: products
  view_name: products

  join: inventory_items {
    type: left_outer
    relationship: one_to_many
    sql_on: ${products.id} = ${inventory_items.product_id} ;;
  }
}
