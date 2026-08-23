import frappe

from teplotec_erp.master_data import (
    COMPANY_ABBR,
    COMPANY_NAME,
    CUSTOMER_GROUPS,
    ITEM_GROUPS,
    MAIN_WAREHOUSE,
    PROJECT_SITES_WAREHOUSE,
    REQUIRED_UOMS,
    SUPPLIER_GROUPS,
    TRANSIT_WAREHOUSE,
    WAREHOUSE_ROOT,
)


EXPECTED_UKRAINIAN_LANGUAGE = {
    "language_code": "uk",
    "language_name": "Українська",
    "enabled": 1,
    "date_format": "dd.mm.yyyy",
    "time_format": "HH:mm",
    "number_format": "# ###,##",
    "first_day_of_the_week": "Monday",
}

EXPECTED_SYSTEM_SETTINGS = {
    "language": "uk",
    "country": "Ukraine",
    "time_zone": "Europe/Kyiv",
    "currency": "UAH",
    "setup_complete": 1,
}


def verify_localization():
    """Fail loudly when the TeploTEC Ukrainian language bootstrap is incomplete."""
    if not frappe.db.exists("Language", "uk"):
        raise AssertionError("Ukrainian language record 'uk' is missing")

    language = frappe.get_doc("Language", "uk")
    mismatches = {}

    for field, expected in EXPECTED_UKRAINIAN_LANGUAGE.items():
        actual = language.get(field)
        if actual != expected:
            mismatches[field] = {"expected": expected, "actual": actual}

    if mismatches:
        raise AssertionError(f"Ukrainian localization mismatch: {mismatches}")

    return {
        "status": "ok",
        "language": language.language_name,
        "language_code": language.language_code,
    }


def verify_master_data_v1():
    """Verify the managed TeploTEC master-data baseline and stock defaults."""
    _verify_tree_nodes("Item Group", "parent_item_group", ITEM_GROUPS)
    _verify_tree_nodes("Customer Group", "parent_customer_group", CUSTOMER_GROUPS)
    _verify_tree_nodes("Supplier Group", "parent_supplier_group", SUPPLIER_GROUPS)

    missing_uoms = [name for name in REQUIRED_UOMS if not frappe.db.exists("UOM", name)]
    if missing_uoms:
        raise AssertionError(f"Required UOMs are missing: {missing_uoms}")

    for warehouse in (WAREHOUSE_ROOT, MAIN_WAREHOUSE, TRANSIT_WAREHOUSE, PROJECT_SITES_WAREHOUSE):
        if not frappe.db.exists("Warehouse", warehouse):
            raise AssertionError(f"Required warehouse is missing: {warehouse}")

    project_sites = frappe.get_doc("Warehouse", PROJECT_SITES_WAREHOUSE)
    warehouse_mismatch = {
        "parent_warehouse": (project_sites.parent_warehouse, WAREHOUSE_ROOT),
        "company": (project_sites.company, COMPANY_NAME),
        "is_group": (int(project_sites.is_group or 0), 1),
    }
    warehouse_mismatch = {
        field: {"actual": actual, "expected": expected}
        for field, (actual, expected) in warehouse_mismatch.items()
        if actual != expected
    }
    if warehouse_mismatch:
        raise AssertionError(f"Project Sites warehouse mismatch: {warehouse_mismatch}")

    settings = frappe.get_single("Stock Settings")
    expected_stock_settings = {
        "item_naming_by": "Item Code",
        "stock_uom": "Nos",
        "default_warehouse": MAIN_WAREHOUSE,
    }
    stock_mismatch = {
        field: {"actual": settings.get(field), "expected": expected}
        for field, expected in expected_stock_settings.items()
        if settings.get(field) != expected
    }
    if stock_mismatch:
        raise AssertionError(f"TeploTEC stock defaults mismatch: {stock_mismatch}")

    return {
        "status": "ok",
        "item_groups": len(ITEM_GROUPS),
        "customer_groups": len(CUSTOMER_GROUPS),
        "supplier_groups": len(SUPPLIER_GROUPS),
        "uoms": len(REQUIRED_UOMS),
        "default_warehouse": MAIN_WAREHOUSE,
        "project_sites_warehouse": PROJECT_SITES_WAREHOUSE,
    }


def _verify_tree_nodes(doctype, parent_field, expected_nodes):
    for name, parent, is_group in expected_nodes:
        if not frappe.db.exists(doctype, name):
            raise AssertionError(f"Managed {doctype} is missing: {name}")

        doc = frappe.get_doc(doctype, name)
        actual_parent = doc.get(parent_field)
        actual_is_group = int(doc.get("is_group") or 0)
        if actual_parent != parent or actual_is_group != is_group:
            raise AssertionError(
                f"Managed {doctype} {name!r} mismatch: "
                f"parent={actual_parent!r}, is_group={actual_is_group}; "
                f"expected parent={parent!r}, is_group={is_group}"
            )


def verify_ukrainian_first_setup():
    """Verify the version-controlled TeploTEC setup profile was applied successfully."""
    verify_localization()

    settings = frappe.get_single("System Settings")
    mismatches = {}

    for field, expected in EXPECTED_SYSTEM_SETTINGS.items():
        actual = settings.get(field)
        if actual != expected:
            mismatches[field] = {"expected": expected, "actual": actual}

    if mismatches:
        raise AssertionError(f"TeploTEC system settings mismatch: {mismatches}")

    company = frappe.db.get_value(
        "Company",
        {"abbr": COMPANY_ABBR},
        ["name", "abbr"],
        as_dict=True,
    )
    if not company or company.name != COMPANY_NAME or company.abbr != COMPANY_ABBR:
        raise AssertionError(f"TeploTEC company bootstrap mismatch: {company}")

    master_data = verify_master_data_v1()

    return {
        "status": "ok",
        "language": settings.language,
        "country": settings.country,
        "time_zone": settings.time_zone,
        "currency": settings.currency,
        "company": company.name,
        "master_data": master_data,
    }
