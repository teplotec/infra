# TeploTEC ERP

Custom Frappe app for TeploTEC-specific ERP behavior.

Initial scope:

- Ukrainian language enablement and translation overrides
- TeploTEC terminology
- Ukrainian accounting/localization extensions
- custom fields and fixtures
- print formats
- setup defaults and migrations

This source is currently co-located with infrastructure while the app and deployment model are being established. Production installation requires a custom Frappe Docker image containing this app; simply storing the source in this repository does not install it into the running ERPNext containers.
