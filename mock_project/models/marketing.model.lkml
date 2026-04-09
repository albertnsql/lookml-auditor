# marketing.model.lkml
# Growth & marketing analytics model covering campaign performance, ad spend,
# attribution, and email engagement.
# Owned by: Growth Analytics Team
# Last reviewed: 2023-11-02

connection: "production_warehouse"

# ── Datagroups ───────────────────────────────────────────────────────────────
include: "/datagroups/caching_policies.lkml"

# ── Marketing Views ───────────────────────────────────────────────────────────
include: "/views/marketing/campaigns.view.lkml"
include: "/views/marketing/ad_spend.view.lkml"
include: "/views/marketing/attribution.view.lkml"
include: "/views/marketing/email_events.view.lkml"

# ── Core Views needed for joins ───────────────────────────────────────────────
include: "/views/customers.view.lkml"
include: "/views/orders.view.lkml"
include: "/views/product/products.view.lkml"

# ── Explores ─────────────────────────────────────────────────────────────────
include: "/explores/marketing.explore.lkml"

# INTENTIONAL ISSUE: references a non-existent explore file
# include: "/explores/growth_funnels.explore.lkml"

label: "Marketing & Growth"
fiscal_month_offset: 0
week_start_day: monday
