import frappe
from frappe.model.rename_doc import rename_doc


COMPANY_NAME = "TEPLOTEC"
COMPANY_ABBR = "TEC"

LEGACY_BRAND_RENAMES = {
    "Item Group": (
        ("TeploTEC", "TEPLOTEC"),
        ("TeploTEC Equipment", "TEPLOTEC Equipment"),
        ("TeploTEC Consumables", "TEPLOTEC Consumables"),
        ("TeploTEC Tools", "TEPLOTEC Tools"),
        ("TeploTEC Services", "TEPLOTEC Services"),
    ),
    "Customer Group": (("TeploTEC Customers", "TEPLOTEC Customers"),),
    "Supplier Group": (("TeploTEC Suppliers", "TEPLOTEC Suppliers"),),
}

ITEM_GROUPS = (
    ("TEPLOTEC", "All Item Groups", 1),
    ("TEPLOTEC Equipment", "TEPLOTEC", 1),
    ("Heat Pumps", "TEPLOTEC Equipment", 0),
    ("Controls & Automation", "TEPLOTEC Equipment", 0),
    ("Geothermal Systems", "TEPLOTEC", 1),
    ("Ground Loops", "Geothermal Systems", 0),
    ("Pipes & Fittings", "Geothermal Systems", 0),
    ("Manifolds", "Geothermal Systems", 0),
    ("Heat Transfer Fluids", "Geothermal Systems", 0),
    ("HVAC & Hydronics", "TEPLOTEC", 1),
    ("TEPLOTEC Consumables", "TEPLOTEC", 0),
    ("TEPLOTEC Tools", "TEPLOTEC", 0),
    ("TEPLOTEC Services", "TEPLOTEC", 1),
    ("Design Services", "TEPLOTEC Services", 0),
    ("Drilling Services", "TEPLOTEC Services", 0),
    ("Installation Services", "TEPLOTEC Services", 0),
    ("Commissioning Services", "TEPLOTEC Services", 0),
    ("Maintenance Services", "TEPLOTEC Services", 0),
)

CUSTOMER_GROUPS = (
    ("TEPLOTEC Customers", "All Customer Groups", 1),
    ("Residential Customers", "TEPLOTEC Customers", 0),
    ("Commercial Customers", "TEPLOTEC Customers", 0),
    ("Public Sector Customers", "TEPLOTEC Customers", 0),
)

SUPPLIER_GROUPS = (
    ("TEPLOTEC Suppliers", "All Supplier Groups", 1),
    ("Equipment Suppliers", "TEPLOTEC Suppliers", 0),
    ("Material Suppliers", "TEPLOTEC Suppliers", 0),
    ("Service Contractors", "TEPLOTEC Suppliers", 0),
)

REQUIRED_UOMS = {
    "Nos": 1,
    "Meter": 0,
    "Kilogram": 0,
    "Litre": 0,
    "Hour": 0,
}

MAIN_WAREHOUSE = f"Main Warehouse - {COMPANY_ABBR}"
TRANSIT_WAREHOUSE = f"In Transit - {COMPANY_ABBR}"
PROJECT_SITES_WAREHOUSE = f"Project Sites - {COMPANY_ABBR}"


def apply_master_data_v1_if_ready():
    if not frappe.db.exists("Company", {"name": COMPANY_NAME, "abbr": COMPANY_ABBR}):
        return {"status": "skipped", "reason": "company-not-ready"}

    return apply_master_data_v1()


def apply_master_data_v1():
    _require_company()
    _rename_legacy_brand_nodes()
    _ensure_uoms()
    _ensure_item_groups()
    _ensure_customer_groups()
    _ensure_supplier_groups()
    _ensure_warehouses()
    _ensure_stock_defaults()
    frappe.clear_cache()

    return {
        "status": "ok",
        "company": COMPANY_NAME,
        "item_groups": len(ITEM_GROUPS),
        "customer_groups": len(CUSTOMER_GROUPS),
        "supplier_groups": len(SUPPLIER_GROUPS),
        "uoms": len(REQUIRED_UOMS),
        "default_warehouse": MAIN_WAREHOUSE,
        "transit_warehouse": TRANSIT_WAREHOUSE,
        "project_sites_warehouse": PROJECT_SITES_WAREHOUSE,
    }


def get_warehouse_root():
    warehouses = frappe.get_all(
        "Warehouse",
        filters={"company": COMPANY_NAME, "is_group": 1},
        fields=["name", "parent_warehouse"],
        order_by="creation asc",
    )
    for warehouse in warehouses:
        if not warehouse.parent_warehouse:
            return warehouse.name

    raise RuntimeError(f"Root Warehouse for {COMPANY_NAME!r} is missing")


