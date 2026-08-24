# Frappe CRM Ukrainian overlay

TEPLOTEC keeps Frappe CRM on an upstream stable release and carries only a small reviewed Ukrainian translation overlay.

Current upstream contract:

- Frappe CRM: `v1.81.0`
- locale: `uk`
- reviewed overlay: `apps/teplotec_erp/teplotec_erp/crm_locale/uk.po`
- upstream template: `apps/crm/crm/locale/main.pot`
- compiled runtime catalog: `sites/assets/locale/uk/LC_MESSAGES/crm.mo`

## Image build

The immutable ERP image build:

1. clones the pinned Frappe CRM release;
2. copies the TEPLOTEC `uk.po` overlay into the CRM app;
3. runs `bench update-po-files --app crm --locale uk`, which merges the reviewed translations with the pinned upstream `main.pot`;
4. reports the number of reviewed translations against the complete upstream catalog;
5. builds the CRM frontend;
6. runs `bench compile-po-to-mo --app crm --locale uk --force`;
7. requires the resulting `crm.mo` file to exist before the image is accepted.

This keeps untranslated upstream strings visible instead of hiding them in a copied full catalog.

## Review scope v1

The first slice focuses on frequent operator-facing CRM language:

- Leads and Deals;
- Contacts and Organizations;
- Tasks, Notes and Call Logs;
- Dashboard and Settings;
- common create/edit/search/filter actions;
- common Lead and Deal fields;
- high-frequency qualification and outcome terms.

It is intentionally incomplete. Translation coverage should expand from real operator screens and workflows instead of translating the whole catalog blindly.

## Upgrading Frappe CRM

When `FRAPPE_CRM_VERSION` changes:

1. update the version in `.github/workflows/erp-image.yml`;
2. update `X-TEPLOTEC-Upstream-CRM-Version` in the overlay;
3. let the image build merge the overlay with the new `main.pot`;
4. inspect the reported coverage and newly untranslated high-frequency strings;
5. review terminology and add only the translations we want to own;
6. keep minimal source patches separate for strings that bypass gettext.

The config check deliberately fails when the overlay version marker and the pinned Frappe CRM release drift apart.
