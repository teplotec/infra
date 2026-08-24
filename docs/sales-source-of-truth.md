# TEPLOTEC Sales Source of Truth

Frappe CRM is the source of truth for the TEPLOTEC sales process.

## Ownership

```text
Frappe CRM
  CRM Lead
  CRM Deal
  CRM Organization
  Contact
  sales ownership
  pipeline stage
  deal status
  sales activity
        |
        | downstream handoff
        v
ERPNext
  Customer
  Quotation
  Sales Order
  Project
  Item / pricing execution
  Stock
  Buying
  Accounting
  Assets / service execution
```

A Lead or Deal must not be recreated as an ERPNext Lead or Opportunity for the normal TEPLOTEC sales flow. ERPNext Lead and Opportunity can remain available for compatibility, but they are not authoritative TEPLOTEC sales records.

## Same-site integration

Frappe CRM and ERPNext are installed on the same Frappe site. The managed `ERPNext CRM Settings` configuration is:

- integration enabled;
- ERPNext company `TEPLOTEC`;
- same-site mode;
- automatic Customer creation on Deal status change disabled initially;
- reverse CRM Product -> ERPNext Item synchronization disabled initially.

ERPNext remains the operational product master for Items, stock, purchasing, and accounting. In same-site mode an ERPNext Item is still represented in CRM as a linked `CRM Product`; disabling `sync_products` prevents CRM Products from becoming an independent upstream Item master.

## Initial handoff policy

The controlled flow is:

```text
CRM Lead
  -> CRM Deal
     -> CRM Product backed by ERPNext Item
     -> ERPNext Quotation against CRM Deal
     -> ERPNext Sales Order
        -> ERPNext Customer created/attached through the upstream integration
     -> ERPNext Project
```

Customer creation is not tied to an automatic Deal-status transition yet. The upstream integration creates or resolves the Customer when the Deal crosses into ERPNext execution through the Quotation / Sales Order flow. We can later enable `Create customer on status change` once a stable TEPLOTEC qualification or winning policy is agreed.

## Deployment contract

The immutable ERP image contains all three applications:

- ERPNext `v16.31.1`;
- Frappe CRM `v1.81.0`;
- `teplotec_erp`.

`teplotec_erp` requires both `erpnext` and `crm`. Production deploy installs missing required apps before migration, then `after_migrate` applies the same-site CRM integration settings and verifies the integration contract in CI.

## Canonical pilot

The disposable transactional pilot now originates in `CRM Lead` / `CRM Deal`. It verifies the supported same-site Frappe CRM / ERPNext bridge instead of maintaining a parallel TEPLOTEC integration.

The pilot proves:

- ERPNext Item -> CRM Product linkage;
- CRM Lead -> CRM Deal;
- CRM Deal -> Quotation;
- Quotation -> Sales Order;
- CRM Deal -> Customer linkage during downstream execution;
- Sales Order -> Customer Installation Project;
- no duplicate ERPNext Lead is created for the CRM-origin scenario.

See `docs/erp-pilot-scenario.md` for the exact disposable fixture.

## Next validation

After the CI pilot is green, validate the same path manually in `/crm` and use the resulting friction to discover TEPLOTEC-specific domain concepts. We should introduce concepts such as customer Object/Site, building parameters, site survey, drilling scope, installation, commissioning, and service only when the real workflow shows that standard CRM/ERPNext fields are insufficient.