def _require_company():
    company = frappe.db.get_value("Company", COMPANY_NAME, ["name", "abbr"], as_dict=True)
    if not company or company.abbr != COMPANY_ABBR:
        raise RuntimeError(
            f"Master Data v1 requires company {COMPANY_NAME!r} with abbreviation {COMPANY_ABBR!r}"
        )


def _rename_legacy_brand_nodes():
    for doctype, renames in LEGACY_BRAND_RENAMES.items():
        for old_name, new_name in renames:
            actual_old = frappe.db.get_value(doctype, {"name": old_name}, "name")
            if actual_old != old_name:
                continue

            actual_new = frappe.db.get_value(doctype, {"name": new_name}, "name")
            if actual_new == new_name:
                raise RuntimeError(
                    f"Cannot normalize {doctype} {old_name!r}: target {new_name!r} already exists"
                )

            rename_doc(
                doctype,
                old_name,
                new_name,
                force=True,
                ignore_permissions=True,
                show_alert=False,
            )


def _ensure_uoms():
    for uom_name, must_be_whole_number in REQUIRED_UOMS.items():
        if frappe.db.exists("UOM", uom_name):
            continue

        frappe.get_doc(
            {
                "doctype": "UOM",
                "uom_name": uom_name,
                "must_be_whole_number": must_be_whole_number,
                "enabled": 1,
            }
        ).insert(ignore_permissions=True)


def _ensure_item_groups():
    for name, parent, is_group in ITEM_GROUPS:
        _ensure_tree_node(
            doctype="Item Group",
            name=name,
            name_field="item_group_name",
            parent_field="parent_item_group",
            parent=parent,
            is_group=is_group,
        )


def _ensure_customer_groups():
    for name, parent, is_group in CUSTOMER_GROUPS:
        _ensure_tree_node(
            doctype="Customer Group",
            name=name,
            name_field="customer_group_name",
            parent_field="parent_customer_group",
            parent=parent,
            is_group=is_group,
        )


def _ensure_supplier_groups():
    for name, parent, is_group in SUPPLIER_GROUPS:
        _ensure_tree_node(
            doctype="Supplier Group",
            name=name,
            name_field="supplier_group_name",
            parent_field="parent_supplier_group",
            parent=parent,
            is_group=is_group,
        )


def _ensure_tree_node(doctype, name, name_field, parent_field, parent, is_group):
    if not frappe.db.exists(doctype, parent):
        raise RuntimeError(f"Required parent {doctype} {parent!r} is missing")

    if frappe.db.exists(doctype, name):
        existing = frappe.get_doc(doctype, name)
        actual_parent = existing.get(parent_field)
        actual_is_group = int(existing.get("is_group") or 0)
        if existing.name != name or actual_parent != parent or actual_is_group != is_group:
            raise RuntimeError(
                f"Managed {doctype} {name!r} drifted: "
                f"name={existing.name!r}, parent={actual_parent!r}, is_group={actual_is_group}; "
                f"expected name={name!r}, parent={parent!r}, is_group={is_group}"
            )
        return

    frappe.get_doc(
        {
            "doctype": doctype,
            name_field: name,
            parent_field: parent,
            "is_group": is_group,
        }
    ).insert(ignore_permissions=True)


def _ensure_warehouses():
    warehouse_root = get_warehouse_root()
    _ensure_warehouse("Main Warehouse", warehouse_root, is_group=0)
    _ensure_warehouse("In Transit", warehouse_root, is_group=0, warehouse_type="Transit")
    _ensure_warehouse("Project Sites", warehouse_root, is_group=1)


def _ensure_warehouse(warehouse_name, parent_warehouse, is_group, warehouse_type=None):
    expected_name = f"{warehouse_name} - {COMPANY_ABBR}"

    if frappe.db.exists("Warehouse", expected_name):
        warehouse = frappe.get_doc("Warehouse", expected_name)
        mismatch = (
            warehouse.name != expected_name
            or warehouse.parent_warehouse != parent_warehouse
            or warehouse.company != COMPANY_NAME
            or int(warehouse.is_group or 0) != is_group
            or (warehouse_type is not None and warehouse.warehouse_type != warehouse_type)
        )
        if mismatch:
            raise RuntimeError(f"Managed Warehouse {expected_name!r} drifted")
        return

    frappe.get_doc(
        {
            "doctype": "Warehouse",
            "warehouse_name": warehouse_name,
            "company": COMPANY_NAME,
            "parent_warehouse": parent_warehouse,
            "is_group": is_group,
            "warehouse_type": warehouse_type,
        }
    ).insert(ignore_permissions=True)


def _ensure_stock_defaults():
    settings = frappe.get_single("Stock Settings")
    changed = False

    expected = {
        "item_naming_by": "Item Code",
        "stock_uom": "Nos",
        "default_warehouse": MAIN_WAREHOUSE,
    }

    for field, value in expected.items():
        if settings.get(field) != value:
            settings.set(field, value)
            changed = True

    if changed:
        settings.save(ignore_permissions=True)
