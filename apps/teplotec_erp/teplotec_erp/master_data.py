import frappe


COMPANY_NAME = "TEPLOTEC"
COMPANY_ABBR = "TTEC"

ITEM_GROUPS = (
    ("TeploTEC", "All Item Groups", 1),
    ("TeploTEC Equipment", "TeploTEC", 1),
    ("Heat Pumps", "TeploTEC Equipment", 0),
    ("Controls & Automation", "TeploTEC Equipment", 0),
    ("Geothermal Systems", "TeploTEC", 1),
    ("Ground Loops", "Geothermal Systems", 0),
    ("Pipes & Fittings", "Geothermal Systems", 0),
    ("Manifolds", "Geothermal Systems", 0),
    ("Heat Transfer Fluids", "Geothermal Systems", 0),
    ("HVAC & Hydronics", "TeploTEC", 1),
    ("TeploTEC Consumables", "TeploTEC", 0),
    ("TeploTEC Tools", "TeploTEC", 0),
    ("TeploTEC Services", "TeploTEC", 1),
    ("Design Services", "TeploTEC Services", 0),
    ("Drilling Services", "TeploTEC Services", 0),
    ("Installation Services", "TeploTEC Services", 0),
    ("Commissioning Services", "TeploTEC Services", 0),
    ("Maintenance Services", "TeploTEC Services", 0),
)

CUSTOMER_GROUPS = (
    ("TeploTEC Customers", "All Customer Groups", 1),
    ("Residential Customers", "TeploTEC Customers", 0),
    ("Commercial Customers", "TeploTEC Customers", 0),
    ("Public Sector Customers", "TeploTEC Customers", 0),
)

SUPPLIER_GROUPS = (
    ("TeploTEC Suppliers", "All Supplier Groups", 1),
    ("Equipment Suppliers", "TeploTEC Suppliers", 0),
    ("Material Suppliers", "TeploTEC Suppliers", 0),
    ("Service Contractors", "TeploTEC Suppliers", 0),
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
        if actual_parent != parent or actual_is_group != is_group:
            raise RuntimeError(
                f"Managed {doctype} {name!r} drifted: "
                f"parent={actual_parent!r}, is_group={actual_is_group}; "
                f"expected parent={parent!r}, is_group={is_group}"
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
            warehouse.parent_warehouse != parent_warehouse
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
