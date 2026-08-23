# TeploTEC ERP CRM / Sales v1

CRM / Sales v1 configures the first standard ERPNext sales path for TeploTEC without introducing custom DocTypes.

The intent is to prove the standard ERPNext model before adding TeploTEC-specific entities.

## Standard flow

```text
Lead
  -> Opportunity
  -> Quotation
  -> Sales Order
  -> Project
```

The next vertical slice can attach installation/service execution to the resulting Project.

## Opportunity sales stages

TeploTEC adds stable stages that match the early project-sales cycle:

```text
New Inquiry
  -> Qualified
  -> Site Survey
  -> Solution Design
  -> Quotation
  -> Negotiation
```

ERPNext Opportunity `status` remains authoritative for final lifecycle states such as `Converted`, `Lost`, and `Closed`. We do not duplicate those states as custom workflow logic.

## Opportunity types

- `Heat Pump Installation` - new geothermal or air-source heat pump installation
- `Modernization` - upgrade or replacement of an existing heating/cooling system
- `Service & Maintenance` - diagnostics, repair, maintenance, or commissioning
- `Engineering & Design` - design, audit, calculations, or consulting before implementation

## Lost reasons

The first structured reasons for a lost opportunity are:

- Price
- Timing
- Competitor
- Technical Fit
- Financing
- No Response
- Project Cancelled

These are intentionally small and actionable so the sales funnel can be analysed later without starting with a large taxonomy.

## Project types

- `Customer Installation`
- `Customer Service`
- `Engineering`

These reuse ERPNext Project rather than creating a TeploTEC Project DocType.

## Selling defaults

CRM / Sales v1 keeps standard ERPNext transaction behavior and only pins a small deterministic baseline:

- Customer Naming By: `Customer Name`
- Default Territory: `Ukraine`
- Sales Order required before downstream documents: `No`
- Delivery Note required before Sales Invoice: `No`
- Sales update frequency: `Each Transaction`
- Same Item may appear multiple times in a transaction: enabled

Customer Group is deliberately not defaulted because TeploTEC serves residential, commercial, and public-sector customers and should classify each customer explicitly.

## What is deliberately not customized yet

- no custom Lead or Opportunity fields
- no custom Site/Object DocType
- no custom sales workflow engine
- no automatic Opportunity -> Project conversion hook
- no pricing model or Price Lists
- no Ukrainian tax rules
- no quotation print format
- no per-project warehouse creation
- no drilling, installation, commissioning, or service execution workflow

Those should be introduced only after the standard Lead -> Opportunity -> Quotation -> Sales Order -> Project path is exercised with real TeploTEC scenarios.
