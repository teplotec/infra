# TEPLOTEC ERP

Custom Frappe app for TEPLOTEC-specific ERP behavior.

Sales source of truth:

- Frappe CRM owns Leads, Deals, Organizations, Contacts, and the sales pipeline.
- ERPNext owns downstream execution: Customers, Quotations, Sales Orders, Projects, Stock, Buying, and Accounting.
- ERPNext Item remains the operational product master; CRM Products are synchronized integration records.

Initial scope:

- Ukrainian language enablement and translation overrides
- TEPLOTEC terminology
- Frappe CRM and ERPNext integration defaults
- Ukrainian accounting/localization extensions
- custom fields and fixtures
- print formats
- setup defaults and migrations

This source is currently co-located with infrastructure while the app and deployment model are being established. Production installation requires a custom Frappe Docker image containing ERPNext, Frappe CRM, and this app; simply storing the source in this repository does not install it into the running containers.
