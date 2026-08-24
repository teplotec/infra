# TeploTEC CRM / Sales v1

CRM / Sales v1 establishes the first TEPLOTEC sales-to-execution boundary without introducing custom DocTypes.

The intent is to prove the standard Frappe CRM + ERPNext model before adding TEPLOTEC-specific entities.

## Canonical flow

```text
Frappe CRM Lead
  -> Frappe CRM Deal
     -> ERPNext Quotation
     -> ERPNext Customer
     -> ERPNext Sales Order
     -> ERPNext Project
```

Frappe CRM owns sales pipeline state. ERPNext owns operational execution once a Deal starts producing quotations, orders, projects, stock, purchasing, accounting, assets, or service work.

ERPNext `Lead` and `Opportunity` remain installed for upstream compatibility, but they are not authoritative TEPLOTEC sales records and must not be duplicated for the normal CRM-origin flow.

## Product ownership

ERPNext is the operational product master.

In same-site integration mode, an ERPNext Item is represented in Frappe CRM by a linked `CRM Product`:

```text
ERPNext Item
  <-> CRM Product
```

The link is maintained through `Item.crm_product_code` and `CRM Product.erpnext_item_code`.

Reverse CRM Product -> ERPNext Item synchronization remains disabled initially so CRM does not become an independent product master.

## ERPNext compatibility taxonomy

TeploTEC still maintains a small set of ERPNext Sales Stages, Opportunity Types, and Lost Reasons. These records are retained for compatibility and for any exceptional ERPNext-native workflows, not as the canonical TEPLOTEC CRM pipeline.

### Sales stages

- `New Inquiry`
- `Qualified`
- `Site Survey`
- `Solution Design`
- `Quotation`
- `Negotiation`

### Opportunity types

- `Heat Pump Installation`
- `Modernization`
- `Service & Maintenance`
- `Engineering & Design`

### Opportunity lost reasons

- `Price`
- `Timing`
- `Competitor`
- `Technical Fit`
- `Financing`
- `No Response`
- `Project Cancelled`

These should not be expanded until we have a concrete ERPNext-native use case for them. Normal pipeline stages and loss reasons belong in Frappe CRM.

## Project types

The first ERPNext execution classifications remain:

- `Customer Installation`
- `Customer Service`
- `Engineering`

These reuse ERPNext Project rather than creating a TEPLOTEC Project DocType.

## Selling defaults

CRM / Sales v1 keeps standard ERPNext transaction behavior and pins only a small deterministic baseline:

- Customer Naming By: `Customer Name`
- Default Territory: `Ukraine`
- Sales Order required before downstream documents: `No`
- Delivery Note required before Sales Invoice: `No`
- Sales update frequency: `Each Transaction`
- Same Item may appear multiple times in a transaction: enabled

Customer Group is deliberately not defaulted because TEPLOTEC serves residential, commercial, and public-sector customers and should classify each Customer explicitly during handoff.

## What is deliberately not customized yet

- no custom CRM Lead or CRM Deal fields
- no custom Site/Object DocType
- no custom sales workflow engine
- no automatic Deal-status -> Customer rule
- no custom CRM-to-ERP bridge
- no production pricing model or Price Lists
- no Ukrainian tax rules
- no quotation print format
- no per-project warehouse creation
- no drilling, installation, commissioning, or service execution workflow

Those should be introduced only after the canonical CRM Lead -> CRM Deal -> Quotation -> Sales Order -> Project path exposes a real business-model gap.
