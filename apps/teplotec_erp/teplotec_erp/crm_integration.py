import frappe

from teplotec_erp.master_data import COMPANY_NAME


CRM_APP = "crm"
CRM_SETTINGS_DOCTYPE = "ERPNext CRM Settings"
ERPNEXT_CRM_SETTINGS_DOCTYPE = "CRM Settings"
SALES_SOURCE_OF_TRUTH = "Frappe CRM"

EXPECTED_CRM_SETTINGS = {
    "enabled": 1,
    "erpnext_company": COMPANY_NAME,
    "is_erpnext_in_different_site": 0,
    "sync_products": 0,
    "create_customer_on_status_change": 0,
}

EXPECTED_ERPNEXT_CRM_SETTINGS = {
    "enable_frappe_crm_data_synchronization": 1,
}

REQUIRED_CRM_DOCTYPES = (
    "CRM Lead",
    "CRM Deal",
    "CRM Organization",
    "CRM Product",
    CRM_SETTINGS_DOCTYPE,
    ERPNEXT_CRM_SETTINGS_DOCTYPE,
)

REQUIRED_INTEGRATION_FIELDS = (
    ("CRM Deal", "erpnext_customer"),
    ("CRM Product", "erpnext_item_code"),
    ("Item", "crm_product_code"),
    ("Quotation", "crm_deal"),
    ("Customer", "crm_deal"),
)


def apply_frappe_crm_integration_if_ready():
    """Configure same-site Frappe CRM integration after CRM and TEPLOTEC are ready."""
    if CRM_APP not in frappe.get_installed_apps():
        return {"status": "skipped", "reason": "crm-not-installed"}

    if not frappe.db.exists("DocType", CRM_SETTINGS_DOCTYPE):
        return {"status": "skipped", "reason": "crm-settings-not-ready"}

    if not frappe.db.exists("DocType", ERPNEXT_CRM_SETTINGS_DOCTYPE):
        return {"status": "skipped", "reason": "erpnext-crm-settings-not-ready"}

    if not frappe.db.exists("Company", COMPANY_NAME):
        return {"status": "skipped", "reason": "company-not-ready"}

    return apply_frappe_crm_integration()


def apply_frappe_crm_integration():
    """Keep Frappe CRM authoritative for sales while ERPNext executes downstream work."""
    settings = frappe.get_single(CRM_SETTINGS_DOCTYPE)
    settings_changed = False

    for field, value in EXPECTED_CRM_SETTINGS.items():
        if settings.get(field) != value:
            settings.set(field, value)
            settings_changed = True

    if settings_changed:
        settings.save(ignore_permissions=True)

    erpnext_settings = frappe.get_single(ERPNEXT_CRM_SETTINGS_DOCTYPE)
    erpnext_settings_changed = False

    for field, value in EXPECTED_ERPNEXT_CRM_SETTINGS.items():
        if erpnext_settings.get(field) != value:
            erpnext_settings.set(field, value)
            erpnext_settings_changed = True

    if erpnext_settings_changed:
        erpnext_settings.save(ignore_permissions=True)

    frappe.clear_cache()

    return {
        "status": "ok",
        "sales_source_of_truth": SALES_SOURCE_OF_TRUTH,
        "company": settings.erpnext_company,
        "same_site": not bool(settings.is_erpnext_in_different_site),
        "bidirectional_product_sync": bool(settings.sync_products),
        "automatic_customer_creation": bool(settings.create_customer_on_status_change),
        "erpnext_data_synchronization": bool(erpnext_settings.enable_frappe_crm_data_synchronization),
    }


def verify_frappe_crm_integration():
    """Fail when the Frappe CRM and ERPNext same-site integration contract drifts."""
    installed_apps = frappe.get_installed_apps()
    if CRM_APP not in installed_apps:
        raise AssertionError("Frappe CRM app is not installed")

    missing_doctypes = [name for name in REQUIRED_CRM_DOCTYPES if not frappe.db.exists("DocType", name)]
    if missing_doctypes:
        raise AssertionError(f"Required Frappe CRM integration DocTypes are missing: {missing_doctypes}")

    settings = frappe.get_single(CRM_SETTINGS_DOCTYPE)
    mismatches = {
        field: {"actual": settings.get(field), "expected": expected}
        for field, expected in EXPECTED_CRM_SETTINGS.items()
        if settings.get(field) != expected
    }
    if mismatches:
        raise AssertionError(f"Frappe CRM integration settings mismatch: {mismatches}")

    erpnext_settings = frappe.get_single(ERPNEXT_CRM_SETTINGS_DOCTYPE)
    erpnext_mismatches = {
        field: {"actual": erpnext_settings.get(field), "expected": expected}
        for field, expected in EXPECTED_ERPNEXT_CRM_SETTINGS.items()
        if erpnext_settings.get(field) != expected
    }
    if erpnext_mismatches:
        raise AssertionError(f"ERPNext Frappe CRM synchronization settings mismatch: {erpnext_mismatches}")

    missing_fields = [
        f"{doctype}.{fieldname}"
        for doctype, fieldname in REQUIRED_INTEGRATION_FIELDS
        if not frappe.get_meta(doctype).has_field(fieldname)
    ]
    if missing_fields:
        raise AssertionError(f"Frappe CRM integration fields are missing: {missing_fields}")

    if not frappe.db.exists("CRM Form Script", "Create Quotation from CRM Deal"):
        raise AssertionError("Frappe CRM Quotation integration form script is missing")

    return {
        "status": "ok",
        "sales_source_of_truth": SALES_SOURCE_OF_TRUTH,
        "crm_app": CRM_APP,
        "company": settings.erpnext_company,
        "same_site": True,
        "erpnext_item_is_product_master": not bool(settings.sync_products),
        "erpnext_data_synchronization": bool(erpnext_settings.enable_frappe_crm_data_synchronization),
    }
