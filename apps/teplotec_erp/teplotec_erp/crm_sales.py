import frappe

from teplotec_erp.master_data import COMPANY_ABBR, COMPANY_NAME


SALES_STAGES = (
    "New Inquiry",
    "Qualified",
    "Site Survey",
    "Solution Design",
    "Quotation",
    "Negotiation",
)

OPPORTUNITY_TYPES = {
    "Heat Pump Installation": "New geothermal or air-source heat pump installation",
    "Modernization": "Upgrade or replacement of an existing heating or cooling system",
    "Service & Maintenance": "Diagnostics, repair, maintenance, or commissioning",
    "Engineering & Design": "Design, audit, calculations, or consulting before implementation",
}

OPPORTUNITY_LOST_REASONS = (
    "Price",
    "Timing",
    "Competitor",
    "Technical Fit",
    "Financing",
    "No Response",
    "Project Cancelled",
)

PROJECT_TYPES = {
    "Customer Installation": "Customer-facing installation from design through commissioning",
    "Customer Service": "Customer service, maintenance, diagnostics, or repair engagement",
    "Engineering": "Engineering, design, audit, or calculation engagement",
}

EXPECTED_SELLING_SETTINGS = {
    "cust_master_name": "Customer Name",
    "territory": "Ukraine",
    "so_required": "No",
    "dn_required": "No",
    "sales_update_frequency": "Each Transaction",
    "allow_multiple_items": 1,
}


def apply_crm_sales_v1_if_ready():
    if not frappe.db.exists("Company", {"name": COMPANY_NAME, "abbr": COMPANY_ABBR}):
        return {"status": "skipped", "reason": "company-not-ready"}

    return apply_crm_sales_v1()


def apply_crm_sales_v1():
    _ensure_named_records("Sales Stage", "stage_name", SALES_STAGES)
    _ensure_named_records(
        "Opportunity Lost Reason",
        "lost_reason",
        OPPORTUNITY_LOST_REASONS,
    )
    _ensure_opportunity_types()
    _ensure_project_types()
    _ensure_selling_settings()
    frappe.clear_cache()

    return {
        "status": "ok",
        "sales_stages": len(SALES_STAGES),
        "opportunity_types": len(OPPORTUNITY_TYPES),
        "lost_reasons": len(OPPORTUNITY_LOST_REASONS),
        "project_types": len(PROJECT_TYPES),
    }


def _ensure_named_records(doctype, fieldname, names):
    for name in names:
        if frappe.db.exists(doctype, name):
            continue

        frappe.get_doc(
            {
                "doctype": doctype,
                fieldname: name,
            }
        ).insert(ignore_permissions=True)


def _ensure_opportunity_types():
    for name, description in OPPORTUNITY_TYPES.items():
        if frappe.db.exists("Opportunity Type", name):
            existing_description = frappe.db.get_value("Opportunity Type", name, "description") or ""
            if existing_description != description:
                raise RuntimeError(
                    f"Managed Opportunity Type {name!r} drifted: "
                    f"description={existing_description!r}; expected {description!r}"
                )
            continue

        frappe.get_doc(
            {
                "doctype": "Opportunity Type",
                "name": name,
                "description": description,
            }
        ).insert(ignore_permissions=True)


def _ensure_project_types():
    for name, description in PROJECT_TYPES.items():
        if frappe.db.exists("Project Type", name):
            existing = frappe.get_doc("Project Type", name)
            if (existing.description or "") != description:
                raise RuntimeError(
                    f"Managed Project Type {name!r} drifted: "
                    f"description={(existing.description or '')!r}; expected {description!r}"
                )
            continue

        frappe.get_doc(
            {
                "doctype": "Project Type",
                "project_type": name,
                "description": description,
            }
        ).insert(ignore_permissions=True)


def _ensure_selling_settings():
    if not frappe.db.exists("Territory", "Ukraine"):
        raise RuntimeError("Required ERPNext Territory 'Ukraine' is missing")

    settings = frappe.get_single("Selling Settings")
    changed = False

    for field, value in EXPECTED_SELLING_SETTINGS.items():
        if settings.get(field) != value:
            settings.set(field, value)
            changed = True

    if changed:
        settings.save(ignore_permissions=True)
