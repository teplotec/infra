# TEPLOTEC CRM Demo Data

TEPLOTEC keeps two intentionally separate kinds of non-production data.

## Exploratory pilot data

`teplotec_erp.pilot` is a small transactional test fixture used by CI and engineering to exercise the ERPNext downstream execution spine. Its purpose is to reveal integration and domain-model gaps. It is disposable and is not intended to look realistic in demonstrations.

## Demo data

`teplotec_erp/data/crm_demo_v1.json` is the curated, version-controlled CRM demo dataset. It exists to make a fresh or reset environment useful immediately for product exploration, UI work, sales-flow design, screenshots, and demonstrations.

The v1 dataset contains 30 synthetic Leads and 23 Deals across B2C, B2B, residential, commercial, and public-sector scenarios. It deliberately covers multiple lead statuses, deal stages, won and lost deals, different organizations, budgets, employee counts, revenue sizes, sources, and next steps.

All demo email addresses use the reserved `teplotec.invalid` domain and all phone numbers are synthetic.

Demo data is never seeded from `after_migrate`, deploy, or reset. A normal production deploy must not create transactional records.

## Restore after reset

After the current immutable ERP image is deployed and the host admin helper is synchronized, run the `ERP Demo Data` workflow from `main` and enter the exact confirmation:

```text
SEED DEMO
```

The workflow calls the restricted `demo-seed` host operation. The importer is idempotent, so it can be run repeatedly to refresh the version-controlled records without creating duplicates.

The same operation can be executed locally on the ERP host through the restricted helper:

```bash
sudo /usr/local/sbin/teplotec-erp-admin demo-seed
```

## Design rule

Demo data can evolve while TEPLOTEC is learning which CRM fields and domain concepts are useful. Once a concept becomes production master data or a real business entity, it must move out of the demo dataset into the appropriate version-controlled master-data or domain migration layer.
