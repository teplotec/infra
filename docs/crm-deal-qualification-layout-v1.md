# TEPLOTEC CRM Deal qualification layout v1

## Purpose

Frappe CRM stores visible Deal fields in `CRM Fields Layout` records. Creating a Frappe `Custom Field` does not guarantee that the field appears in an already persisted CRM layout.

TEPLOTEC therefore manages a small additive layout contract for the qualification fields introduced in Sales Qualification v1.

## Managed surfaces

### Data Fields

The main Deal data area contains the complete qualification set:

- Тип об'єкта
- Локація об'єкта
- Опалювана площа, м²
- Поточне джерело тепла
- Орієнтовні тепловтрати, кВт
- Бажана система
- Можливість буріння
- Статус обстеження об'єкта
- Бажана дата запуску

### Side Panel

The Deal side panel contains the compact high-frequency subset:

- Тип об'єкта
- Локація об'єкта
- Опалювана площа, м²
- Бажана система
- Можливість буріння
- Статус обстеження об'єкта

### Quick Entry

TEPLOTEC does not add technical qualification fields to Deal Quick Entry. A salesperson should be able to create a Deal quickly and qualify it afterwards.

## Ownership rule

The TEPLOTEC section has the stable name `teplotec_qualification_section`.

The bootstrap may create or update that managed section, but it must preserve unrelated Frappe CRM and user-defined sections. It does not replace the entire `CRM Deal-Data Fields` or `CRM Deal-Side Panel` layout.

This lets us evolve the exploratory qualification model without forking Frappe CRM or taking ownership of the whole CRM UI configuration.

## Migration order

On `after_migrate`:

1. create or update TEPLOTEC qualification Custom Fields;
2. add/update the managed qualification layout sections;
3. verify the managed section labels and field ordering;
4. continue with the same-site Frappe CRM / ERPNext integration bootstrap.

## Next domain decision

Do not introduce `Site`, `Building`, `Installation`, or `Site Survey` DocTypes merely because qualification data exists.

First use the Deal qualification UI with representative demo and real sales scenarios. Promote a concept into its own DocType only when it needs an independent lifecycle, repeated relationships, history, or reuse outside one Deal.
