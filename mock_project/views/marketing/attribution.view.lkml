# attribution.view.lkml
# Multi-touch attribution PDT — assigns credit to marketing touchpoints.
# Uses datagroup_trigger for daily persistence.

view: attribution {
  derived_table: {
    datagroup_trigger: daily_refresh
    sql:
      WITH touchpoints AS (
        SELECT
          e.customer_id,
          e.campaign_id,
          e.channel,
          e.touched_at,
          o.id                                                              AS order_id,
          o.amount                                                          AS order_amount,
          ROW_NUMBER() OVER (
            PARTITION BY e.customer_id, o.id
            ORDER BY e.touched_at
          )                                                                 AS touch_rank,
          COUNT(*) OVER (
            PARTITION BY e.customer_id, o.id
          )                                                                 AS total_touches
        FROM marketing.attribution_events e
        INNER JOIN public.orders o
          ON e.customer_id = o.customer_id
          AND e.touched_at < o.created_at
          AND DATEDIFF(day, e.touched_at, o.created_at) <= 30
        WHERE e.touched_at >= DATEADD(day, -365, CURRENT_DATE)
      )
      SELECT
        campaign_id,
        channel,
        customer_id,
        order_id,
        touch_rank,
        total_touches,
        touched_at,
        order_amount,
        -- Linear attribution: divide credit equally among all touches
        order_amount / NULLIF(total_touches, 0)                           AS linear_credit,
        -- First-touch: full credit to first touch
        CASE WHEN touch_rank = 1 THEN order_amount ELSE 0 END            AS first_touch_credit,
        -- Last-touch: full credit to last touch
        CASE WHEN touch_rank = total_touches THEN order_amount ELSE 0 END AS last_touch_credit
      FROM touchpoints
    ;;
  }

  # ── Primary Key ─────────────────────────────────────────────────────────────
  dimension: pk {
    type: string
    sql: CONCAT(${TABLE}.customer_id, '-', ${TABLE}.campaign_id, '-', ${TABLE}.order_id, '-', ${TABLE}.touch_rank) ;;
    primary_key: yes
    hidden: yes
    description: "Synthetic composite primary key for attribution records"
  }

  dimension: campaign_id {
    type: string
    sql: ${TABLE}.campaign_id ;;
    label: "Campaign ID"
    description: "Campaign that contributed this touchpoint"
    hidden: yes
  }

  dimension: customer_id {
    type: number
    sql: ${TABLE}.customer_id ;;
    label: "Customer ID"
    description: "Customer attributed to this touchpoint"
    hidden: yes
  }

  dimension: order_id {
    type: number
    sql: ${TABLE}.order_id ;;
    label: "Order ID"
    description: "Order being attributed"
    hidden: yes
  }

  dimension: channel {
    type: string
    sql: ${TABLE}.channel ;;
    label: "Attribution Channel"
    description: "Marketing channel of the touchpoint"
  }

  dimension: touch_rank {
    type: number
    sql: ${TABLE}.touch_rank ;;
    label: "Touch Rank"
    description: "Position of this touchpoint in the customer journey (1 = first)"
  }

  dimension: total_touches {
    type: number
    sql: ${TABLE}.total_touches ;;
    label: "Total Touches"
    description: "Total number of touchpoints before the order"
  }

  dimension_group: touched {
    type: time
    timeframes: [raw, date, week, month]
    sql: ${TABLE}.touched_at ;;
    label: "Touch"
    description: "When the marketing touchpoint occurred"
    datatype: timestamp
  }

  # ── Measures ─────────────────────────────────────────────────────────────────
  measure: total_linear_credit {
    type: sum
    sql: ${TABLE}.linear_credit ;;
    label: "Linear Attribution Revenue"
    description: "Revenue credited using linear (equal-weight) attribution"
    value_format_name: usd
  }

  measure: total_first_touch_credit {
    type: sum
    sql: ${TABLE}.first_touch_credit ;;
    label: "First-Touch Attribution Revenue"
    description: "Revenue credited to the first marketing touchpoint"
    value_format_name: usd
  }

  measure: total_last_touch_credit {
    type: sum
    sql: ${TABLE}.last_touch_credit ;;
    label: "Last-Touch Attribution Revenue"
    description: "Revenue credited to the last marketing touchpoint before conversion"
    value_format_name: usd
  }

  measure: count_attributed_orders {
    type: count_distinct
    sql: ${order_id} ;;
    label: "Attributed Orders"
    description: "Count of orders with at least one marketing touchpoint"
  }

  measure: count_touchpoints {
    type: count
    label: "Touchpoint Count"
    description: "Total number of marketing touchpoints recorded"
  }

  measure: avg_touches_per_order {
    type: average
    sql: ${total_touches} ;;
    label: "Avg Touches per Order"
    description: "Average number of marketing touches before a conversion"
    value_format_name: decimal_1
  }
}
