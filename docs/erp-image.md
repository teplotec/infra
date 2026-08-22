# TeploTEC ERP image

TeploTEC-specific ERPNext behavior is shipped as the `teplotec_erp` Frappe app inside an immutable container image.

## Image

Repository:

```text
ghcr.io/teplotec/erpnext
```

Immutable production tags use the Git commit SHA:

```text
ghcr.io/teplotec/erpnext:sha-<40-char-git-sha>
```

The `main` tag is published for convenience, but production deployment records and uses the immutable SHA tag.

## Build

`.github/workflows/erp-image.yml` builds against `frappe_docker` v3.2.1 using the official layered-image pattern. The build installs:

- Frappe Framework v16 line
- ERPNext v16.31.1
- local `teplotec_erp` app from this repository

The local app is exposed to Bench as a build-local Git repository and installed through `bench init --apps_path`. This keeps the application source in the same repository while still using Frappe's normal app installation path.

Pull requests build the image without publishing it. Merges to `main` publish both the immutable SHA tag and the moving `main` tag to GHCR.

## Production deployment

`ERP Image Deploy` is a manual workflow on `main` and requires the exact confirmation:

```text
DEPLOY ERP
```

It runs on the CX33 self-hosted runner, authenticates to GHCR with the workflow's short-lived `GITHUB_TOKEN`, and calls the restricted root-owned admin command. No persistent GHCR token is stored on the server.

The deploy operation:

1. updates `CUSTOM_IMAGE`, `CUSTOM_TAG`, and `PULL_POLICY` in the server-side ERP environment file;
2. regenerates the Compose configuration from the pinned `frappe_docker` checkout;
3. pulls and starts the immutable custom image;
4. verifies `teplotec_erp` is present in the image;
5. installs `teplotec_erp` on the ERP site if needed;
6. runs migrations and clears cache.

The MariaDB data volume and ERP site volume are preserved. Deploying a custom image does not reset the database.

## Reset interaction

After `teplotec_erp` is deployed and installed, the separate `ERP Reset` workflow can rebuild the site/database from the version-controlled setup profile. The reset workflow also ensures `teplotec_erp` is installed before finishing.
