# ad_spend.view.lkml
# Marketing ad spend PDT with performance metrics.
# INTENTIONAL ISSUES:
#   - Uses deprecated sql_trigger_value for persistence
#   - No primary key
#   - campaign_id is hidden but used in explore joins

view: ad_spend {
  derived_table: {
    # INTENTIONAL ISSUE: sql_trigger_value is deprecated — should use datagroup_trigger
    sql_trigger_value: SELECT FLOOR(EXTRACT(EPOCH FROM NOW()) / 3600) ;;
    sql:
      SELECT
        a.campaign_id,
        DATE_TRUNC('day', a.spend_date)                       AS spend_date,
        a.channel,
        a.ad_group,
        SUM(a.spend)                                          AS total_spend,
        SUM(a.clicks)                                         AS total_clicks,
        SUM(a.impressions)                                    AS total_impressions,
        SUM(a.conversions)                                    AS total_conversions,
        SUM(a.revenue)                                        AS attributed_revenue,
        COUNT(DISTINCT a.ad_id)                               AS active_ads
      FROM marketing.ad_spend a
      INNER JOIN marketing.campaigns c
        ON a.campaign_id = c.id
        AND c.status != 'cancelled'
      WHERE a.spend_date >= DATEADD(day, -365, CURRENT_DATE)
        AND a.spend > 0
      GROUP BY 1, 2, 3, 4
    ;;
  }

  # INTENTIONAL ISSUE: hidden field (campaign_id) used as join key in explore
  dimension: campaign_id {
    type: string
    hidden: yes
    sql: ${TABLE}.campaign_id ;;
    description: "Campaign ID — hidden but used as join key"
  }

  # INTENTIONAL ISSUE: no primary key defined
  dimension: spend_date {
    type: date
    sql: ${TABLE}.spend_date ;;
    label: "Spend Date"
    description: "Date of the ad spend record"
  }

  dimension: channel {
    type: string
    sql: ${TABLE}.channel ;;
    label: "Ad Channel"
    description: "Channel for this spend record: Google, Facebook, TikTok, etc."
  }

  dimension: ad_group {
    type: string
    sql: ${TABLE}.ad_group ;;
    label: "Ad Group"
    description: "Ad group name within the campaign"
  }

  dimension: active_ads {
    type: number
    sql: ${TABLE}.active_ads ;;
    label: "Active Ads"
    description: "Count of distinct ads running on this date"
  }

  # ── Measures ─────────────────────────────────────────────────────────────────
  measure: total_spend {
    type: sum
    sql: ${TABLE}.total_spend ;;
    label: "Total Ad Spend"
    description: "Sum of all ad spend across campaigns"
    value_format_name: usd
  }

  measure: total_clicks {
    type: sum
    sql: ${TABLE}.total_clicks ;;
    label: "Total Clicks"
    description: "Sum of all clicks from ads"
  }

  measure: total_impressions {
    type: sum
    sql: ${TABLE}.total_impressions ;;
    label: "Total Impressions"
    description: "Sum of all ad impressions"
  }

  measure: total_conversions {
    type: sum
    sql: ${TABLE}.total_conversions ;;
    label: "Total Conversions"
    description: "Sum of attributed conversions"
  }

  measure: attributed_revenue {
    type: sum
    sql: ${TABLE}.attributed_revenue ;;
    label: "Attributed Revenue"
    description: "Revenue attributed to paid ads"
    value_format_name: usd
  }

  measure: ctr {
    type: number
    sql: ${total_clicks} / NULLIF(${total_impressions}, 0) ;;
    label: "CTR"
    description: "Click-through rate (clicks / impressions)"
    value_format_name: percent_4
  }

  measure: cpc {
    type: number
    sql: ${total_spend} / NULLIF(${total_clicks}, 0) ;;
    label: "CPC"
    description: "Cost per click"
    value_format_name: usd
  }

  measure: roas {
    type: number
    sql: ${attributed_revenue} / NULLIF(${total_spend}, 0) ;;
    label: "ROAS"
    description: "Return on ad spend (attributed revenue / spend)"
    value_format_name: decimal_2
  }

  measure: count {
    type: count
    label: "Spend Record Count"
    description: "Count of spend records in this PDT"
  }
}
