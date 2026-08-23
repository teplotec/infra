# TeploTEC ERP Pilot Scenario

The first pilot is disposable transactional data used to exercise the standard ERPNext sales spine before TeploTEC introduces custom business entities.

It is deliberately **not** executed from `after_migrate`. Deploying application code must not silently create Leads, Customers, Quotations, Sales Orders, or Projects.

## Scenario

The pilot represents a residential customer asking TeploTEC to install a heat pump.

```text
Lead: Іван Петренко
  -> Opportunity: Heat Pump Installation
     -> Sales Stage: Site Survey
  -> Quotation
  -> Customer: Residential Customers
  -> Sales Order
  -> Project: Customer Installation
```

The pilot also creates one disposable service Item:

```text
PILOT-SVC-HP-INSTALL
```

with a test rate of `250000 UAH`.

## Standard ERPNext behavior under test

The implementation intentionally uses ERPNext's standard mapping functions rather than constructing every downstream document independently:

- Lead -> Opportunity uses the ERPNext Lead mapper;
- Opportunity -> Quotation uses the ERPNext Opportunity mapper;
- Lead -> Customer uses the ERPNext Lead mapper;
- Quotation -> Sales Order uses the ERPNext Quotation mapper;
- Project uses the standard ERPNext Project DocType and links to the resulting Customer and Sales Order.

The Quotation and Sales Order are submitted. The Project remains an open operational record.

## CI

Pull-request image CI runs the pilot twice on the fresh Ukrainian-first ERPNext site and then verifies it. Running it twice proves the pilot helper is resumable/idempotent for the same dedicated pilot customer.

## Production-like site

After the pilot code is merged and its immutable image is deployed, synchronize the restricted host helper with the Ansible host playbook. The playbook copies the repository-owned `scripts/erp-admin` to `/usr/local/sbin/teplotec-erp-admin` without changing the runner registration when it is already present.

Then run the manual GitHub Actions workflow:

```text
Actions -> ERP Pilot -> Run workflow
confirmation: CREATE PILOT
```

The workflow runs on the restricted CX33 self-hosted runner and calls only:

```text
sudo /usr/local/sbin/teplotec-erp-admin pilot
```

The helper creates or resumes the pilot through `bench execute` and immediately runs `verify_pilot_scenario`.

For break-glass operator use, the equivalent direct commands remain:

```bash
ssh teplotec-erp 'cd /opt/teplotec/erpnext/gitops && docker compose --project-name teplotec-erp --env-file erpnext.env -f docker-compose.yml exec -T backend bench --site erp.teplotec.com execute teplotec_erp.pilot.create_pilot_scenario'
```

```bash
ssh teplotec-erp 'cd /opt/teplotec/erpnext/gitops && docker compose --project-name teplotec-erp --env-file erpnext.env -f docker-compose.yml exec -T backend bench --site erp.teplotec.com execute teplotec_erp.pilot.verify_pilot_scenario'
```

These are explicit operator actions. The pilot must not become part of normal migrations or disaster-recovery restore behavior.

## What we learn next

After creating the pilot, review each document in the Desk and record what TeploTEC-specific information has no natural home in standard ERPNext. The expected candidates are:

- physical customer object/site separate from Customer;
- site address plus geo coordinates;
- building parameters and heat-loss inputs;
- requested heat-pump / system parameters;
- site survey results;
- borehole / drilling scope;
- design package and engineering artifacts;
- installation and commissioning stages;
- service lifecycle after project completion.

Only fields/entities proven necessary by this pilot should become TeploTEC customizations.
