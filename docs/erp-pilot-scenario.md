# TEPLOTEC ERPNext Downstream Pilot

This pilot is disposable transactional data used to exercise the standard ERPNext execution spine. It predates the decision to make Frappe CRM the TEPLOTEC sales source of truth and is now retained only as a downstream compatibility baseline.

It is deliberately **not** executed from `after_migrate`. Deploying application code must not silently create Leads, Customers, Quotations, Sales Orders, or Projects.

## Baseline scenario

```text
ERPNext Lead: Іван Петренко
  -> ERPNext Opportunity: Heat Pump Installation
     -> Sales Stage: Site Survey
  -> Quotation
  -> Customer: Residential Customers
  -> Sales Order
  -> Project: Customer Installation
```

The pilot also creates one disposable service Item:

```text
PILOT-SVC-HP-INSTALL
```

with a test rate of `250000 UAH`.

## Why it remains

Frappe CRM now owns TEPLOTEC Leads, Deals, Organizations, Contacts, and pipeline state. The normal sales flow must therefore originate in `CRM Lead` / `CRM Deal`, not ERPNext Lead / Opportunity.

This older pilot remains useful temporarily because it proves that the ERPNext downstream objects and mappings still work. It will be replaced by a CRM-origin pilot that hands a `CRM Deal` into ERPNext Customer, Quotation, Sales Order, and Project.

## CI

Pull-request image CI runs this baseline twice on the fresh Ukrainian-first site and then verifies it. Running it twice proves the helper is resumable/idempotent for the same dedicated pilot customer.

Frappe CRM installation and same-site ERPNext integration are verified separately by the TEPLOTEC bootstrap diagnostics.

## Production-like site

The manual `ERP Pilot` workflow can create and verify this baseline explicitly on CX33. It must not become part of normal migrations or disaster-recovery restore behavior.

## Next pilot

The canonical TEPLOTEC sales pilot is the next slice:

```text
CRM Lead
  -> CRM Deal
     -> ERPNext Customer
     -> ERPNext Quotation
     -> ERPNext Sales Order
     -> ERPNext Project
```

That pilot will be used to discover TEPLOTEC-specific concepts such as the physical customer object/site, building parameters, heat-loss inputs, site survey, drilling scope, engineering artifacts, installation, commissioning, and service lifecycle.
