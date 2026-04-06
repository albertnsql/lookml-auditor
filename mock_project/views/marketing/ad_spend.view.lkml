view: ad_spend {
  derived_table: {
    sql:
      SELECT
        campaign_id,
        date,
        spend,
        clicks,
        impressions
      FROM marketing.ad_spend
      WHERE spend > 0
    ;;
  }

  dimension: campaign_id {
    type: string
    hidden: yes
    sql: ${TABLE}.campaign_id ;;
  }

  dimension: date {
    type: date
    sql: ${TABLE}.date ;;
  }

  measure: total_spend {
    type: sum
    sql: ${TABLE}.spend ;;
  }

  measure: count {
    type: count
    description: "Count of spend records"
  }
}
