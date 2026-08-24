import frappe
from frappe.utils import add_days, nowdate

from teplotec_erp.master_data import COMPANY_NAME


PILOT_ID = "TEPLOTEC-CRM-PILOT-001"
PILOT_EMAIL = "pilot.oksana.bondar@teplotec.invalid"
PILOT_ITEM_CODE = "PILOT-SVC-GEO-HP-INSTALL"
PILOT_PROJECT_NAME = "CRM Pilot - Бондар - Геотермальний тепловий насос"
PILOT_RATE = 310000


def create_pilot_scenario():
    """Create or resume the canonical CRM-origin TEPLOTEC sales pilot."""
    item, crm_product = _get_or_create_item_and_product()
    lead = _get_or_create_crm_lead()
    deal = _get_or_create_crm_deal(lead, crm_product)
    quotation = _get_or_create_quotation(deal, item)
    sales_order = _get_or_create_sales_order(quotation)
    customer = frappe.get_doc("Customer", sales_order.customer)
    _apply_teplotec_customer_classification(customer)
    project = _get_or_create_project(customer, sales_order)

    frappe.db.commit()
    return _scenario_result(item, crm_product, lead, deal, quotation, customer, sales_order, project)


def verify_pilot_scenario():
    """Verify the CRM Deal -> ERPNext execution contract without ERPNext Lead/Opportunity."""
    if not frappe.db.exists("Item", PILOT_ITEM_CODE):
        raise AssertionError("Pilot ERPNext Item is missing")
    item = frappe.get_doc("Item", PILOT_ITEM_CODE)

    crm_product_name = frappe.db.get_value("CRM Product", {"erpnext_item_code": item.name}, "name")
    if not crm_product_name:
        raise AssertionError("Pilot Item is not linked to a CRM Product")
    crm_product = frappe.get_doc("CRM Product", crm_product_name)

    lead_name = frappe.db.get_value("CRM Lead", {"email": PILOT_EMAIL}, "name")
    if not lead_name:
        raise AssertionError("Pilot CRM Lead is missing")
    lead = frappe.get_doc("CRM Lead", lead_name)

    deal_name = frappe.db.get_value("CRM Deal", {"lead": lead.name}, "name", order_by="creation desc")
    if not deal_name:
        raise AssertionError("Pilot CRM Deal is missing")
    deal = frappe.get_doc("CRM Deal", deal_name)

    if not any(row.product_code == crm_product.name for row in deal.products):
        raise AssertionError("Pilot CRM Deal is not linked to the ERPNext-backed CRM Product")

    quotation_name = frappe.db.get_value("Quotation", {"crm_deal": deal.name}, "name", order_by="creation desc")
    if not quotation_name:
        raise AssertionError("Pilot Quotation is missing")
    quotation = frappe.get_doc("Quotation", quotation_name)

    customer_name = frappe.db.get_value("Customer", {"crm_deal": deal.name}, "name")
    if not customer_name:
        raise AssertionError("Pilot Customer was not created from the CRM Deal")
    customer = frappe.get_doc("Customer", customer_name)

    sales_order_item = frappe.db.get_value(
        "Sales Order Item",
        {"prevdoc_docname": quotation.name, "docstatus": 1},
        ["parent", "item_code"],
        as_dict=True,
    )
    if not sales_order_item:
        raise AssertionError("Pilot Sales Order is missing")
    sales_order = frappe.get_doc("Sales Order", sales_order_item.parent)

    project_name = frappe.db.get_value("Project", {"project_name": PILOT_PROJECT_NAME}, "name")
    if not project_name:
        raise AssertionError("Pilot Project is missing")
    project = frappe.get_doc("Project", project_name)

    erpnext_lead = frappe.db.get_value("Lead", {"email_id": PILOT_EMAIL}, "name")
    if erpnext_lead:
        raise AssertionError(f"CRM-origin pilot unexpectedly created ERPNext Lead {erpnext_lead}")

    expected = {
        "item_group": (item.item_group, "Installation Services"),
        "item_crm_product": (item.crm_product_code, crm_product.name),
        "crm_product_item": (crm_product.erpnext_item_code, item.name),
        "deal_status": (deal.status, "Qualification"),
        "deal_currency": (deal.currency, "UAH"),
        "quotation_to": (quotation.quotation_to, "CRM Deal"),
        "quotation_party": (quotation.party_name, deal.name),
        "quotation_crm_deal": (quotation.crm_deal, deal.name),
        "quotation_status": (quotation.docstatus, 1),
        "customer_crm_deal": (customer.crm_deal, deal.name),
        "customer_group": (customer.customer_group, "Residential Customers"),
        "customer_type": (customer.customer_type, "Individual"),
        "sales_order_customer": (sales_order.customer, customer.name),
        "sales_order_status": (sales_order.docstatus, 1),
        "sales_order_item": (sales_order_item.item_code, item.name),
        "project_type": (project.project_type, "Customer Installation"),
        "project_customer": (project.customer, customer.name),
        "project_sales_order": (project.sales_order, sales_order.name),
    }
    mismatches = {
        field: {"actual": actual, "expected": wanted}
        for field, (actual, wanted) in expected.items()
        if actual != wanted
    }
    if mismatches:
        raise AssertionError(f"CRM-origin pilot mismatch: {mismatches}")

    return _scenario_result(item, crm_product, lead, deal, quotation, customer, sales_order, project)


