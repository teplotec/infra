# Reproducible ERP reset

During the initial implementation phase, `erp.teplotec.com` is intentionally treated as a resettable production-like environment.

## Setup profile

`config/erp-setup.json` is the source of truth for the Setup Wizard values:

- language: Українська (`uk`), provided by the TeploTEC ERP app before the setup profile is applied
- country: Ukraine
- timezone: Europe/Kyiv
- currency: UAH
- company: TEPLOTEC
- abbreviation: TEC
- chart of accounts: Standard with Numbers
- financial year: January 1 through December 31, calculated from the current year
- demo data: disabled
- telemetry: disabled

The profile deliberately contains no passwords.

Pull-request CI applies the same profile to a disposable fresh ERPNext site and verifies that the resulting system language is `uk`, the Ukraine/Kyiv/UAH defaults are active, and the TEPLOTEC company exists.

## Reset workflow

`Actions -> ERP Reset` is destructive. It requires the exact confirmation text:

```text
RESET ERP
```

The workflow runs only on the CX33 self-hosted admin runner. It reads the desired Administrator password from the `ERPNEXT_ADMIN_PASSWORD` repository secret and then:

1. runs Frappe `bench reinstall` for `erp.teplotec.com` using the current installed app set, including `teplotec_erp`;
2. recreates the database and the TeploTEC Ukrainian language record through the app install hook;
3. invokes the Frappe v16 setup engine programmatically with `config/erp-setup.json`;
4. verifies the custom app remains installed, clears cache, and runs migrations.

This removes the need to click through the four-page Setup Wizard after every reset and makes Ukrainian the default language of a clean TeploTEC ERP site.

## Safety model

- Terraform infrastructure is not destroyed or recreated.
- Cloudflare Tunnel and Access are untouched.
- The CX33 is untouched.
- The ERP database and site data are destroyed.
- The reset workflow is serialized with other ERP admin operations.
- Reset is appropriate only while this environment is explicitly disposable.

Before real business data is entered, the reset workflow must be disabled or protected with stronger GitHub Environment approvals and backups.

## TeploTEC ERP app

`apps/teplotec_erp` is the TeploTEC Frappe app. Its scope is larger than translation alone:

- Ukrainian language enablement;
- Ukrainian translation overrides;
- TeploTEC terminology;
- Ukrainian accounting and tax localization;
- custom fields and fixtures;
- print formats;
- migration hooks and setup defaults.

The app enables an `uk` Language record named `Українська` with Ukrainian date/number conventions and ships a small translation seed.

The source is currently co-located in `infra`. Frappe Docker requires custom apps to be baked into a custom/layered image, so TeploTEC publishes its own ERPNext image containing `erpnext` and `teplotec_erp` before deploying the app to the production-like site.
