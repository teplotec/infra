# TEPLOTEC CRM-Origin Sales Pilot

This pilot is disposable transactional data used to exercise the canonical TEPLOTEC sales-to-execution spine with Frappe CRM as the sales source of truth.

It is deliberately **not** executed from `after_migrate`. Deploying application code must not silently create Leads, Deals, Customers, Quotations, Sales Orders, or Projects.

## Canonical scenario

```text
Frappe CRM Lead: Оксана Бондар
  -> Frappe CRM Deal: Qualification
     -> CRM Product linked from ERPNext Item
  -> ERPNext Quotation against CRM Deal
  -> ERPNext Sales Order
     -> Customer created/attached by the upstream Frappe CRM integration
  -> ERPNext Project: Customer Installation
```

The pilot creates one disposable ERPNext service Item:

```text
PILOT-SVC-GEO-HP-INSTALL
```

with a test rate of `310000 UAH`.

Because same-site Frappe CRM integration is enabled, the ERPNext Item must automatically produce a linked `CRM Product`. The reverse CRM Product -> ERPNext Item direction remains disabled, so ERPNext stays the operational product master.

## Source-of-truth boundary

The pilot must not create an ERPNext `Lead` or `Opportunity`.

Frappe CRM owns:

- CRM Lead
- CRM Deal
- pipeline status
- sales ownership and activity

ERPNext owns downstream execution:

- Item
- Quotation
- Customer
- Sales Order
- Project
- later Stock, Buying, Accounting, Assets, and Service

The integration boundary is carried by the upstream Frappe CRM / ERPNext fields such as `Quotation.crm_deal`, `Customer.crm_deal`, `CRM Product.erpnext_item_code`, and `Item.crm_product_code`.

## Why this matters

The previous pilot originated in ERPNext Lead / Opportunity and only proved the downstream ERPNext spine. It has now been replaced because that model contradicted the decision to make Frappe CRM authoritative for TEPLOTEC sales.

The canonical pilot intentionally uses the supported upstream same-site integration instead of implementing a parallel TEPLOTEC CRM-to-ERP bridge. TEPLOTEC code only adds its downstream business classification, currently `Residential Customers` and `Customer Installation`.

## CI

Pull-request image CI runs the pilot twice on a fresh Ukrainian-first site and then verifies it. Running it twice proves the dedicated fixture is resumable/idempotent.

Verification includes:

- ERPNext Item -> CRM Product link in both directions
- CRM Lead -> CRM Deal
- CRM Deal product backed by the ERPNext Item
- Quotation directly against `CRM Deal`
- Customer linked back to the CRM Deal
- submitted Sales Order linked to the Quotation
- Customer Installation Project linked to the Sales Order
- absence of a duplicate ERPNext Lead for the CRM-origin scenario

## Production-like site

The manual `ERP Pilot` workflow can create and verify this disposable scenario explicitly on CX33. It must not become part of normal migrations, deploys, reset, or disaster-recovery restore behavior.

## What we discover next

This pilot is the boundary test for deciding which TEPLOTEC-specific concepts deserve first-class modeling. Candidate concepts include:

- physical customer object / site
- building parameters
- heat-loss calculation inputs
- site survey
- drilling scope and boreholes
- engineering artifacts
- installation stages
- commissioning
- service lifecycle

We should add those concepts only when the real sales-to-execution flow proves that standard CRM/ERPNext fields are insufficient.