def _get_or_create_item_and_product():
    if frappe.db.exists("Item", PILOT_ITEM_CODE):
        item = frappe.get_doc("Item", PILOT_ITEM_CODE)
    else:
        item = frappe.get_doc(
            {
                "doctype": "Item",
                "item_code": PILOT_ITEM_CODE,
                "item_name": "Pilot geothermal heat pump installation",
                "item_group": "Installation Services",
                "stock_uom": "Nos",
                "is_stock_item": 0,
                "is_sales_item": 1,
                "is_purchase_item": 0,
                "standard_rate": PILOT_RATE,
                "description": "Disposable CRM-origin pilot service item for the TEPLOTEC sales-to-execution flow.",
            }
        ).insert(ignore_permissions=True)

    crm_product_name = frappe.db.get_value("CRM Product", {"erpnext_item_code": item.name}, "name")
    if not crm_product_name:
        raise AssertionError("Same-site Frappe CRM integration did not create a CRM Product for the pilot Item")

    return frappe.get_doc("Item", item.name), frappe.get_doc("CRM Product", crm_product_name)


def _get_or_create_crm_lead():
    existing = frappe.db.get_value("CRM Lead", {"email": PILOT_EMAIL}, "name")
    if existing:
        return frappe.get_doc("CRM Lead", existing)

    return frappe.get_doc(
        {
            "doctype": "CRM Lead",
            "first_name": "Оксана",
            "last_name": "Бондар",
            "email": PILOT_EMAIL,
            "mobile_no": "+380670009001",
            "status": "Qualified",
            "source": "Reference",
            "lead_owner": "Administrator",
        }
    ).insert(ignore_permissions=True)


def _get_or_create_crm_deal(lead, crm_product):
    existing = frappe.db.get_value("CRM Deal", {"lead": lead.name}, "name", order_by="creation desc")
    if existing:
        deal = frappe.get_doc("CRM Deal", existing)
    else:
        from crm.fcrm.doctype.crm_lead.crm_lead import convert_to_deal

        deal_name = convert_to_deal(
            lead.name,
            deal={
                "status": "Qualification",
                "currency": "UAH",
                "exchange_rate": 1,
                "expected_deal_value": PILOT_RATE,
                "expected_closure_date": add_days(nowdate(), 35),
                "next_step": "Уточнити тепловтрати будинку та площу ділянки",
            },
        )
        deal = frappe.get_doc("CRM Deal", deal_name)

    if not any(row.product_code == crm_product.name for row in deal.products):
        deal.append(
            "products",
            {
                "product_code": crm_product.name,
                "product_name": crm_product.product_name,
                "qty": 1,
                "rate": PILOT_RATE,
                "discount_percentage": 0,
            },
        )
        deal.save(ignore_permissions=True)

    return deal


