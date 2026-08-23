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
- automatic Customer creation disabled initially;
- bidirectional Product sync disabled initially.

The last setting is deliberate. Frappe CRM owns sales, but ERPNext remains the operational product master for Items, stock, purchasing, and accounting. CRM Products are integration-facing sales representations of ERPNext Items rather than an independent product master.

## Initial handoff policy

The first controlled flow is:

```text
CRM Lead
  -> CRM Deal
     -> ERPNext Customer when qualification requires it
     -> ERPNext Quotation
     -> ERPNext Sales Order
     -> ERPNext Project
```

Customer creation stays explicit until the exact TEPLOTEC deal-status policy is agreed and tested. We can later enable Frappe CRM's `Create customer on status change` integration once a stable winning/qualification status is defined.

## Deployment contract

The immutable ERP image contains all three applications:

- ERPNext `v16.31.1`;
- Frappe CRM `v1.80.0`;
- `teplotec_erp`.

`teplotec_erp` requires both `erpnext` and `crm`. Production deploy installs missing required apps before migration, then `after_migrate` applies the same-site CRM integration settings and verifies the integration contract in CI.

## Next validation

After deployment, open `/crm` and validate the sales flow in the Frappe CRM UI. The next transactional pilot should originate in `CRM Lead` / `CRM Deal`, not in ERPNext Lead / Opportunity. The existing ERPNext pilot is retained only as a downstream compatibility baseline until the CRM-origin pilot replaces it.
