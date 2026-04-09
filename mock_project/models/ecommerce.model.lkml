# ecommerce.model.lkml
# Primary transactional model covering orders, customers, products, and payments.
# Owned by: Data Platform Team
# Last reviewed: 2024-01-15

connection: "production_warehouse"

# ── Datagroups ───────────────────────────────────────────────────────────────
include: "/datagroups/caching_policies.lkml"

# ── Core Views ───────────────────────────────────────────────────────────────
include: "/views/orders.view.lkml"
include: "/views/customers.view.lkml"
include: "/views/order_items.view.lkml"
include: "/views/payments.view.lkml"
include: "/views/orders_summary.view.lkml"
include: "/views/customers_dup.view.lkml"
include: "/views/customers_pii.view.lkml"
include: "/views/users.view.lkml"
include: "/views/refunds.view.lkml"
include: "/views/returns.view.lkml"
include: "/views/customer_lifetime_value.view.lkml"
include: "/views/staging_temp.view.lkml"

# ── Product Views ─────────────────────────────────────────────────────────────
include: "/views/product/products.view.lkml"
include: "/views/product/inventory_items.view.lkml"
include: "/views/product/warehouses.view.lkml"
include: "/views/product/product_metrics.view.lkml"

# ── Refinements ───────────────────────────────────────────────────────────────
include: "/refinements/orders.refine.lkml"

# ── Explores ─────────────────────────────────────────────────────────────────
include: "/explores/core.explore.lkml"

# Model-level settings
fiscal_month_offset: 0
week_start_day: monday

label: "E-Commerce Analytics"