def _get_or_create_quotation(deal, item):
    existing = frappe.db.get_value("Quotation", {"crm_deal": deal.name}, "name", order_by="creation desc")
    if existing:
        quotation = frappe.get_doc("Quotation", existing)
        if quotation.docstatus == 0:
            quotation.submit()
        return quotation

    quotation = frappe.get_doc(
        {
            "doctype": "Quotation",
            "quotation_to": "CRM Deal",
            "party_name": deal.name,
            "crm_deal": deal.name,
            "company": COMPANY_NAME,
            "transaction_date": nowdate(),
            "valid_till": add_days(nowdate(), 30),
            "currency": "UAH",
            "conversion_rate": 1,
            "price_list_currency": "UAH",
            "plc_conversion_rate": 1,
            "ignore_pricing_rule": 1,
            "items": [
                {
                    "item_code": item.name,
                    "qty": 1,
                    "uom": "Nos",
                    "price_list_rate": PILOT_RATE,
                    "rate": PILOT_RATE,
                }
            ],
        }
    )
    quotation.flags.ignore_permissions = True
    quotation.insert(ignore_permissions=True)
    quotation.submit()
    return quotation


def _get_or_create_sales_order(quotation):
    existing = frappe.db.get_value(
        "Sales Order Item",
        {"prevdoc_docname": quotation.name, "docstatus": 1},
        "parent",
    )
    if existing:
        return frappe.get_doc("Sales Order", existing)

    from erpnext.selling.doctype.quotation.quotation import _make_sales_order

    sales_order = _make_sales_order(quotation.name, ignore_permissions=True)
    delivery_date = add_days(nowdate(), 45)
    sales_order.delivery_date = delivery_date
    for row in sales_order.items:
        row.delivery_date = delivery_date
    sales_order.flags.ignore_permissions = True
    sales_order.insert(ignore_permissions=True)
    sales_order.submit()

    if not sales_order.customer:
        raise AssertionError("Frappe CRM Sales Order hook did not create or attach a Customer")

    return sales_order


def _apply_teplotec_customer_classification(customer):
    changed = False
    expected = {
        "customer_group": "Residential Customers",
        "territory": "Ukraine",
        "default_currency": "UAH",
    }
    for field, value in expected.items():
        if customer.get(field) != value:
            customer.set(field, value)
            changed = True

    if changed:
        customer.flags.ignore_permissions = True
        customer.save(ignore_permissions=True)


def _get_or_create_project(customer, sales_order):
    existing = frappe.db.get_value("Project", {"project_name": PILOT_PROJECT_NAME}, "name")
    if existing:
        return frappe.get_doc("Project", existing)

    return frappe.get_doc(
        {
            "doctype": "Project",
            "project_name": PILOT_PROJECT_NAME,
            "project_type": "Customer Installation",
            "company": COMPANY_NAME,
            "customer": customer.name,
            "sales_order": sales_order.name,
            "status": "Open",
            "expected_start_date": nowdate(),
            "expected_end_date": add_days(nowdate(), 60),
            "notes": f"{PILOT_ID}: disposable CRM-origin TEPLOTEC integration pilot.",
        }
    ).insert(ignore_permissions=True)


def _scenario_result(item, crm_product, lead, deal, quotation, customer, sales_order, project):
    return {
        "status": "ok",
        "pilot_id": PILOT_ID,
        "item": item.name,
        "crm_product": crm_product.name,
        "crm_lead": lead.name,
        "crm_deal": deal.name,
        "quotation": quotation.name,
        "customer": customer.name,
        "sales_order": sales_order.name,
        "project": project.name,
    }
