# TEPLOTEC Sales Qualification v1

## Purpose

This slice is intentionally exploratory. It adds a small qualification layer to `CRM Deal` so TEPLOTEC can learn which technical and site facts are actually required before Quotation.

It does **not** introduce a new Site, Building, Installation, Survey, or Engineering DocType. Those boundaries should be created only after repeated real workflows prove that the data needs an independent lifecycle.

## Source of truth

Frappe CRM remains the sales source of truth. Qualification fields live on `CRM Deal` while the opportunity is being qualified.

The canonical sales handoff stays:

```text
CRM Lead
  -> CRM Deal + TEPLOTEC qualification
  -> ERPNext Quotation
  -> Sales Order
  -> Customer
  -> Project
```

## Exploratory fields

The first version manages these custom fields on `CRM Deal`:

- object type
- object location
- heated area, m²
- existing heat source
- estimated heat loss, kW
- requested system
- drilling feasibility
- site survey status
- target commissioning date

All fieldnames use the `teplotec_` prefix. Labels are Ukrainian-first because these are TEPLOTEC-owned UI fields rather than upstream Frappe CRM strings.

Select values are deliberately simple. They may be renamed, split, replaced by Link fields, or removed while the sales model is being learned.

## Demo data

`teplotec_erp/data/sales_qualification_demo_v1.json` is a version-controlled overlay on top of the existing CRM demo dataset.

It currently covers eight representative deals across:

- private houses
- multi-unit residential
- public sector
- agriculture
- commercial property

The overlay is separate from `crm_demo_v1.json` so the core CRM demo scenarios remain readable while technical qualification can evolve quickly.

The manual demo seed applies the overlay idempotently and verification checks every version-controlled qualification value.

## Design rule

Do not promote an exploratory field into a new domain entity because it looks architecturally clean.

Promote it only when real workflow proves one or more of these conditions:

1. the data must survive beyond the Deal lifecycle;
2. multiple Deals can reference the same physical object;
3. survey, engineering, installation, and service need the same object independently;
4. the object needs its own history, documents, photos, measurements, or permissions;
5. the same data is repeatedly duplicated across CRM, Project, service, or maintenance records.

That evidence will drive the next Site/Object and Site Survey slices.
