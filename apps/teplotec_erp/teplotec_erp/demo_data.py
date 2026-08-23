import json
from pathlib import Path

import frappe
from frappe.utils import add_days, nowdate


CRM_APP = "crm"
DEMO_DATASET = "TEPLOTEC CRM Demo v1"
DEMO_EMAIL_SUFFIX = "@teplotec.invalid"
DATA_FILE = Path(__file__).with_name("data") / "crm_demo_v1.json"


def seed_crm_demo_v1():
    """Create or update the curated CRM demo dataset without touching real records."""
    _require_crm()
    data = _load_dataset()

    created_leads = 0
    updated_leads = 0
    created_deals = 0
    updated_deals = 0

    for row in data["leads"]:
        lead, created = _upsert_lead(row)
        if created:
            created_leads += 1
        else:
            updated_leads += 1

        deal_spec = row.get("deal")
        if deal_spec:
            _, deal_created = _upsert_deal(lead, deal_spec)
            if deal_created:
                created_deals += 1
            else:
                updated_deals += 1

    frappe.db.commit()

    result = verify_crm_demo_v1()
    result.update(
        {
            "created_leads": created_leads,
            "updated_leads": updated_leads,
            "created_deals": created_deals,
            "updated_deals": updated_deals,
        }
    )
    return result


def verify_crm_demo_v1():
    """Verify that all version-controlled demo Leads and Deals exist."""
    _require_crm()
    data = _load_dataset()

    missing_leads = []
    missing_deals = []
    status_mismatches = []

    for row in data["leads"]:
        lead_name = frappe.db.get_value("CRM Lead", {"email": row["email"]}, "name")
        if not lead_name:
            missing_leads.append(row["id"])
            continue

        deal_spec = row.get("deal")
        if not deal_spec:
            continue

        deal_name = frappe.db.get_value("CRM Deal", {"lead": lead_name}, "name", order_by="creation desc")
        if not deal_name:
            missing_deals.append(row["id"])
            continue

        actual_status = frappe.db.get_value("CRM Deal", deal_name, "status")
        if actual_status != deal_spec["status"]:
            status_mismatches.append(
                {
                    "id": row["id"],
                    "actual": actual_status,
                    "expected": deal_spec["status"],
                }
            )

    if missing_leads or missing_deals or status_mismatches:
        raise AssertionError(
            "CRM demo verification failed: "
            f"missing_leads={missing_leads}, "
            f"missing_deals={missing_deals}, "
            f"status_mismatches={status_mismatches}"
        )

    return {
        "status": "ok",
        "dataset": data["dataset"],
        "version": data["version"],
        "leads": len(data["leads"]),
        "deals": sum(1 for row in data["leads"] if row.get("deal")),
    }


def _require_crm():
    if CRM_APP not in frappe.get_installed_apps():
        raise RuntimeError("Frappe CRM must be installed before seeding demo data")


def _load_dataset():
    with DATA_FILE.open(encoding="utf-8") as handle:
        data = json.load(handle)

    if data.get("dataset") != DEMO_DATASET or data.get("version") != 1:
        raise ValueError(f"Unexpected CRM demo dataset metadata in {DATA_FILE}")

    return data


def _upsert_lead(row):
    existing = frappe.db.get_value("CRM Lead", {"email": row["email"]}, "name")
    created = not bool(existing)
    lead = frappe.get_doc("CRM Lead", existing) if existing else frappe.new_doc("CRM Lead")

    fields = {
        "first_name": row["first_name"],
        "last_name": row.get("last_name"),
        "email": row["email"],
        "mobile_no": row.get("mobile_no"),
        "organization": row.get("organization"),
        "website": row.get("website"),
        "no_of_employees": row.get("no_of_employees"),
        "annual_revenue": row.get("annual_revenue"),
        "source": row.get("source"),
        "lead_owner": "Administrator",
    }

    for field, value in fields.items():
        lead.set(field, value)

    if not lead.get("converted"):
        lead.status = row.get("status") or "New"
        lead.lost_reason = row.get("lost_reason")
        lead.lost_notes = row.get("lost_notes")

    lead.flags.ignore_permissions = True
    if created:
        lead.insert(ignore_permissions=True)
    else:
        lead.save(ignore_permissions=True)

    return lead, created


def _upsert_deal(lead, spec):
    existing = frappe.db.get_value("CRM Deal", {"lead": lead.name}, "name", order_by="creation desc")
    created = not bool(existing)

    if existing:
        deal = frappe.get_doc("CRM Deal", existing)
    else:
        from crm.fcrm.doctype.crm_lead.crm_lead import convert_to_deal

        deal_payload = _deal_fields(spec)
        deal_name = convert_to_deal(lead.name, deal=deal_payload)
        deal = frappe.get_doc("CRM Deal", deal_name)

    for field, value in _deal_fields(spec).items():
        deal.set(field, value)

    deal.flags.ignore_permissions = True
    deal.save(ignore_permissions=True)
    return deal, created


def _deal_fields(spec):
    expected_closure_days = int(spec.get("expected_closure_days", 30))
    fields = {
        "status": spec["status"],
        "currency": "UAH",
        "exchange_rate": 1,
        "expected_deal_value": spec.get("expected_deal_value"),
        "deal_value": spec.get("deal_value"),
        "expected_closure_date": add_days(nowdate(), expected_closure_days),
        "next_step": spec.get("next_step"),
        "lost_reason": spec.get("lost_reason"),
        "lost_notes": spec.get("lost_notes"),
    }
    return {field: value for field, value in fields.items() if value is not None}
