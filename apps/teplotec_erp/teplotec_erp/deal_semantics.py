import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.custom.doctype.property_setter.property_setter import make_property_setter


CRM_APP = "crm"
DEAL_DOCTYPE = "CRM Deal"
DISPLAY_TITLE_FIELD = "teplotec_display_title"
DISPLAY_TITLE_LABEL = "Назва угоди"

DISPLAY_TITLE_CUSTOM_FIELD = {
    "fieldname": DISPLAY_TITLE_FIELD,
    "fieldtype": "Data",
    "label": DISPLAY_TITLE_LABEL,
    "hidden": 1,
    "read_only": 1,
    "no_copy": 1,
    "insert_after": "naming_series",
}


def apply_deal_semantics_v1_if_ready():
    """Apply TEPLOTEC deal display semantics when Frappe CRM is available."""
    if CRM_APP not in frappe.get_installed_apps():
        return {"status": "skipped", "reason": "crm-not-installed"}

    if not frappe.db.exists("DocType", DEAL_DOCTYPE):
        return {"status": "skipped", "reason": "crm-deal-not-ready"}

    return apply_deal_semantics_v1()


def apply_deal_semantics_v1():
    create_custom_fields({DEAL_DOCTYPE: [DISPLAY_TITLE_CUSTOM_FIELD]}, ignore_validate=True)
    _ensure_display_title_property_setter()
    backfilled = backfill_deal_display_titles()
    frappe.clear_cache(doctype=DEAL_DOCTYPE)
    result = verify_deal_semantics_v1()
    result["backfilled"] = backfilled
    return result


def set_deal_display_title(doc, method=None):
    if doc.doctype != DEAL_DOCTYPE:
        return

    doc.set(DISPLAY_TITLE_FIELD, get_deal_display_title(doc))


def get_deal_display_title(doc):
    organization = (doc.get("organization") or doc.get("organization_name") or "").strip()
    if organization:
        return organization

    person_name = " ".join(
        part.strip()
        for part in (doc.get("first_name") or "", doc.get("last_name") or "")
        if part and part.strip()
    )
    if person_name:
        return person_name

    lead_name = (doc.get("lead_name") or "").strip()
    if lead_name:
        return lead_name

    email = (doc.get("email") or "").strip()
    if email:
        return email

    return doc.get("name") or "Угода"


def backfill_deal_display_titles():
    updated = 0
    for name in frappe.get_all(DEAL_DOCTYPE, pluck="name"):
        deal = frappe.get_doc(DEAL_DOCTYPE, name)
        expected = get_deal_display_title(deal)
        if deal.get(DISPLAY_TITLE_FIELD) == expected:
            continue

        frappe.db.set_value(DEAL_DOCTYPE, name, DISPLAY_TITLE_FIELD, expected, update_modified=False)
        updated += 1

    return updated


def verify_deal_semantics_v1():
    meta = frappe.get_meta(DEAL_DOCTYPE)
    field = meta.get_field(DISPLAY_TITLE_FIELD)
    if not field:
        raise AssertionError(f"Managed CRM Deal display title field is missing: {DISPLAY_TITLE_FIELD}")

    if field.fieldtype != "Data" or field.label != DISPLAY_TITLE_LABEL:
        raise AssertionError(
            "Managed CRM Deal display title field drifted: "
            f"fieldtype={field.fieldtype!r}, label={field.label!r}"
        )

    if meta.title_field != DISPLAY_TITLE_FIELD:
        raise AssertionError(
            f"CRM Deal title_field mismatch: actual={meta.title_field!r}, expected={DISPLAY_TITLE_FIELD!r}"
        )

    blank_titles = frappe.get_all(
        DEAL_DOCTYPE,
        filters={DISPLAY_TITLE_FIELD: ["in", ["", None]]},
        pluck="name",
        limit=20,
    )
    if blank_titles:
        raise AssertionError(f"CRM Deals with blank managed display titles: {blank_titles}")

    return {
        "status": "ok",
        "doctype": DEAL_DOCTYPE,
        "title_field": DISPLAY_TITLE_FIELD,
    }


def _ensure_display_title_property_setter():
    property_setter_name = f"{DEAL_DOCTYPE}-main-title_field"
    existing = frappe.db.get_value(
        "Property Setter",
        property_setter_name,
        ["name", "value", "property_type", "doctype_or_field"],
        as_dict=True,
    )

    if (
        existing
        and existing.value == DISPLAY_TITLE_FIELD
        and existing.property_type == "Data"
        and existing.doctype_or_field == "DocType"
    ):
        return

    if existing:
        frappe.delete_doc("Property Setter", existing.name, ignore_permissions=True, force=True)

    make_property_setter(
        DEAL_DOCTYPE,
        None,
        "title_field",
        DISPLAY_TITLE_FIELD,
        "Data",
        for_doctype=True,
        validate_fields_for_doctype=False,
    )
