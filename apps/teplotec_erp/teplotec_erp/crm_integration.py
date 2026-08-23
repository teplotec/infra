import frappe

from teplotec_erp.master_data import COMPANY_NAME


CRM_APP = "crm"
CRM_SETTINGS_DOCTYPE = "ERPNext CRM Settings"
SALES_SOURCE_OF_TRUTH = "Frappe CRM"

EXPECTED_CRM_SETTINGS = {
    "enabled": 1,
    "erpnext_company": COMPANY_NAME,
    "is_erpnext_in_different_site": 0,
    "sync_products": 0,
    "create_customer_on_status_change": 0,
}


def apply_frappe_crm_integration_if_ready():
    """Configure same-site Frappe CRM integration after CRM and TEPLOTEC are ready."""
    if CRM_APP not in frappe.get_installed_apps():
        return {"status": "skipped", "reason": "crm-not-installed"}

    if not frappe.db.exists("DocType", CRM_SETTINGS_DOCTYPE):
        return {"status": "skipped", "reason": "crm-settings-not-ready"}

    if not frappe.db.exists("Company", COMPANY_NAME):
        return {"status": "skipped", "reason": "company-not-ready"}

    return apply_frappe_crm_integration()


def apply_frappe_crm_integration():
    """Keep Frappe CRM authoritative for sales while ERPNext executes downstream work."""
    settings = frappe.get_single(CRM_SETTINGS_DOCTYPE)
    changed = False

    for field, value in EXPECTED_CRM_SETTINGS.items():
        if settings.get(field) != value:
            settings.set(field, value)
            changed = True

    if changed:
        settings.save(ignore_permissions=True)

    frappe.clear_cache()

    return {
        "status": "ok",
        "sales_source_of_truth": SALES_SOURCE_OF_TRUTH,
        "company": settings.erpnext_company,
        "same_site": not bool(settings.is_erpnext_in_different_site),
        "bidirectional_product_sync": bool(settings.sync_products),
        "automatic_customer_creation": bool(settings.create_customer_on_status_change),
    }
