# TeploTEC ERP Master Data v1

Master Data v1 is the first version-controlled business baseline layered on top of the standard ERPNext setup wizard data.

It intentionally contains structure, not real customers, suppliers, items, projects, prices, or transactions.

## Lifecycle

`teplotec_erp.install.after_migrate` applies the baseline after the TeploTEC company exists. Before the setup wizard creates `TEPLOTEC`, the hook safely skips the company-specific bootstrap.

This means a fresh `ERP Reset` follows the same path as CI:

```text
ERPNext reinstall
  -> setup wizard creates TEPLOTEC / TTEC
  -> migrate
  -> teplotec_erp after_migrate
  -> Master Data v1
  -> diagnostic verification
```

The managed structure is idempotent. Missing managed records are created. Existing managed tree nodes with a different parent or group/leaf type are treated as configuration drift and fail loudly instead of being silently rewritten.

## Company and stock defaults

The baseline expects the version-controlled setup profile to have already created:

- Company: `TEPLOTEC`
- Abbreviation: `TTEC`
- Currency: `UAH`
- Timezone: `Europe/Kyiv`

Stock defaults are kept intentionally simple:

- Item Naming By: `Item Code`
- Default Stock UOM: `Nos`
- Default Warehouse: `Stores - TTEC`

ERPNext already creates the standard company warehouses. TeploTEC uses them rather than creating duplicates:

- Main warehouse: `Stores - TTEC`
- In transit: `Goods In Transit - TTEC`
- Project/site parent: `Project Sites - TTEC` - added by TeploTEC as a group warehouse

Individual project-site warehouses will be created later when the project model is defined.

## Item Groups

```text
All Item Groups
└── TeploTEC
    ├── TeploTEC Equipment
    │   ├── Heat Pumps
    │   └── Controls & Automation
    ├── Geothermal Systems
    │   ├── Ground Loops
    │   ├── Pipes & Fittings
    │   ├── Manifolds
    │   └── Heat Transfer Fluids
    ├── HVAC & Hydronics
    ├── TeploTEC Consumables
    ├── TeploTEC Tools
    └── TeploTEC Services
        ├── Design Services
        ├── Drilling Services
        ├── Installation Services
        ├── Commissioning Services
        └── Maintenance Services
```

The generic ERPNext groups such as `Products`, `Raw Material`, `Services`, `Sub Assemblies`, and `Consumable` remain untouched.

## Customer Groups

```text
All Customer Groups
└── TeploTEC Customers
    ├── Residential Customers
    ├── Commercial Customers
    └── Public Sector Customers
```

The standard ERPNext customer groups remain available.

## Supplier Groups

```text
All Supplier Groups
└── TeploTEC Suppliers
    ├── Equipment Suppliers
    ├── Material Suppliers
    └── Service Contractors
```

## Required UOMs

Master Data v1 guarantees that the basic UOM records needed for early catalog work exist:

- `Nos`
- `Meter`
- `Kilogram`
- `Litre`
- `Hour`

ERPNext normally creates these during setup; TeploTEC only fills a missing record rather than maintaining a parallel UOM vocabulary.

## Explicitly deferred

Master Data v1 does not yet define:

- real Items or Item Codes
- item naming taxonomy beyond `Item Code`
- warehouse `ROW -> RACK -> LEVEL -> BIN` locations
- customers or suppliers
- projects or project-site warehouse instances
- price lists
- taxes or Ukrainian accounting localization
- serial/batch rules
- service workflow
- drilling workflow
- purchasing or sales workflow customizations

Those should be introduced as separate vertical slices after this baseline is proven on the fresh TeploTEC site.
