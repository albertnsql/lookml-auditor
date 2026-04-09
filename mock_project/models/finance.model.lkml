# finance.model.lkml
# Finance and billing analytics model covering invoices, revenue rollups,
# and billing account management.
# Owned by: Finance Data Team
# Last reviewed: 2024-02-20

connection: "production_warehouse"

# ── Datagroups ───────────────────────────────────────────────────────────────
include: "/datagroups/caching_policies.lkml"

# ── Finance Views ─────────────────────────────────────────────────────────────
include: "/views/finance/invoices.view.lkml"
include: "/views/finance/billing_accounts.view.lkml"
include: "/views/finance/revenue_rollup.view.lkml"

# ── Shared Core Views ─────────────────────────────────────────────────────────
include: "/views/customers.view.lkml"
include: "/views/orders.view.lkml"
include: "/views/payments.view.lkml"

# ── Marketing Views referenced in finance explores ────────────────────────────
include: "/views/marketing/campaigns.view.lkml"
include: "/views/product/products.view.lkml"
include: "/views/product/inventory_items.view.lkml"

# ── Explores ─────────────────────────────────────────────────────────────────
include: "/explores/finance.explore.lkml"

label: "Finance & Billing"
fiscal_month_offset: 0
week_start_day: sunday
