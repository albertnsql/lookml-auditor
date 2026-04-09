# caching_policies.lkml
# Defines reusable datagroup triggers for PDT persistence across all models.
# Referenced by derived_table blocks using datagroup_trigger parameter.

datagroup: daily_refresh {
  label: "Daily Refresh"
  description: "Triggers a cache rebuild once per day based on ETL pipeline completion"
  sql_trigger: SELECT MAX(updated_at) FROM etl_metadata.pipeline_runs WHERE pipeline = 'daily' ;;
  max_cache_age: "24 hours"
}

datagroup: weekly_refresh {
  label: "Weekly Refresh"
  description: "Triggers a cache rebuild once per week, typically Sunday night"
  sql_trigger: SELECT DATE_TRUNC('week', MAX(updated_at)) FROM etl_metadata.pipeline_runs WHERE pipeline = 'weekly' ;;
  max_cache_age: "168 hours"
}

datagroup: hourly_metrics {
  label: "Hourly Metrics Refresh"
  description: "Used for near-real-time dashboards that require fresh hourly aggregations"
  sql_trigger: SELECT FLOOR(EXTRACT(EPOCH FROM NOW()) / 3600) ;;
  max_cache_age: "2 hours"
}

# INTENTIONAL ISSUE: datagroup with no sql_trigger (only max_cache_age — not recommended)
datagroup: lazy_cache {
  label: "Lazy Cache"
  description: "Fallback cache with no sql_trigger — will never proactively rebuild"
  max_cache_age: "48 hours"
}
