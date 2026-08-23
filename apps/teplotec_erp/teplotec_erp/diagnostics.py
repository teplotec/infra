import frappe

from teplotec_erp.crm_sales import (
    EXPECTED_SELLING_SETTINGS,
    OPPORTUNITY_LOST_REASONS,
    OPPORTUNITY_TYPES,
    PROJECT_TYPES,
    SALES_STAGES,
)
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
    get_warehouse_root,
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

    warehouse_root = get_warehouse_root()
    _verify_warehouse(MAIN_WAREHOUSE, warehouse_root, is_group=0)
    _verify_warehouse(TRANSIT_WAREHOUSE, warehouse_root, is_group=0, warehouse_type="Transit")
    _verify_warehouse(PROJECT_SITES_WAREHOUSE, warehouse_root, is_group=1)

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
        "transit_warehouse": TRANSIT_WAREHOUSE,
        "project_sites_warehouse": PROJECT_SITES_WAREHOUSE,
    }


def verify_crm_sales_v1():
    """Verify TeploTEC CRM/Sales classification records and selling defaults."""
    _verify_named_records("Sales Stage", SALES_STAGES)
    _verify_named_records("Opportunity Lost Reason", OPPORTUNITY_LOST_REASONS)

    for name, description in OPPORTUNITY_TYPES.items():
        if not frappe.db.exists("Opportunity Type", name):
            raise AssertionError(f"Managed Opportunity Type is missing: {name}")
        actual = frappe.db.get_value("Opportunity Type", name, "description") or ""
        if actual != description:
            raise AssertionError(
                f"Managed Opportunity Type {name!r} description mismatch: "
                f"actual={actual!r}, expected={description!r}"
            )

    for name, description in PROJECT_TYPES.items():
        if not frappe.db.exists("Project Type", name):
            raise AssertionError(f"Managed Project Type is missing: {name}")
        actual = frappe.db.get_value("Project Type", name, "description") or ""
        if actual != description:
            raise AssertionError(
                f"Managed Project Type {name!r} description mismatch: "
                f"actual={actual!r}, expected={description!r}"
            )

    settings = frappe.get_single("Selling Settings")
    setting_mismatches = {
        field: {"actual": settings.get(field), "expected": expected}
        for field, expected in EXPECTED_SELLING_SETTINGS.items()
        if settings.get(field) != expected
    }
    if setting_mismatches:
        raise AssertionError(f"TeploTEC selling defaults mismatch: {setting_mismatches}")

    return {
        "status": "ok",
        "sales_stages": len(SALES_STAGES),
        "opportunity_types": len(OPPORTUNITY_TYPES),
        "lost_reasons": len(OPPORTUNITY_LOST_REASONS),
        "project_types": len(PROJECT_TYPES),
        "territory": settings.territory,
    }


def _verify_named_records(doctype, names):
    missing = [name for name in names if not frappe.db.exists(doctype, name)]
    if missing:
        raise AssertionError(f"Managed {doctype} records are missing: {missing}")


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


def _verify_warehouse(name, parent, is_group, warehouse_type=None):
    if not frappe.db.exists("Warehouse", name):
        raise AssertionError(f"Managed Warehouse is missing: {name}")

    warehouse = frappe.get_doc("Warehouse", name)
    expected = {
        "parent_warehouse": parent,
        "company": COMPANY_NAME,
        "is_group": is_group,
    }
    if warehouse_type is not None:
        expected["warehouse_type"] = warehouse_type

    mismatch = {
        field: {"actual": warehouse.get(field), "expected": value}
        for field, value in expected.items()
        if warehouse.get(field) != value
    }
    if mismatch:
        raise AssertionError(f"Managed Warehouse {name!r} mismatch: {mismatch}")


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
    crm_sales = verify_crm_sales_v1()

    return {
        "status": "ok",
        "language": settings.language,
        "country": settings.country,
        "time_zone": settings.time_zone,
        "currency": settings.currency,
        "company": company.name,
        "master_data": master_data,
        "crm_sales": crm_sales,
    }
